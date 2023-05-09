import argparse
import m5
from m5.objects import *

# Add the common scripts to our path
m5.util.addToPath("../")
# import the caches which we made
from common.Caches import *
from common import Options


def malformedSplitSimUrl(s):
    print("Error: SplitSim URL", s, "is malformed")
    sys.exit(1)


# Parse SplitSim "URLs" in the following format:
# ADDR[ARGS]
# ADDR = connect:UX_SOCKET_PATH |
#        listen:UX_SOCKET_PATH:SHM_PATH
# ARGS = :sync | :link_latency=XX | :sync_interval=XX
def parseSplitSimUrl(s):
    out = {"sync": False}
    parts = s.split(":")
    if len(parts) < 2:
        malformedSplitSimUrl(s)

    if parts[0] == "connect":
        out["listen"] = False
        out["uxsocket_path"] = parts[1]
        parts = parts[2:]
    elif parts[0] == "listen":
        if len(parts) < 3:
            malformedSplitSimUrl(s)
        out["listen"] = True
        out["uxsocket_path"] = parts[1]
        out["shm_path"] = parts[2]
        parts = parts[3:]
    else:
        malformedSplitSimUrl(s)

    for p in parts:
        if p == "sync":
            out["sync"] = True
        elif p.startswith("sync_interval="):
            out["sync_tx_interval"] = p.split("=")[1]
        elif p.startswith("latency="):
            out["link_latency"] = p.split("=")[1]
        else:
            malformedSplitSimUrl(s)
    return out


parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"
# system.mem_ranges = [AddrRange('1GB')]

idv_mem_start = f"{args.split_cpu}GB"
idv_mem_end = f"{args.split_cpu + 1}GB"
system.mem_ranges = [AddrRange(idv_mem_start, idv_mem_end)]


system.cpu = TimingSimpleCPU(cpu_id=args.split_cpu)

# Create L1 instruction and data cache
system.cpu.icache = L1_ICache(size="32kB")
system.cpu.dcache = L1_DCache(size="32kB")

# Connect cpu to L1 caches
system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side

# create L2 bus and connect
system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

# Create SimbricksAdapter object and Connect to L2 bus
params = parseSplitSimUrl(args.splitsim[0])
params["uxsocket_path"] = params["uxsocket_path"] + f".{args.split_cpu}"
if params["listen"] == True:
    params["shm_path"] = params["shm_path"] + f".{args.split_cpu}"

system.splitcpu_adapter = SplitCPUAdapter(**params)

system.l2bus.mem_side_ports = system.splitcpu_adapter.cpu_side


# create the interrupt controller for the CPU
system.cpu.createInterruptController()

# Create Mem controller and connect to memory bus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.splitcpu_adapter.mem_side

# For x86 only, make sure the interrupts are connected to the memory
# Note: these are directly connected to the memory bus and are not cached

# if m5.defines.buildEnv['TARGET_ISA'] == "x86":
system.cpu.interrupts[0].pio = system.splitcpu_adapter.pio_proxy
system.cpu.interrupts[0].int_requestor = system.splitcpu_adapter.int_req_proxy
system.cpu.interrupts[0].int_responder = system.splitcpu_adapter.int_resp_proxy

# Connect the system up to the membus
# system.system_port = system.membus.cpu_side_ports


system.workload = SEWorkload.init_compatible(
    "/OS/endhost-networking/work/sim/hejing/gem5/tests/test-progs/hello/bin/x86/linux/hello64-static"
)

# system.workload = SEWorkload.init_compatible(
#     'tests/test-progs/blackScholes/bin/bs64-static')

# system.workload = SEWorkload.init_compatible(
#     'tests/test-progs/membound/bin/mb64-static')

# phymem = 5242880 *  args.simbricks_cpu

process = Process(pid=100 + args.split_cpu)

# process.cmd = ['tests/test-progs/hello/bin/x86/linux/hello64-static']
if args.cmd == "cpu":
    process.cmd = [
        "/OS/endhost-networking/work/sim/hejing/gem5/tests/test-progs/blackScholes/bin/bs64-static",
        "100",
        "1",
        "2",
        "3",
        "4",
        "300000",
        f"{args.split_cpu}",
    ]
elif args.cmd == "mem":
    process.cmd = [
        "/OS/endhost-networking/work/sim/hejing/gem5/tests/test-progs/membound/bin/mb64-static",
        "50000",
        "1500",
    ]

system.cpu.workload = [process]

system.cpu.createThreads()


root = Root(full_system=False, system=system)
m5.instantiate()
# system.cpu.workload[0].map(0, phymem, 5000000, True)

print("Beginning Simulation!\n")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s\n" % (m5.curTick(), exit_event.getCause()))

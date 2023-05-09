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
total_mem = f"{args.num_cpus}GB"
system.mem_ranges = [AddrRange("0GB", total_mem)]

# Create SimbricksAdapter objects and Connect to L2 bus

system.membus = SystemXBar()
mem_adapter_params = []
i = 0
url = args.splitsim[0]
for i in range(args.num_cpus):
    params = parseSplitSimUrl(url)
    params["uxsocket_path"] = params["uxsocket_path"] + f".{i}"
    if params["listen"] == True:
        params["shm_path"] = params["shm_path"] + f".{i}"
    mem_adapter_params.append(params)

system.splitmem_adapter = [
    SplitMEMAdapter(**params) for params in (mem_adapter_params)
]

system.l2 = [L2Cache(size="32MB") for i in range(args.num_cpus)]

for i in range(args.num_cpus):

    # Create L2 cache and connect to SimbricksAdapter
    system.l2[i].cpu_side = system.splitmem_adapter[i].mem_side

    # connect to L2 Cache to system bus
    system.l2[i].mem_side = system.membus.cpu_side_ports

    ########## Need to add pio, interrupt port on adapter object

    # For x86 only, make sure the interrupts are connected to the memory
    # Note: these are directly connected to the memory bus and are not cached
    # if m5.defines.buildEnv['TARGET_ISA'] == "x86":
    system.splitmem_adapter[i].pio_proxy = system.membus.mem_side_ports
    system.splitmem_adapter[i].int_req_proxy = system.membus.cpu_side_ports
    system.splitmem_adapter[i].int_resp_proxy = system.membus.mem_side_ports
    # Connect the system up to the membus


# system.system_port = system.membus.cpu_side_ports

# Create Mem controller and connect to memory bus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# system.workload = SEWorkload.init_compatible(
#    'tests/test-progs/hello/bin/x86/linux/hello')

# process = Process()
# process.cmd = ['tests/test-progs/hello/bin/x86/linux/hello']
# system.cpu.workload = process
# system.cpu.createThreads()


root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning Simulation!\n")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s\n" % (m5.curTick(), exit_event.getCause()))

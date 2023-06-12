import argparse
import m5
from m5.objects import *

# Add the common scripts to our path
m5.util.addToPath("../")
# import the caches which we made
from common.Caches import *
from common import Options

parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"
system.mem_ranges = []

# Parse Splitsim URLs and prepare parameters for adapters
up_adapter_params = []
down_adapter_params = []
url = args.splitsim[0]


for i in range(args.split_numa_num):
    up_params = Options.parseSplitSimUrl(url)
    up_params["uxsocket_path"] = up_params["uxsocket_path"] + f".up.{i}"
    if up_params["listen"] == True:
        up_params["shm_path"] = up_params["shm_path"] + f".up.{i}"
    up_adapter_params.append(up_params)

    down_params = Options.parseSplitSimUrl(url)
    down_params["uxsocket_path"] = down_params["uxsocket_path"] + f".down.{i}"
    if down_params["listen"] == True:
        down_params["shm_path"] = down_params["shm_path"] + f".down.{i}"
    down_adapter_params.append(down_params)

system.sysbus = SystemXBar()

per_numa_mem = args.num_cpus * 512
for i in range(args.split_numa_num):
    start_range = f"{i * per_numa_mem}MB"
    end_range = f"{(i + 1) * per_numa_mem}MB"
    system.mem_ranges.append(AddrRange(start_range, end_range))

system.upbr = [Bridge() for i in range(args.split_numa_num)]
system.downbr = [Bridge() for i in range(args.split_numa_num)]

system.splitcpu_adapter = [
    SplitCPUAdapter(**down_adapter_params[i])
    for i in range(args.split_numa_num)
]

system.splitmem_adapter = [
    SplitMEMAdapter(**up_adapter_params[i]) for i in range(args.split_numa_num)
]

# Connect to bridges and adapters to the system bus
for i in range(args.split_numa_num):

    system.upbr[i].cpu_side_port = system.sysbus.mem_side_ports
    system.upbr[i].mem_side_port = system.splitcpu_adapter[i].cpu_side
    system.upbr[i].ranges = system.mem_ranges[i]

    system.splitmem_adapter[i].mem_side = system.downbr[i].cpu_side_port
    system.downbr[i].mem_side_port = system.sysbus.cpu_side_ports

    per_numa_range = []
    for k in range(args.split_numa_num):
        if k != i:
            per_numa_range.append(system.mem_ranges[k])

    system.downbr[i].ranges = per_numa_range
# Create dummy Mem controller and connect to memory bus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.splitcpu_adapter[0].mem_side

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning Simulation!\n")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s\n" % (m5.curTick(), exit_event.getCause()))

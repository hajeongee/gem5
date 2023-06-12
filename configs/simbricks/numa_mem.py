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

# Calculate memory ranges for each NUMA node in the system
per_numa_mem = args.num_cpus * 512
for i in range(args.split_numa_num):
    start_range = f"{i * per_numa_mem}MB"
    end_range = f"{(i + 1) * per_numa_mem}MB"
    system.mem_ranges.append(AddrRange(start_range, end_range))

# Parse Splitsim URLs and prepare parameters for adapters
mem_adapter_params = []
br_adapter_params = []
url = args.splitsim[0]
base_cpu_idx = args.num_cpus * args.split_numa_idx

for i in range(args.num_cpus):
    params = Options.parseSplitSimUrl(url)
    params["uxsocket_path"] = params["uxsocket_path"] + f".{base_cpu_idx + i}"
    if params["listen"] == True:
        params["shm_path"] = params["shm_path"] + f".{base_cpu_idx + i}"
    mem_adapter_params.append(params)

url = args.splitsim[1]
up_params = Options.parseSplitSimUrl(url)
up_params["uxsocket_path"] = (
    up_params["uxsocket_path"] + f".up.{args.split_numa_idx}"
)
if up_params["listen"] == True:
    up_params["shm_path"] = (
        up_params["shm_path"] + f".up.{args.split_numa_idx}"
    )
mem_adapter_params.append(up_params)

down_params = Options.parseSplitSimUrl(url)
down_params["uxsocket_path"] = (
    down_params["uxsocket_path"] + f".down.{args.split_numa_idx}"
)
if down_params["listen"] == True:
    down_params["shm_path"] = (
        down_params["shm_path"] + f".down.{args.split_numa_idx}"
    )
br_adapter_params.append(down_params)

# Create system bus
system.membus = SystemXBar()

# Create SimbricksAdapter objects and Connect to L2 bus
system.splitmem_adapter = [
    SplitMEMAdapter(**params) for params in (mem_adapter_params)
]


system.splitmem_adapter[args.num_cpus].mem_side = system.membus.cpu_side_ports


for i in range(args.num_cpus):

    system.membus.cpu_side_ports = system.splitmem_adapter[i].mem_side
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
system.mem_ctrl.dram.range = system.mem_ranges[args.split_numa_idx]
system.mem_ctrl.port = system.membus.mem_side_ports

# Create Bridge Down and its adapter
# system.downbr = Bridge()
per_numa_range = []
for k in range(args.split_numa_num):
    if k != args.split_numa_idx:
        per_numa_range.append(system.mem_ranges[k])
# system.downbr.ranges = per_numa_range

system.splitcpu_adapter = SplitCPUAdapter(
    **br_adapter_params[0], addr_ranges=per_numa_range
)

# system.splitcpu_adapter.addr_ranges = per_numa_range
system.splitcpu_adapter.cpu_side = system.membus.mem_side_ports

# system.downbr.cpu_side_port = system.membus.mem_side_ports
# system.downbr.mem_side_port = system.splitcpu_adapter.cpu_side


root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning Simulation!\n")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s\n" % (m5.curTick(), exit_event.getCause()))

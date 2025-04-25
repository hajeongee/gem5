# Copyright (c) 2021-2023 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# When run with multiple MPI ranks
#  mpirun -n 3 --allow-run-as-root sst --partitioner=sst.self --add-lib-path=./ sst/x86_example.py 

import sst
import sys
import os
import copy

from sst import UnitAlgebra
from sst.merlin import *

eth_link_latency = "500ns"
memory_size_sst = "500MiB"
cpu_clock_rate = "2GHz"
host_id = 0

# We keep a track of all the memory ports that we have.
sst_ports = {
    "eth_port" : f"system.pc.sst_ethif_0"

}

# We need a list of ports.
port_list = []
for port in sst_ports:
    port_list.append(port)

def generate_cpu_params(base_params, host_id):
    params = copy.deepcopy(base_params)
    params["cmd"] = f" --outdir=/simbricks/experiments/out/sst/gem5-out.{host_id}" + params["cmd"]
    if (host_id == 0):
        params["cmd"] += f" --disk-image=/simbricks/experiments/out/sst/cfg.server_iperf.tar"
    else:
        params["cmd"] += f" --disk-image=/simbricks/experiments/out/sst/cfg.client_iperf.tar"
    return params

cpu_params = {
    "frequency": cpu_clock_rate,
    "cmd": " ../../configs/example/sst/x86_fs.py"
            + f" --cpu-clock={cpu_clock_rate}"
            + f" --cpu-type=TimingSimpleCPU"
            + f" --kernel=/simbricks/images/vmlinux"
            + f" --disk-image=/simbricks/images/output-base/base.raw"
            + " --sst-eth-e1000"
            + " --caches"
            + " --l2cache"
            + " --l1d_size=32kB"
            + " --l1i_size=32kB"
            + " --l2_size=2MB"
            + " --l1d_assoc=8"
            + " --l1i_assoc=8"
            + " --l2_assoc=4"
            + " --cacheline_size=64"
            + f" --mem-size={memory_size_sst}",
    "debug_flags": "",
    "ports" : " ".join(port_list)
}


# The first host
gem5_node_0 = sst.Component("gem5_node_0", "gem5.gem5Component")
gem5_node_0.setRank(1,0)
cpu_params_0 = generate_cpu_params(cpu_params, host_id)
gem5_node_0.addParams(cpu_params_0)

# for initialization
eth_port_0 = gem5_node_0.setSubComponent(port_list[0], "gem5.gem5EthBridge", 0)
# tell the SubComponent the name of the corresponding SimObject
eth_port_0.addParams({ "response_receiver_name": sst_ports["eth_port"]})
eth_port_0.addParam("host_id", host_id)
eth_port_0.addParam("dst_id", 1)


# The second host
host_id += 1
gem5_node_1 = sst.Component("gem5_node_1", "gem5.gem5Component")
gem5_node_1.setRank(2,0)
cpu_params_1 = generate_cpu_params(cpu_params, host_id)
gem5_node_1.addParams(cpu_params_1)

# for initialization
eth_port_1 = gem5_node_1.setSubComponent(port_list[0], "gem5.gem5EthBridge", 0)
# tell the SubComponent the name of the corresponding SimObject
eth_port_1.addParams({ "response_receiver_name": sst_ports["eth_port"]})
eth_port_1.addParam("host_id", host_id)
eth_port_1.addParam("dst_id", 0)

# Create a router
rtr = sst.Component("rtr_0", "merlin.hr_router")
rtr.setRank(0,0)
rtr.setSubComponent("topology","merlin.singlerouter",0)
rtr.addParam("id", 0)
rtr.addParam("num_ports", 2)
rtr.addParam("flit_size", "64B")
rtr.addParam("xbar_bw", "100GB/s")
rtr.addParam("link_bw", "100GB/s")
rtr.addParam("input_buf_size", "8MB")
rtr.addParam("output_buf_size", "8MB")


# Connections
# gem5 <-> router
gem5_rtr_link_0 = sst.Link("gem5_rtr_link_0")
gem5_rtr_link_0.connect(
    (eth_port_0, "port", eth_link_latency),
    (rtr, "port0", eth_link_latency)
)

gem5_rtr_link_1 = sst.Link("gem5_rtr_link_1")
gem5_rtr_link_1.connect(
    (eth_port_1, "port", eth_link_latency),
    (rtr, "port1", eth_link_latency)
)

# enable Statistics
stat_params = { "rate" : "0ns" }
sst.setStatisticLoadLevel(7)
sst.setStatisticOutput("sst.statOutputTXT", {"filepath" : "./sst-stats.txt"})
sst.enableAllStatisticsForComponentName("rtr_0", stat_params)


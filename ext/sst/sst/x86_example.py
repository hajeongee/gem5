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
import argparse

from sst import UnitAlgebra
from sst.merlin import *

eth_link_latency = "500ns"
memory_size_sst = "500MiB"
cpu_clock_rate = "2GHz"
host_id = 0
# host_pairs = 1

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Simulate host pairs.")
parser.add_argument("--host_pairs", type=int, required=True, help="Number of host pairs")
args = parser.parse_args()

host_pairs = args.host_pairs
print(f"Host pairss: {host_pairs}")

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
    if (host_id < host_pairs):
        # servers
        params["cmd"] = f" --outdir=/simbricks/experiments/out/sst/gem5-out.server.{host_id}" + params["cmd"]
        params["cmd"] += f" --disk-image=/simbricks/experiments/out/sst/cfg.server.{host_id}.tar"
    else:
        # clients
        params["cmd"] = f" --outdir=/simbricks/experiments/out/sst/gem5-out.client.{host_id - host_pairs}" + params["cmd"]
        params["cmd"] += f" --disk-image=/simbricks/experiments/out/sst/cfg.client.{host_id - host_pairs}.tar"
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


server_host_list = []
client_host_list = []

server_rtr_links = []
client_rtr_links = []

# Create a router
rtr = sst.Component("rtr_0", "merlin.hr_router")
rtr.setRank(0,0)
rtr.setSubComponent("topology","merlin.singlerouter",0)
rtr.addParam("id", 0)
rtr.addParam("num_ports", 2 * host_pairs)
rtr.addParam("flit_size", "64B")
rtr.addParam("xbar_bw", "100GB/s")
rtr.addParam("link_bw", "100GB/s")
rtr.addParam("input_buf_size", "8MB")
rtr.addParam("output_buf_size", "8MB")

# Create server hosts
for i in range(0, host_pairs):
    host_id = i

    comp_name = f"server_node_{i}"
    server_node = sst.Component(comp_name, "gem5.gem5Component")
    server_node.setRank(i + 1,0)
    server_cpu_params = generate_cpu_params(cpu_params, i)
    server_node.addParams(server_cpu_params)
    server_host_list.append(server_node)

    eth_port = server_node.setSubComponent(port_list[0], "gem5.gem5EthBridge", 0)
    # tell the SubComponent the name of the corresponding SimObject
    eth_port.addParams({ "response_receiver_name": sst_ports["eth_port"]})
    eth_port.addParam("host_id", host_id)
    eth_port.addParam("dst_id", host_id + host_pairs)

    # Create link to the router
    link_name = f"server_rtr_{i}"
    port_name = f"port{i}"
    server_rtr_link = sst.Link(link_name)
    server_rtr_link.connect(
        (eth_port, "port", eth_link_latency),
        (rtr, port_name, eth_link_latency)
    )
    server_rtr_links.append(server_rtr_link)


# Create client hosts
for i in range(0, host_pairs):
    host_id = i + host_pairs

    comp_name = f"client_node_{i}"
    client_node = sst.Component(comp_name, "gem5.gem5Component")
    client_node.setRank(i + 1 + host_pairs,0)
    client_cpu_params = generate_cpu_params(cpu_params, i + host_pairs)
    client_node.addParams(client_cpu_params)
    client_host_list.append(client_node)

    eth_port = client_node.setSubComponent(port_list[0], "gem5.gem5EthBridge", 0)
    # tell the SubComponent the name of the corresponding SimObject
    eth_port.addParams({ "response_receiver_name": sst_ports["eth_port"]})
    eth_port.addParam("host_id", host_id)
    eth_port.addParam("dst_id", host_id - host_pairs)

    # Create link to the router
    link_name = f"client_rtr_{i}"
    port_name = f"port{i + host_pairs}"
    client_rtr_link = sst.Link(link_name)
    client_rtr_link.connect(
        (eth_port, "port", eth_link_latency),
        (rtr, port_name, eth_link_latency)
    )
    client_rtr_links.append(client_rtr_link)

# enable Statistics
stat_params = { "rate" : "0ns" }
sst.setStatisticLoadLevel(7)
sst.setStatisticOutput("sst.statOutputTXT", {"filepath" : "./out/sst-stats.txt"})
sst.enableAllStatisticsForComponentName("rtr_0", stat_params)


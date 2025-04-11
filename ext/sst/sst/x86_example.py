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

import sst
import sys
import os

from sst import UnitAlgebra
from sst.merlin import *

eth_link_latency = "500ns"
memory_size_sst = "500MiB"
cpu_clock_rate = "2GHz"

# We keep a track of all the memory ports that we have.
sst_ports = {
    "eth_port" : "system.e1000_outgoing_bridge"

}

# We need a list of ports.
port_list = []
for port in sst_ports:
    port_list.append(port)

cpu_params = {
    "frequency": cpu_clock_rate,
    "cmd": " ../../configs/example/sst/x86_fs.py"
            + f" --cpu-clock={cpu_clock_rate}"
            + f" --cpu-type=TimingSimpleCPU"
            + f" --kernel=/simbricks/images/vmlinux"
            + f" --disk-image=/simbricks/images/output-base/base.raw"
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

gem5_node = sst.Component("gem5_node", "gem5.gem5Component")
gem5_node.addParams(cpu_params)


# for initialization
eth_port = gem5_node.setSubComponent(port_list[0], "gem5.gem5EthBridge", 0)
# tell the SubComponent the name of the corresponding SimObject
eth_port.addParams({ "response_receiver_name": sst_ports["eth_port"]})

# Create a router
rtr = sst.Component("rtr_0", "merlin.hr_router")
rtr.setSubComponent("topology","merlin.singlerouter",0)
rtr.addParam("id", 0)
rtr.addParam("num_ports", 1)
rtr.addParam("flit_size", "8B")
rtr.addParam("xbar_bw", "4GB/s")
rtr.addParam("link_bw", "4GB/s")
rtr.addParam("input_buf_size", "4kB")
rtr.addParam("output_buf_size", "4kB")


# Connections
# gem5 <-> router
gem5_rtr_link = sst.Link("gem5_rtr_link")
gem5_rtr_link.connect(
    (eth_port, "port", eth_link_latency),
    (rtr, "port0", eth_link_latency)
)

# enable Statistics
stat_params = { "rate" : "0ns" }
sst.setStatisticLoadLevel(7)
sst.setStatisticOutput("sst.statOutputTXT", {"filepath" : "./sst-stats.txt"})
sst.enableAllStatisticsForComponentName("rtr_0", stat_params)


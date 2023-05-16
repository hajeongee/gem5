from m5.objects import *
from components.memory_hierarchy import *
from components.sys_structure import *


class MyRemoteCore(SubSystem):
    def __init__(self, uxpath, shmpath, cpu_id):
        super().__init__()

        self.adapter = SplitMEMAdapter()
        self.adapter.listen = True
        self.adapter.uxsocket_path = uxpath
        self.adapter.shm_path = shmpath

        self._cpu_id = cpu_id

    def connect_l2(self, port):
        self.adapter.mem_side = port

    def connect_ints(self, int_req, int_resp):
        self.adapter.int_req_proxy = int_req
        self.adapter.int_resp_proxy = int_resp

    def get_cpu_id(self):
        return self._cpu_id

class MyRemoteSocket(SubSystem):
    def __init__(self, core, uxpath, shmpath):
        super().__init__()

        self.adapter = SplitCPUAdapter()
        self.adapter.listen = False
        self.adapter.uxsocket_path = uxpath
        self.adapter.shm_path = shmpath

        self.core = core
        core.connect_l2(self.adapter.cpu_side)
        core.connect_ints(
            self.adapter.int_req_proxy,
            self.adapter.int_resp_proxy)


def makeSplitDummySystem(rsock):
    system = System()
    system.clk_domain =  SrcClockDomain()
    system.clk_domain.clock = '1GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    system.mem_mode = 'timing'
    system.m5ops_base = 0xFFFF0000
    system.cache_line_size = 64

    system.remote_socket = rsock
    return system


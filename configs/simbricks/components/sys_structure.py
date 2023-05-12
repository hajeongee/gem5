from m5.objects import *
from components.memory_hierarchy import *

class MyCPUCore(SubSystem):
    def __init__(self, CPUClass, clock, cpuId, socketId):
        super().__init__()

        self.voltage_domain = VoltageDomain()
        self.clock_domain = SrcClockDomain(
            clock=clock,
            voltage_domain=self.voltage_domain)

        self.cpu = CPUClass(
            clk_domain=self.clock_domain,
            cpu_id=cpuId,
            socket_id =socketId)
        self.cpu.createThreads()
        self.cpu.createInterruptController()
    
        self.l1_xbar = L1XBar()
        self.l1_d = L1_DCache()
        self.l1_i = L1_DCache()
        self.l2_xbar = L2XBar()
        self.l2 = L2_Cache()

        # wire up caches and in-core xbars
        self.l2_xbar.default = self.l2.cpu_side
        self.l1_d.mem_side = self.l2_xbar.cpu_side_ports
        self.l1_i.mem_side = self.l2_xbar.cpu_side_ports
        self.cpu.icache_port = self.l1_i.cpu_side
        self.l1_xbar.mem_side_ports = self.l1_d.cpu_side
        self.cpu.dcache_port = self.l1_xbar.cpu_side_ports
        self.cpu.mmu.itb.walker.port = self.l1_xbar.cpu_side_ports
        self.cpu.mmu.dtb.walker.port = self.l1_xbar.cpu_side_ports

        # we wire up LAPIC pio port directly to l2 xbar memory side, as
        # these registers can only be accessed locally anyways
        self.l2_xbar.mem_side_ports = self.cpu.interrupts[0].pio


    def connect_l2(self, port):
        self.l2.mem_side = port

    def connect_ints(self, int_req, int_resp):
        self.cpu.interrupts[0].int_requestor = int_req
        self.cpu.interrupts[0].int_responder = int_resp


class MyCPUSocket(SubSystem):
    def __init__(self, cores):
        super().__init__()

        #cores = []
        #for i in range(numCores):
        #    core = MyCPUCore(CPUClass, clock, i + coreIdStart, socketId)
        #    cores.append(core)
        self.cores = cores

        # create L3 crossbar and cache
        self.l3_xbar = L3XBar()
        self._have_dma = False
        self._have_pio_xbar = False
        self.offsocket_xbar = OffSocketXBar()
        self.l3 = L3_Cache()

        # wire up ports
        self.l3.cpu_side = self.l3_xbar.mem_side_ports
        self.l3.mem_side = self.offsocket_xbar.cpu_side_ports
        for core in self.cores:
            core.connect_l2(self.l3_xbar.cpu_side_ports)

    def connect_system(self, sys):
        sys.system_port = self.offsocket_xbar.cpu_side_ports

    def connect_mem(self, mem):
        mem.port = self.offsocket_xbar.mem_side_ports

    def connect_pci(self, dev):
        self.connect_pio(dev)
        self.connect_dma(dev)

    def get_pio_bus(self):
        if not self._have_pio_xbar:
            self.io_pio_xbar = IOPioXBar()
            self.io_pio_xbar.cpu_side_ports = self.offsocket_xbar.mem_side_ports
            self._have_pio_xbar = True
        return self.io_pio_xbar

    def connect_pio(self, dev):
        self.get_pio_bus().mem_side_ports = dev.pio

    def get_dma_bus(self):
        if not self._have_dma:
            self.ioc = IOCache()
            self.io_dma_xbar = IODmaXBar()
            self.l3_xbar.cpu_side_ports = self.ioc.mem_side
            self.ioc.cpu_side = self.io_dma_xbar.mem_side_ports
            self._have_dma = True
        return self.io_dma_xbar

    def connect_dma(self, dev):
        dev.dma = self.get_dma_bus().cpu_side_ports

    def connect_ints(self, req, resp):
        for core in self.cores:
            core.connect_ints(req, resp)

    def connect_board(self, req, resp):
        self.offsocket_xbar.cpu_side_ports = req
        self.offsocket_xbar.default = resp


class MyNUMANode(SubSystem):
    def __init__(self, socket, MemClass, memOff, memSz, memNum):
        super().__init__()

        self.cpu_socket = socket
        # FIXME: avoid assigning range 3G-4G
        memctrls = []
        for i in range(memNum):
            ctrl = MemCtrl()
            ctrl.dram = MemClass()
            ctrl.dram.range = AddrRange(
                memOff + i * memSz,
                memOff + (i + 1) * memSz)
            memctrls.append(ctrl)
        self.mem_ctrls = memctrls
        for c in self.mem_ctrls:
            self.cpu_socket.connect_mem(c)

    def add_pci_device(self, name, dev):
        setattr(self, name, dev)
        self.cpu_socket.connect_pci(dev)

    def connect_system(self, system):
        self.cpu_socket.connect_system(system)

    def connect_ints(self, req, resp):
        self.cpu_socket.connect_ints(req, resp)

    def connect_board(self, req, resp):
        self.cpu_socket.connect_board(req, resp)


class MyBoard(SubSystem):
    def __init__(self, nodes):
        super().__init__()

        self.nodes = nodes
        self.mem_xbar = BoardMemXBar()
        self.int_xbar = IntXBar()
        for n in nodes:
            n.connect_ints(
                self.int_xbar.cpu_side_ports,
                self.int_xbar.mem_side_ports)
            n.connect_board(
                self.mem_xbar.mem_side_ports,
                self.mem_xbar.cpu_side_ports)
            
        self.pc_legacy = Pc()
        self.pc_legacy.attachIO(self.mem_xbar, int_bus=self.int_xbar)
        #self.pc_legacy.attachIO(
        #    self.nodes[0].cpu_socket.get_pio_bus(),
        #    [],
        #    self.nodes[0].cpu_socket.get_dma_bus(),
        #    self.int_xbar)

    def physmem_ranges(self):
        # get memory ranges from each numa node's memory controllers
        raw_ranges = []
        for n in self.nodes:
            for c in n.mem_ctrls:
                raw_ranges.append(c.dram.range)

        # sort by start of range
        rs = sorted(raw_ranges, key=lambda ar: ar.start)
    
        # compress consecutive ranges
        start = rs[0].start
        end = rs[0].end
        out_ranges = []
        for r in rs[1:]:
            # rule out overlapping ranges
            assert r.start.value >= end.value

            if r.start.value != end.value:
                out_ranges.append(AddrRange(start, end))
                start = r.start
            end = r.end
        out_ranges.append(AddrRange(start, end))

        return out_ranges

            
    def connect_system(self, system):
        self.nodes[0].connect_system(system)

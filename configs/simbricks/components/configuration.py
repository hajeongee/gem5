from m5.objects import *

class CowIdeDisk(IdeDisk):
    image = CowDiskImage(child=RawDiskImage(read_only=True), read_only=False)

    def childImage(self, ci):
        self.image.child.image_file = ci


def makeCowDisks(disk_paths):
    disks = []
    for disk_path in disk_paths:
        disk = CowIdeDisk(driveID="device0")
        disk.childImage(disk_path)
        disks.append(disk)
    return disks


# Set up the Intel MP tables
def makeMPTables(system):
    base_entries = []
    ext_entries = []
    max_apic_id = 0
    for n in system.board.nodes:
        for core in n.cpu_socket.cores:
            # FIXME: incorrect with SMT
            cpu_id = core.get_cpu_id()
            apic_id = cpu_id

            bp = X86IntelMPProcessor(
                local_apic_id=apic_id,
                local_apic_version=0x14,
                enable=True,
                bootstrap=(cpu_id == 0),
            )
            base_entries.append(bp)
            max_apic_id = max(apic_id, max_apic_id)
    io_apic = X86IntelMPIOAPIC(
        id=max_apic_id + 1, version=0x11, enable=True, address=0xFEC00000
    )
    system.board.pc_legacy.south_bridge.io_apic.apic_id = io_apic.id
    base_entries.append(io_apic)
    # In gem5 Pc::calcPciConfigAddr(), it required "assert(bus==0)",
    # but linux kernel cannot config PCI device if it was not connected to
    # PCI bus, so we fix PCI bus id to 0, and ISA bus id to 1.
    pci_bus = X86IntelMPBus(bus_id=0, bus_type="PCI   ")
    base_entries.append(pci_bus)
    isa_bus = X86IntelMPBus(bus_id=1, bus_type="ISA   ")
    base_entries.append(isa_bus)
    connect_busses = X86IntelMPBusHierarchy(
        bus_id=1, subtractive_decode=True, parent_bus=0
    )
    ext_entries.append(connect_busses)
    for dev in range(0, 4):
        pci_dev_inta = X86IntelMPIOIntAssignment(
            interrupt_type="INT",
            polarity="ConformPolarity",
            trigger="ConformTrigger",
            source_bus_id=0,
            source_bus_irq=0 + (dev << 2),
            dest_io_apic_id=io_apic.id,
            dest_io_apic_intin=16 + dev,
        )
        base_entries.append(pci_dev_inta)

    def assignISAInt(irq, apicPin):
        assign_8259_to_apic = X86IntelMPIOIntAssignment(
            interrupt_type="ExtInt",
            polarity="ConformPolarity",
            trigger="ConformTrigger",
            source_bus_id=1,
            source_bus_irq=irq,
            dest_io_apic_id=io_apic.id,
            dest_io_apic_intin=0,
        )
        base_entries.append(assign_8259_to_apic)
        assign_to_apic = X86IntelMPIOIntAssignment(
            interrupt_type="INT",
            polarity="ConformPolarity",
            trigger="ConformTrigger",
            source_bus_id=1,
            source_bus_irq=irq,
            dest_io_apic_id=io_apic.id,
            dest_io_apic_intin=apicPin,
        )
        base_entries.append(assign_to_apic)

    assignISAInt(0, 2)
    assignISAInt(1, 1)
    for i in range(3, 15):
        assignISAInt(i, i)
    system.workload.intel_mp_table.base_entries = base_entries
    system.workload.intel_mp_table.ext_entries = ext_entries


# Add in a Bios information structure.
def makeBiosTables(system):
    structures = [X86SMBiosBiosInformation()]
    system.workload.smbios_table.structures = structures

    # We assume below that there's at least 1MB of memory. We'll require 2
    # just to avoid corner cases.
    mem_ranges = system.mem_ranges
    phys_mem_size = sum([r.size() for r in mem_ranges])
    assert phys_mem_size >= 0x200000
    assert len(system.mem_ranges) <= 2

    entries = [
        # Mark the first megabyte of memory as reserved
        X86E820Entry(addr=0, size="639kB", range_type=1),
        X86E820Entry(addr=0x9FC00, size="385kB", range_type=2),
        # Mark the rest of physical memory as available
        X86E820Entry(
            addr=0x100000,
            size="%dB" % (mem_ranges[0].size() - 0x100000),
            range_type=1,
        ),
    ]

    # Mark [mem_size, 3GB) as reserved if memory less than 3GB, which force
    # IO devices to be mapped to [0xC0000000, 0xFFFF0000). Requests to this
    # specific range can pass though bridge to iobus.
    if len(mem_ranges) == 1:
        entries.append(
            X86E820Entry(
                addr=mem_ranges[0].size(),
                size="%dB" % (0xC0000000 - mem_ranges[0].size()),
                range_type=2,
            )
        )

    # Reserve the last 16kB of the 32-bit address space for the m5op interface
    entries.append(X86E820Entry(addr=0xFFFF0000, size="64kB", range_type=2))

    # In case the physical memory is greater than 3GB, we split it into two
    # parts and add a separate e820 entry for the second part.  This entry
    # starts at 0x100000000,  which is the first address after the space
    # reserved for devices.
    if len(mem_ranges) == 2:
        entries.append(
            X86E820Entry(
                addr=0x100000000,
                size="%dB" % (mem_ranges[1].size()),
                range_type=1,
            )
        )

    system.workload.e820_table.entries = entries

class ConfigParams(object):
    def __init__(self, mem_mode, disks, kernel, cmdline):
        self.mem_mode = mem_mode
        self.disks = disks
        self.kernel = kernel
        self.cmdline = cmdline
        self.workload = X86FsLinux

    def make_workload(self):
        workload = self.workload()
        workload.object_file = self.kernel
        workload.command_line = self.cmdline
        return workload



def makeSystem(board, config):
    system = System()
    system.clk_domain =  SrcClockDomain()
    system.clk_domain.clock = '1GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    system.mem_mode = config.mem_mode

    system.m5ops_base = 0xFFFF0000
    system.cache_line_size = 64


    system.board = board
    board.connect_system(system)

    system.mem_ranges = system.board.physmem_ranges()

    # prepare serial console
    board.pc_legacy.com_1.device = Terminal(port=3456, outfile="stdoutput")

    # prepare disks
    disks = makeCowDisks(config.disks)

    board.pc_legacy.south_bridge.ide.disks = disks

    system.workload = config.make_workload()
    
    makeMPTables(system)
    makeBiosTables(system)


    return system

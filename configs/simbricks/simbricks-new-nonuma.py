import m5
from m5.objects import *


from components.sys_structure import *
from components.configuration import *


cores = []
for i in range(4):
    cores.append(MyCPUCore(X86TimingSimpleCPU, '1GHz', i, int(i/2)))

sock0 = MyCPUSocket(cores[:2])
node0 = MyNUMANode(sock0, DDR3_1600_8x8, 0, 512 * 1024 * 1024, 6)
board = MyNonNumaBoard(node0)

nic0 = IGbE_e1000(
    host=board.pc_legacy.pci_host,
    pci_bus=0,
    pci_dev=0,
    pci_func=0,
    InterruptLine=16,
    InterruptPin=1)
node0.add_pci_device('pci0', nic0)

cmdline = (
    'earlyprintk=ttyS0 console=ttyS0 root=/dev/sda1 no_timer_check '
    'memory_corruption_check=0 random.trust_cpu=on '
    'init=/home/ubuntu/guestinit.sh')
system = makeSystem(
    board=board,
    mem_mode='timing',
    disks=['/local/antoinek/simbricks/images/output-base/base.raw'],
    kernel='/local/antoinek/simbricks/images/vmlinux',
    cmdline=cmdline)

root = Root(full_system = True, system = system)

m5.instantiate()
exit_event = m5.simulate()
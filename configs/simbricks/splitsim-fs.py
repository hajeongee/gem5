from __future__ import print_function

import sys
import m5
from m5.objects import *


from components.sys_structure import *
from components.configuration import *
from components.splitsim import *

path_prefix = 'splitsim'
num_cores = 2

base_cfg = ConfigParams(
    mem_mode='timing',
    disks=['/local/antoinek/simbricks/images/output-base/base.raw'],
    kernel='/local/antoinek/simbricks/images/vmlinux',
    cmdline=(
        'earlyprintk=ttyS0 console=ttyS0 root=/dev/sda1 no_timer_check '
        'memory_corruption_check=0 random.trust_cpu=on '
        'init=/home/ubuntu/guestinit.sh')
    )

def create_generic_system(cores, cfg):
    sock0 = MyCPUSocket(cores)
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

    system = makeSystem(board, cfg)
    return system

def create_generic_ith_core(i):
    return MyCPUCore(X86TimingSimpleCPU, '1GHz', i, int(i/2))



def create_monolith():
    cores = []
    for i in range(num_cores):
        cores.append(create_generic_ith_core(i))
    return create_generic_system(cores)


def create_split_main():
    cores = []
    for i in range(num_cores):
        cores.append(MyRemoteCore(f'{path_prefix}/{i}-ux',
                                  f'{path_prefix}/{i}-shm',
                                  i))
    base_cfg.workload = X86FsLinuxMem
    return create_generic_system(cores, base_cfg)

def create_split_core(i):
    rsock = MyRemoteSocket(
        create_generic_ith_core(i),
        f'{path_prefix}/{i}-ux',
        f'{path_prefix}/{i}-shm'
    )
    base_cfg.workload = X86FsLinuxCPU0 if i == 0 else X86FsLinuxCPUn
    return makeSplitDummySystem(rsock, base_cfg)

mode = sys.argv[1]
if mode == 'monolith':
    print('mono')
    system = create_monolith()
    print(system)
elif mode == 'split-main':
    system = create_split_main()
elif mode.startswith('split-core'):
    n = int(mode[10:])
    system = create_split_core(n)
else:
    sys.exit(1)

root = Root(full_system = True, system = system)
m5.instantiate()
exit_event = m5.simulate()

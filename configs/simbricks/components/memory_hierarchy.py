from m5.objects import *

#######################################
# Caches

class L1Cache(Cache):
    size = '32kB'
    assoc = 8
    tag_latency = 0
    data_latency = 0
    response_latency = 0
    mshrs = 4
    tgts_per_mshr = 20
    

class L1_ICache(L1Cache):
    is_read_only = True
    # Writeback clean lines as well
    writeback_clean = True

class L1_DCache(L1Cache):
    pass

class TLBWalkerCache(L1Cache):
    pass

class L2_Cache(Cache):
    size='2MB'
    assoc = 4
    tag_latency = 3
    data_latency = 3
    response_latency = 3
    mshrs = 20
    tgts_per_mshr = 12
    write_buffers = 8
    

class L3_Cache(Cache):
    size = '32MB'
    assoc = 16
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 32
    tgts_per_mshr = 24
    write_buffers = 16

# I/O cache used for DMA accesses
class IOCache(Cache):
    size = '32kB'
    assoc = 8
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 20
    tgts_per_mshr = 12


#######################################
# Crossbars

# Noncoherent crossbar template
class MyNcXBar(NoncoherentXBar):
    width = 64

    # introduce no additional latency. L1 should really have multiple ports
    frontend_latency = 0
    forward_latency = 0
    response_latency = 0


# Noncoherent crossbar template
class MyCXbar(CoherentXBar):
    width = 64

    # Assume that most of this is covered by the cache latencies, with
    # no more than a single pipeline stage for any packet.
    frontend_latency = 1
    forward_latency = 0
    response_latency = 1
    snoop_response_latency = 1

    # Use a snoop-filter by default, and set the latency to zero as
    # the lookup is assumed to overlap with the frontend latency of
    # the crossbar
    snoop_filter = SnoopFilter(lookup_latency=0)

# Crossbar connecting CPU data porPt and page table walker to L1D
class L1XBar(MyNcXBar):
    pass

# Crossbar connecting L1D and L1I caches to L2
class L2XBar(MyCXbar):
    point_of_unification = True


# Crossbar connecting L2 caches to L3
class L3XBar(MyCXbar):
    pass


# Crossbar connecting L3 cache to off-core ports (memory, peer sockets, devices)
# TODO: presumably needs to be coherent for NUMA
class OffSocketXBar(MyCXbar):
    #point_of_unification = True
    pass

# Main memory bus on board, connects all numa nodes together, also legacy
# devices
class BoardMemXBar(MyCXbar):
    #point_of_unification = True
    point_of_coherency = True
    pass

# Crossbar connecting DMA ports of IO-devices to IO cache
class IODmaXBar(MyNcXBar):
    pass

# Crossbar connecting PIO ports of IO-devices to off-core crossbar
class IOPioXBar(MyNcXBar):
    pass

# Crossbar connecting interrupt request and response ports together
class IntXBar(MyNcXBar):
    pass
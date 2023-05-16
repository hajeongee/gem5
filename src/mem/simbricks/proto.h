/*
 * Copyright 2021 Max Planck Institute for Software Systems, and
 * National University of Singapore
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */


#ifndef SPLITGEM5_MEM_PROTO_H_
#define SPLITGEM5_MEM_PROTO_H_

#include <assert.h>
#include <stdint.h>

#include <simbricks/base/proto.h>

/** in dev_intro.flags to indicate that sender supports issuing syncs. */
#define SPLIT_PROTO_CPU_FLAGS_DI_SYNC (1 << 0)
#define SPLIT_PROTO_CPU_FLAGS_HI_SYNC (1 << 0)

#define SPLIT_PROTO_C2M_MSG_MASK 0x7f
#define SPLIT_PROTO_M2C_MSG_MASK 0x7f
/** Mask for ownership bit in own_type field */
#define SPLIT_PROTO_C2M_OWN_MASK 0x80
/** Message is owned by device */
#define SPLIT_PROTO_C2M_OWN_CPU 0x00
/** Message is owned by host */
#define SPLIT_PROTO_C2M_OWN_MEM 0x80
/** Messgae is a sync message */
#define SPLIT_PROTO_C2M_SYNC 0x1
/** Messgae is data message message */
#define SPLIT_PROTO_C2M_RECV 0x2

#define SPLIT_PROTO_M2C_OWN_MASK 0x80
/** Message is owned by host */
#define SPLIT_PROTO_M2C_OWN_MEM 0x00
/** Message is owned by device */
#define SPLIT_PROTO_M2C_OWN_CPU 0x80
/** Messgae is a sync message */
#define SPLIT_PROTO_M2C_SYNC 0x1
/** Messgae is data message message */
#define SPLIT_PROTO_M2C_RECV 0x2

/* Initialization messages on Unix socket */

/** welcome message sent by network devices to eachother. */
struct SimbricksProtoMemIntro {
  uint32_t dummy; /* not used, but need to avoid empty struct for standard C */
} __attribute__((packed));


/** Gem5 packet of the message is functional */
/* pkt_type[0]: packet is functioal->0; timing->1
** pkt_type[1]: packet is normal packet->0; addr_range->1
----------------
Below three bits are one-hot indicating from which port
did addr_range packet come

** pkt_type[2]: PIO_PROXY
** pkt_type[3]: INT_REQ_PROXY
** pkt_type[4]: INT_RESP_PROXY
**
*/

#define PACKET_FUNCTIONAL 0x00
#define PACKET_TIMING 0x01
#define PACKET_ADDR_RANGE (1 << 1)
#define PIO_PROXY (1 << 2)
#define INT_REQ_PROXY (1 << 3)
#define INT_RESP_PROXY (1 << 4)


enum Command
{
  InvalidCmd,
  ReadReq,
  ReadResp,
  ReadRespWithInvalidate,
  WriteReq,
  WriteResp,
  WriteCompleteResp,
  WritebackDirty,
  WritebackClean,
  WriteClean,            // writes dirty data below without evicting
  CleanEvict,
  SoftPFReq,
  SoftPFExReq,
  HardPFReq,
  SoftPFResp,
  HardPFResp,
  WriteLineReq,
  UpgradeReq,
  SCUpgradeReq,           // Special "weak" upgrade for StoreCond
  UpgradeResp,
  SCUpgradeFailReq,       // Failed SCUpgradeReq in MSHR (never sent)
  UpgradeFailResp,        // Valid for SCUpgradeReq only
  ReadExReq,
  ReadExResp,
  ReadCleanReq,
  ReadSharedReq,
  LoadLockedReq,
  StoreCondReq,
  StoreCondFailReq,       // Failed StoreCondReq in MSHR (never sent)
  StoreCondResp,
  SwapReq,
  SwapResp,
  // MessageReq and MessageResp are deprecated.
  MemFenceReq = SwapResp + 3,
  MemSyncReq,  // memory synchronization request (e.g., cache invalidate)
  MemSyncResp, // memory synchronization response
  MemFenceResp,
  CleanSharedReq,
  CleanSharedResp,
  CleanInvalidReq,
  CleanInvalidResp,
  // Error responses
  // @TODO these should be classified as responses rather than
  // requests; coding them as requests initially for backwards
  // compatibility
  InvalidDestError,  // packet dest field invalid
  BadAddressError,   // memory address invalid
  FunctionalReadError, // unable to fulfill functional read
  FunctionalWriteError, // unable to fulfill functional write
  // Fake simulator-only commands
  PrintReq,       // Print state matching address
  FlushReq,      //request for a cache flush
  InvalidateReq,   // request for address to be invalidated
  InvalidateResp,
  // hardware transactional memory
  HTMReq,
  HTMReqResp,
  HTMAbort,
  //NUM_MEM_CMDS = 53 // number of enums except this one
};

enum Attribute
{
  IsRead,         //!< Data flows from responder to requester
  IsWrite,        //!< Data flows from requester to responder
  IsUpgrade,
  IsInvalidate,
  IsClean,        //!< Cleans any existing dirty blocks
  NeedsWritable,  //!< Requires writable copy to complete in-cache
  IsRequest,      //!< Issued by requester
  IsResponse,     //!< Issue by responder
  NeedsResponse,  //!< Requester needs response from target
  IsEviction,
  IsSWPrefetch,
  IsHWPrefetch,
  IsLlsc,         //!< Alpha/MIPS LL or SC access
  HasData,        //!< There is an associated payload
  IsError,        //!< Error response
  IsPrint,        //!< Print state matching address (for debugging)
  IsFlush,        //!< Flush the address from caches
  FromCache,      //!< Request originated from a caching agent
  //NUM_COMMAND_ATTRIBUTES = 18 // number of enums except this one
};

enum FlagsType
{
  // Flags to transfer across when copying a packet
  COPY_FLAGS             = 0x000000FF,

  // Flags that are used to create reponse packets
  RESPONDER_FLAGS        = 0x00000009,

  // Does this packet have sharers (which means it should not be
  // considered writable) or not. See setHasSharers below.
  HAS_SHARERS            = 0x00000001,

  // Special control flags
  /// Special timing-mode atomic snoop for multi-level coherence.
  EXPRESS_SNOOP          = 0x00000002,

  /// Allow a responding cache to inform the cache hierarchy
  /// that it had a writable copy before responding. See
  /// setResponderHadWritable below.
  RESPONDER_HAD_WRITABLE = 0x00000004,

  // Snoop co-ordination flag to indicate that a cache is
  // responding to a snoop. See setCacheResponding below.
  CACHE_RESPONDING       = 0x00000008,

  // The writeback/writeclean should be propagated further
  // downstream by the receiver
  WRITE_THROUGH          = 0x00000010,

  // Response co-ordination flag for cache maintenance
  // operations
  SATISFIED              = 0x00000020,

  // hardware transactional memory

  // Indicates that this packet/request has returned from the
  // cache hierarchy in a failed transaction. The core is
  // notified like this.
  FAILS_TRANSACTION      = 0x00000040,

  // Indicates that this packet/request originates in the CPU executing
  // in transactional mode, i.e. in a transaction.
  FROM_TRANSACTION       = 0x00000080,

  /// Are the 'addr' and 'size' fields valid?
  VALID_ADDR             = 0x00000100,
  VALID_SIZE             = 0x00000200,

  /// Is the data pointer set to a value that shouldn't be freed
  /// when the packet is destroyed?
  STATIC_DATA            = 0x00001000,
  /// The data pointer points to a value that should be freed when
  /// the packet is destroyed. The pointer is assumed to be pointing
  /// to an array, and delete [] is consequently called
  DYNAMIC_DATA           = 0x00002000,

  /// suppress the error if this packet encounters a functional
  /// access failure.
  SUPPRESS_FUNC_ERROR    = 0x00008000,

  // Signal block present to squash prefetch and cache evict packets
  // through express snoop flag
  BLOCK_CACHED          = 0x00010000
};

enum HtmCacheFailure
{
    NO_FAIL,     // no failure in cache
    FAIL_SELF,   // failed due local cache's replacement policy
    FAIL_REMOTE, // failed due remote invalidation
    FAIL_OTHER,  // failed due other circumstances
};
/** request FlagsType
 * supposed to be enum, but c enum has 32-bit size
 * so leave it as global variable
 *
 * Architecture specific flags.
 * These bits int the flag field are reserved for
 * architecture-specific code. For example, SPARC uses them to
 * represent ASIs.
 */

enum FlagsType_req {
  ARCH_BITS = 0x000000FF,
  INST_FETCH = 0x00000100,
  PHYSICAL = 0x00000200,
  UNCACHEABLE = 0x00000400,
  STRICT_ORDER = 0x00000800,
  PRIVILEGED = 0x00008000,
  CACHE_BLOCK_ZERO = 0x00010000,
  NO_ACCESS = 0x00080000,
  LOCKED_RMW = 0x00100000,
  LLSC = 0x00200000,
  MEM_SWAP = 0x00400000,
  MEM_SWAP_COND = 0x00800000,
  PREFETCH = 0x01000000,
  PF_EXCLUSIVE = 0x02000000,
  EVICT_NEXT = 0x04000000,
  ACQUIRE = 0x00020000,
  RELEASE = 0x00040000,
  ATOMIC_RETURN_OP = 0x40000000,
  ATOMIC_NO_RETURN_OP = 0x80000000,
  KERNEL = 0x00001000,
  SECURE = 0x10000000,
  PT_WALK = 0x20000000,
  INVALIDATE,                 // 64_bit, 0x0000000100000000
  CLEAN,                      // 64_bit, 0x0000000200000000
  DST_POU,                    // 64_bit, 0x0000001000000000
  DST_POC,                    // 64_bit, 0x0000002000000000
  DST_BITS,                   // 64_bit, 0x0000003000000000
  HTM_START,                  // 64_bit, 0x0000010000000000
  HTM_COMMIT,                 // 64_bit, 0x0000020000000000
  HTM_CANCEL,                 // 64_bit, 0x0000040000000000
  HTM_ABORT,                  // 64_bit, 0x0000080000000000
  STICKY_FLAGS = 0x00000100,  // = INST_FETCH

  /* Request CacheCoherenceFlagsType (new version)
  ** mem_sync_op flags */
  I_CACHE_INV = 0x00000001,
  INV_L1 = 0x00000001,
  V_CACHE_INV = 0x00000002,
  K_CACHE_INV = 0x00000004,
  GL1_CACHE_INV = 0x00000008,
  K_CACHE_WB = 0x00000010,
  FLUSH_L2 = 0x00000020,
  GL2_CACHE_INV = 0x00000040,
  SLC_BIT = 0x00000080,
  DLC_BIT = 0x00000100,
  GLC_BIT = 0x00000200,
  CACHED = 0x00000400,
  READ_WRITE = 0x00000800,
  SHARED = 0x00001000,

/*
Those are MemSpaceConfigFlagsType from old version of src/mem/request.hh 
This should be used temperally until the gem5 is upgraded
*/
  SCOPE_VALID = 0x00000001,
  /** Access has Wavefront scope visibility */
  WAVEFRONT_SCOPE = 0x00000002,
  /** Access has Workgroup scope visibility */
  WORKGROUP_SCOPE = 0x00000004,
  /** Access has Device (e.g., GPU) scope visibility */
  DEVICE_SCOPE = 0x00000008,
  /** Access has System (e.g., CPU + GPU) scope visibility */
  SYSTEM_SCOPE = 0x00000010,

  /** Global Segment */
  GLOBAL_SEGMENT = 0x00000020,
  /** Group Segment */
  GROUP_SEGMENT = 0x00000040,
  /** Private Segment */
  PRIVATE_SEGMENT = 0x00000080,
  /** Kergarg Segment */
  KERNARG_SEGMENT = 0x00000100,
  /** Readonly Segment */
  READONLY_SEGMENT = 0x00000200,
  /** Spill Segment */
  SPILL_SEGMENT = 0x00000400,
  /** Arg Segment */
  ARG_SEGMENT = 0x00000800,
};

enum PrivateFlagsType
{
    /** Whether or not the size is valid. */
    VALID_SIZE_r           = 0x00000001,
    /** Whether or not paddr is valid (has been written yet). */
    VALID_PADDR          = 0x00000002,
    /** Whether or not the vaddr is valid. */
    VALID_VADDR          = 0x00000004,
    /** Whether or not the instruction sequence number is valid. */
    VALID_INST_SEQ_NUM   = 0x00000008,
    /** Whether or not the pc is valid. */
    VALID_PC             = 0x00000010,
    /** Whether or not the context ID is valid. */
    VALID_CONTEXT_ID     = 0x00000020,
    /** Whether or not the sc result is valid. */
    VALID_EXTRA_DATA     = 0x00000080,
    /** Whether or not the stream ID and substream ID is valid. */
    VALID_STREAM_ID      = 0x00000100,
    VALID_SUBSTREAM_ID   = 0x00000200,
    // hardware transactional memory
    /** Whether or not the abort cause is valid. */
    VALID_HTM_ABORT_CAUSE = 0x00000400,
    /** Whether or not the instruction count is valid. */
    VALID_INST_COUNT      = 0x00000800,
    /**
     * These flags are *not* cleared when a Request object is reused
     * (assigned a new address).
     */
    STICKY_PRIVATE_FLAGS = VALID_CONTEXT_ID
};


struct SplitGem5Req
{
  uint64_t _paddr;
  unsigned _size;
  uint64_t _byteEnable;
  uint16_t _requestorId;
  //uint8_t pad[2];
  uint64_t _flags;
  uint64_t _cacheCoherenceFlags;
  uint16_t privateFlags;
  uint64_t _time; //Tick _time = MaxTick;
  uint32_t _taskId;
  uint32_t _streamId;
  uint64_t _vaddr;
  uint64_t _extraData;
  int _contextId;
  uint64_t _pc;
  uint64_t _reqInstSeqNum;
  int64_t _instCount;
  uint64_t _reqCount;
}__attribute__((packed));

struct SplitGem5Packet
{
  uint8_t pad[48];
  uint64_t timestamp; //simbricks
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
  enum FlagsType flags;
  enum Command cmd;
  uint64_t packet_id;
  //uint8_t pad_[7];
  bool _isSecure;
  uint8_t _qosValue;
  struct SplitGem5Req req;
  uint64_t addr;
  unsigned size;
  uint64_t bytesValid;
  enum HtmCacheFailure htmReturnReason;
  uint64_t htmTransactionUid;
  uint32_t headerDelay;
  uint32_t snoopDelay;
  uint32_t payloadDelay;
  uint8_t data[];
} __attribute__((packed));
//SPLIT_GEM5_MSG_SZCHECK(struct SplitGem5Packet);

struct SplitGem5C2MSync
{
  uint8_t pad[48];
  uint64_t timestamp;
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);

struct SplitGem5M2CSync
{
  uint8_t pad[48];
  uint64_t timestamp;
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);

struct SplitGem5AddrRange
{
  uint8_t pad[48];
  uint64_t timestamp;
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
  uint8_t size;
  uint64_t _start[150];
  uint64_t _end[150];
}__attribute__((packed));

struct SplitGem5C2Mdummy
{
  uint8_t pad[48];
  uint64_t timestamp;
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);

struct SplitGem5M2Cdummy
{
  uint8_t pad[48];
  uint64_t timestamp;
  uint8_t pad_[7];
  uint8_t own_type;
  uint8_t pkt_type;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);
union SplitProtoC2M
{
  struct SplitGem5Packet packet;
  struct SplitGem5C2MSync sync;
  struct SplitGem5AddrRange addr_range;
  struct SplitGem5C2Mdummy dummy;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);


union SplitProtoM2C
{
  struct SplitGem5Packet packet;
  struct SplitGem5M2CSync sync;
  struct SplitGem5AddrRange addr_range;
  struct SplitGem5M2Cdummy dummy;
} __attribute__((packed));
//SIMBRICKS_PROTO_PCIE_MSG_SZCHECK(union SimbricksProtoPcieD2H);


#endif //SPLITGEM5_MEM_PROTO_H_
#ifndef __SPLIT_CPU_ADAPTER_HH__
#define __SPLIT_CPU_ADAPTER_HH__

#include <unordered_map>

#include "mem/packet_queue.hh"
#include "mem/port.hh"
#include "mem/qport.hh"
#include "params/SplitCPUAdapter.hh"
#include "simbricks/base.hh"

namespace gem5 {
namespace simbricks {
extern "C" {
#include <simbricks/gem5_mem/proto.h>

}

class SplitCPUAdapter
    : public SimObject,
      public simbricks::base::GenericBaseAdapter<SplitProtoM2C,
                                                 SplitProtoC2M>::Interface {
 private:
  class CPUSidePort : public ResponsePort
  {
   private:
    SplitCPUAdapter *owner;

   public:
    CPUSidePort(const std::string &name, SplitCPUAdapter *owner)
        : ResponsePort(name, owner), owner(owner) {
    }
    AddrRangeList getAddrRanges() const override;

   protected:
    Tick recvAtomic(PacketPtr pkt) override {
      panic("recvAtomic unimpl\n");
    }

    void recvFunctional(PacketPtr pkt) override;
    bool recvTimingReq(PacketPtr pkt) override;
    void recvRespRetry() override;
  };

  class IntReqProxyPort : public ResponsePort
  {
   private:
    SplitCPUAdapter *owner;

   public:
    IntReqProxyPort(const std::string &name, SplitCPUAdapter *owner)
        : ResponsePort(name, owner), owner(owner) {
    }
    AddrRangeList getAddrRanges() const override;
    AddrRangeList ranges_;

   protected:
    Tick recvAtomic(PacketPtr pkt) override {
      panic("recvAtomic unimpl\n");
    }

    void recvFunctional(PacketPtr pkt) override {
      panic("recvFunctional unimpl\n");
    }

    bool recvTimingReq(PacketPtr pkt) override {
      panic("recvTimingReq unimpl\n");
    }

    void recvRespRetry() override {
      panic("recvRespRetry unimpl\n");
    }
  };

  class IntRespProxyPort : public RequestPort
  {
   private:
    SplitCPUAdapter *owner;

   public:
    IntRespProxyPort(const std::string &name, SplitCPUAdapter *owner)
        : RequestPort(name, owner), owner(owner) {
    }

   protected:
    bool recvTimingResp(PacketPtr pkt) override {
      panic("recvTimingResp no impl\n");
    }
    void recvReqRetry() override {
      panic("recvREqRetry no impl\n");
    }
    void recvRangeChange() override;
  };

  class PioProxyPort : public RequestPort
  {
   private:
    SplitCPUAdapter *owner;

   public:
    PioProxyPort(const std::string &name, SplitCPUAdapter *owner)
        : RequestPort(name, owner), owner(owner) {
    }

   protected:
    bool recvTimingResp(PacketPtr pkt) override {
      panic("recvTimingResp no impl\n");
    }
    void recvReqRetry() override {
      panic("recvREqRetry no impl\n");
    }
    void recvRangeChange() override;
  };

  // dummy memside port for dummy memory control
  class MemSidePort : public RequestPort
  {
   private:
    SplitCPUAdapter *owner;

   public:
    MemSidePort(const std::string &name, SplitCPUAdapter *owner)
        : RequestPort(name, owner), owner(owner) {
    }

    // void sendPacket(PacketPtr pkt);

   protected:
    bool recvTimingResp(PacketPtr pkt) override {
      panic("recvTimingResp no impl\n");
    }
    void recvReqRetry() override {
      panic("recvREqRetry no impl\n");
    }
    void recvRangeChange() override;
  };

 protected:
  // SimBricks base adapter
  simbricks::base::GenericBaseAdapter<SplitProtoM2C, SplitProtoC2M> adapter;
  bool sync;

  virtual size_t introOutPrepare(void *data, size_t maxlen) override;
  virtual void introInReceived(const void *data, size_t len) override;
  virtual void initIfParams(SimbricksBaseIfParams &p) override;
  virtual void handleInMsg(volatile SplitProtoM2C *msg) override;

  // These functions seem useless
  bool handleRequest(PacketPtr pkt);
  bool handleResponse(PacketPtr pkt);
  ////

  volatile union SplitProtoC2M *c2mAlloc(bool syncAlloc, bool functional);
  void handleFunctional(PacketPtr pkt);
  AddrRangeList getAddrRanges() const;
  void sendRangeChange();
  void PktToMsg(PacketPtr pkt, volatile union SplitProtoC2M *msg,
                uint8_t pkt_type);

  const AddrRangeList addrRanges;
  CPUSidePort cpu_side;
  IntReqProxyPort int_req_proxy;
  IntRespProxyPort int_resp_proxy;
  PioProxyPort pio_proxy;

  // It's a dummy mem side port (connected to a dummy memory module),
  // to not let gem5 cpu process complain about
  // the absense of memory module.
  MemSidePort mem_side;
  uint32_t reqCount;

  // Remembers request packets pointers and
  // <RequestorId, request task_Id> so that
  // we can reuse it for response received from simbricks channel

  std::unordered_map<uint32_t, PacketPtr> in_flight;

 public:
  PARAMS(SplitCPUAdapter);
  SplitCPUAdapter(const SplitCPUAdapterParams &params);
  virtual ~SplitCPUAdapter();
  void init() override;
  virtual void startup() override;
  Port &getPort(const std::string &if_name,
                PortID idx = InvalidPortID) override;
};
}  // namespace simbricks
}  // namespace gem5

#endif  //__SPLIT_CPU_ADAPTER_HH__

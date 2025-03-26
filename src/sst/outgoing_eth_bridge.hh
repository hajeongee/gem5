/*
 * Copyright 2022 Max Planck Institute for Software Systems, and
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


#ifndef __SST_OUTGOING_REQUEST_BRIDGE_HH__
#define __SST_OUTGOING_REQUEST_BRIDGE_HH__

#include <utility>
#include <vector>

#include "dev/net/etherint.hh"
#include "mem/port.hh"
#include "params/OutgoingEthBridge.hh"
#include "sim/sim_object.hh"
#include "sst/sst_responder_interface.hh"

namespace gem5
{

class OutgoingEthBridge: public SimObject
{
  public:
    class OutgoingEthPort: public EtherInt
    {
      private:
        OutgoingEthBridge* owner;
      public:
        OutgoingEthPort(const std::string &name_,
                            OutgoingEthBridge* owner_);
        ~OutgoingEthPort();
        bool recvPacket(EthPacketPtr pkt) override {
          return owner->recvPacket(pkt);
      }

      void sendDone() override {}
    };

  public:
    OutgoingEthPort *outgoingPort;
    // pointer to the corresponding SST responder
    SSTResponderInterface* sstResponder;

  public:
    OutgoingEthBridge(const OutgoingEthBridgeParams &params);
    ~OutgoingEthBridge();

    // Required to let the OutgoingEthPort to send range change request.
    void init();

    // Required to return a port during gem5 instantiate phase.
    Port & getPort(const std::string &if_name, PortID idx);

    // gem5 Component (from SST) will call this function to let set the
    // bridge's corresponding SSTResponderSubComponent (which implemented
    // SSTResponderInterface). I.e., this will connect this bridge to the
    // corresponding port in SST.
    void setResponder(SSTResponderInterface* responder);


    bool recvPacket(EthPacketPtr packet);
};

}; // namespace gem5

#endif //__SST_OUTGOING_REQUEST_BRIDGE_HH__

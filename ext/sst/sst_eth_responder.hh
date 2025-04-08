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


#ifndef __SST_ETH_RESPONDER_HH__
#define __SST_ETH_RESPONDER_HH__

#define TRACING_ON 0

#include <string>
#include <vector>

#include <sst/core/sst_config.h>
#include <sst/core/component.h>

#include <sst/core/interfaces/stringEvent.h>
#include <sst/core/interfaces/stdMem.h>
#include <sst/core/interfaces/simpleNetwork.h>

#include <sst/core/eli/elementinfo.h>
#include <sst/core/link.h>


// from gem5
#include <sim/sim_object.hh>
#include <sst/outgoing_eth_bridge.hh>
#include <sst/sst_responder_interface.hh>
#include <dev/net/etherpkt.hh>


#include "sst_eth_responder_subcomponent.hh"


class SSTEthResponderSubComponent;


class SSTEthResponder: public gem5::SSTResponderInterface
{
  private:
    SSTEthResponderSubComponent* owner;
    SST::Output* output;
  public:
    SSTEthResponder(SSTEthResponderSubComponent* owner_);
    ~SSTEthResponder() override;

    void setOutputStream(SST::Output* output_);
    
    bool handleRecvTimingReq(gem5::PacketPtr pkt) override {
      return true;
    };
    void handleRecvFunctional(gem5::PacketPtr pkt) override {};

    void handleRecvRespRetry() override{};

    void handleRecvPacket(gem5::EthPacketPtr pkt) override;

};

#endif // __SST_ETH_RESPONDER_HH__

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


#ifndef __SST_ETH_RESPONDER_SUBCOMPONENT_HH__
#define __SST_ETH_RESPONDER_SUBCOMPONENT_HH__

#define TRACING_ON 0

#include <string>
#include <vector>
#include <unordered_map>
#include <queue>

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
#include <sim/root.hh>
#include <sst/sst_responder_interface.hh>
#include <dev/net/etherpkt.hh>

#include "translator.hh"
#include "sst_eth_responder.hh"

class SSTEthResponderSubComponent: public SST::SubComponent
{
  private:
    gem5::OutgoingEthBridge* responseReceiver;
    gem5::SSTResponderInterface* sstResponder;

    // TODO: fix this with ETH interface
    SST::Interfaces::SimpleNetwork* networkInterface;
    SST::TimeConverter* timeConverter;
    SST::Output* output;

    std::string gem5SimObjectName;

  public:
    SSTEthResponderSubComponent(SST::ComponentId_t id, SST::Params& params);
    ~SSTEthResponderSubComponent();

    void init(unsigned phase);
    void setTimeConverter(SST::TimeConverter* tc);
    void setOutputStream(SST::Output* output_);

    void setResponseReceiver(gem5::OutgoingEthBridge* gem5_bridge);
    bool portEventHandler(int vn);

    bool blocked();
    void setup();

    // return true if the SimObject could be found
    bool findCorrespondingSimObject(gem5::Root* gem5_root);

    bool handleEthPacket(SST::Interfaces::SimpleNetwork::Request* request);

  public: // register the component to SST
    SST_ELI_REGISTER_SUBCOMPONENT_API(SSTEthResponderSubComponent);
    SST_ELI_REGISTER_SUBCOMPONENT(
        SSTEthResponderSubComponent,
        "gem5", // SST will look for libgem5.so or libgem5.dylib
        "gem5EthBridge",
        SST_ELI_ELEMENT_VERSION(1, 0, 0),
        "Initialize gem5 and link SST's ports to gem5's ports",
        SSTEthResponderSubComponent
    )

    SST_ELI_DOCUMENT_SUBCOMPONENT_SLOTS(
        {"eth", "Interface to the network", \
         "SST::Interfaces::SimpleNetwork"}
    )

    SST_ELI_DOCUMENT_PORTS(
        {"port", "Handling network events", {"simpleNetwork.event", ""}}
    )

    SST_ELI_DOCUMENT_PARAMS(
        {"response_receiver_name", \
         "Name of the SimObject receiving the responses"}
    )

};

#endif // __SST_ETH_RESPONDER_SUBCOMPONENT_HH__

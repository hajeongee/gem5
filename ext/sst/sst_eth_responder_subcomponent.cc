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


#include "sst_eth_responder_subcomponent.hh"

#include <cassert>
#include <sstream>
#include <iomanip>

#ifdef fatal  // gem5 sets this
#undef fatal
#endif

SSTEthResponderSubComponent::SSTEthResponderSubComponent(SST::ComponentId_t id,
                                                   SST::Params& params)
    : SubComponent(id)
{
    sstResponder = new SSTEthResponder(this);
    gem5SimObjectName = params.find<std::string>("response_receiver_name", "");
    if (gem5SimObjectName == "")
        assert(false && "The response_receiver_name must be specified");
}

SSTEthResponderSubComponent::~SSTEthResponderSubComponent()
{
    delete sstResponder;
}

void
SSTEthResponderSubComponent::setTimeConverter(SST::TimeConverter* tc)
{
    timeConverter = tc;
    int vn = 0;

    // Get the memory interface
    SST::Params interface_params;
    // This is how you tell the interface the name of the port it should use
    interface_params.insert("port", "port");
    // Loads a “memHierarchy.memInterface” into index 0 of the “memory” slot
    // SHARE_PORTS means the interface can use our port as if it were its own
    // INSERT_STATS means the interface will inherit our statistic
    //   configuration (e.g., if ours are enabled, the interface’s will be too)
    networkInterface = loadAnonymousSubComponent<SST::Interfaces::SimpleNetwork>(
        "merlin.LinkControl", "eth", 0,
        SST::ComponentInfo::SHARE_PORTS | SST::ComponentInfo::INSERT_STATS,
        interface_params, vn
    );
}

void
SSTEthResponderSubComponent::setOutputStream(SST::Output* output_)
{
    output = output_;
}

void
SSTEthResponderSubComponent::setResponseReceiver(
    gem5::OutgoingEthBridge* gem5_bridge)
{
    responseReceiver = gem5_bridge;
    responseReceiver->setResponder(sstResponder);
}

void
SSTEthResponderSubComponent::init(unsigned phase)
{
    // if (phase == 1) {
    //     for (auto p: responseReceiver->getInitData()) {
    //         gem5::Addr addr = p.first;
    //         std::vector<uint8_t> data = p.second;
    //         SST::Interfaces::StandardMem::Request* request = \
    //             new SST::Interfaces::StandardMem::Write(
    //                 addr, data.size(), data);
    //         memoryInterface->sendUntimedData(request);
    //     }
    // }
    // memoryInterface->init(phase);
}

void
SSTEthResponderSubComponent::setup()
{
}

bool
SSTEthResponderSubComponent::findCorrespondingSimObject(gem5::Root* gem5_root)
{
    gem5::OutgoingEthBridge* receiver = \
        dynamic_cast<gem5::OutgoingEthBridge*>(
            gem5_root->find(gem5SimObjectName.c_str()));
    setResponseReceiver(receiver);
    return receiver != NULL;
}

bool
SSTEthResponderSubComponent::portEventHandler(
    int vn)
{
    // Expect to handle an SST response
    return true;
}


bool
SSTEthResponderSubComponent::blocked()
{
    return false;
}

bool 
handleEthPacket(SST::Interfaces::SimpleNetwork::Request* request){
    return true;
}
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
    
    host_id = params.find<int>("host_id", -1);
    if (host_id == -1)
        assert(false && "The host_id must be specified");

}

SSTEthResponderSubComponent::~SSTEthResponderSubComponent()
{
    delete sstResponder;
}

void
SSTEthResponderSubComponent::setTimeConverter(SST::TimeConverter* tc)
{
    timeConverter = tc;
    int vn = 1;

    // Get the memory interface
    SST::Params interface_params;
    // This is how you tell the interface the name of the port it should use
    interface_params.insert("port_name", "port");
    interface_params.insert("link_bw", "1GB/s");
    // Loads a “memHierarchy.memInterface” into index 0 of the “memory” slot
    // SHARE_PORTS means the interface can use our port as if it were its own
    // INSERT_STATS means the interface will inherit our statistic
    //   configuration (e.g., if ours are enabled, the interface’s will be too)
    networkInterface = loadAnonymousSubComponent<SST::Interfaces::SimpleNetwork>(
        "merlin.linkcontrol", "eth", 0,
        SST::ComponentInfo::SHARE_PORTS | SST::ComponentInfo::INSERT_STATS,
        interface_params, vn
    );

    
    if (!networkInterface) {
        std::cerr << "Failed to load network interface" << std::endl;
        assert(false);
    }

    recv_notify_functor = new SST::Interfaces::SimpleNetwork::Handler<SSTEthResponderSubComponent>(this, &SSTEthResponderSubComponent::portEventHandler);

    networkInterface->setNotifyOnReceive(recv_notify_functor);

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
    if (phase == 1) {

    }
    networkInterface->init(phase);
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
    SST::Interfaces::SimpleNetwork::Request* req = networkInterface->recv(vn);
    if ( req != NULL ) {
        std::cout << "Received SST packet from: " << req->src << std::endl;
        delete req;
    }
    return true;
}


bool
SSTEthResponderSubComponent::blocked()
{
    return false;
}

bool 
SSTEthResponderSubComponent::handleEthPacket(SST::Interfaces::SimpleNetwork::Request* request){
    std::cout << "Sending out gem5 Eth Packet" << request->dest << std::endl;
    networkInterface->send(request, 0);
    return true;
}
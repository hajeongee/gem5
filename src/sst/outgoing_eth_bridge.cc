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


#include "sst/outgoing_eth_bridge.hh"

#include <cassert>
#include <iomanip>
#include <sstream>

#include <debug/SSTOutgoingEthBridge.hh>

#include "base/trace.hh"

namespace gem5
{

OutgoingEthBridge::OutgoingEthBridge(
    const OutgoingEthBridgeParams &params) :
    SimObject(params),
    sstResponder(nullptr) {

    outgoingPort = new OutgoingEthPort(name() + ".int0", this);

}

OutgoingEthBridge::~OutgoingEthBridge()
{
}

OutgoingEthBridge::
OutgoingEthPort::OutgoingEthPort(const std::string &name_,
                                         OutgoingEthBridge* owner_) :
    EtherInt(name_), owner(owner_)
{
    owner = owner_;
}

OutgoingEthBridge::
OutgoingEthPort::~OutgoingEthPort()
{
}

void
OutgoingEthBridge::init()
{
    if (!outgoingPort->isConnected())
        panic("outgoingPort of %s not connected!", name());

}

Port &
OutgoingEthBridge::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "int0") {
        return *outgoingPort;
    }
    return SimObject::getPort(if_name, idx);
}



void
OutgoingEthBridge::setResponder(SSTResponderInterface* responder)
{
    sstResponder = responder;
}

bool
OutgoingEthBridge::recvPacket(EthPacketPtr packet){

    DPRINTF(SSTOutgoingEthBridge, "sending out a packet\n");

    // SST responder
    sstResponder->handleRecvPacket(packet);
    return true;
}

}; // namespace gem5

// Copyright (c) 2021 The Regents of the University of California
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met: redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer;
// redistributions in binary form must reproduce the above copyright
// notice, this list of conditions and the following disclaimer in the
// documentation and/or other materials provided with the distribution;
// neither the name of the copyright holders nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include <netinet/if_ether.h>
#include <netinet/ip.h>

#include "sst_eth_responder.hh"

#include <cassert>
#include "translator.hh"


SSTEthResponder::SSTEthResponder(SSTEthResponderSubComponent* owner_)
    : gem5::SSTResponderInterface()
{
    owner = owner_;
}

SSTEthResponder::~SSTEthResponder()
{
}

void
SSTEthResponder::setOutputStream(SST::Output* output_)
{
    output = output_;
}

void
SSTEthResponder::handleRecvPacket(gem5::EthPacketPtr pkt)
{   
    // const struct ether_header* eth_hdr =
    //     reinterpret_cast<const struct ether_header*>(pkt->data);
    // const struct iphdr* ip_hdr =
    //     reinterpret_cast<const struct iphdr*>(pkt->data + sizeof(struct ether_header));
    // std::cout << "Source IP: " << ip_hdr->saddr << " to: " << ip_hdr->daddr << std::endl;
    
    
    auto eth_pkt = Translator::gem5EthPktToSSTEthPkt(
        pkt
    );
    int dest = owner->dst_id;
    int src = owner->host_id;
    eth_pkt->src = src;
    eth_pkt->dest = dest;
    owner->handleEthPacket(eth_pkt);
}

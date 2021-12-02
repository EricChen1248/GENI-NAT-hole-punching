# Install scapy on all machines
```
sudo apt update &&
sudo apt install python3-pip -y &&
pip3 install scapy
```

# NAT1
eth1 is the interface connecting NAT-1 and local net (client-1)
eth2 is the interface between NAT-1 and internet (server)
10.10.1.3 is the ip of NAT-1 in the internet
10.10.2.1 is the ip of the Client on the local net

We want to replace all outbound networks for the internet with the NAT's own ip,
in a full on setup we will want proper routing table that assigns ports according to 
Cone type NAT behaviors, but since we only have 1 client in our local net, we can
just set a fixed routing table.

```
sudo iptables -t nat -A POSTROUTING -o eth2 -j SNAT --to-source "10.10.1.3"
sudo iptables -t nat -A PREROUTING -i eth2 -j DNAT --to-destination "10.10.2.1"
```

We also want to only allow networks bound for the local net to be dropped unless it was a response from a previous connection 
Just to make the tcpdump cleaner and easier to analyze, we also drop the icmp port-unreachable message responded by the machine
when the port is unbound. Most consumer routers drop packets instead of rejecting them anyways.

```
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state NEW -j DROP
sudo iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT
sudo iptables -A OUTPUT -p icmp -m icmp --icmp-type port-unreachable -j DROP
```

For TCP, hole-punching requires NATs to view an incoming SYN message to be related to an earlier outgoing SYN message. 
This requirement is why most implementations only use UDP hole punching instead of TCP, and implement their own connection-oriented
protocol at the application layer if needed.

In our case, the firewall we are using (iptables) is one of the more stricters ones, which will consider all SYN messages to be a 
new connection. To allow us to do our testing, we add in a preliminary rule that will allow all SYN messages to be forwarded, though 
this is not a typical behavior. Allowing this behavior would actually allow direct connections through the NAT as long as port numbers
are known, but we will still implement normal hole punching techniques in our system to perform port discovery.
```
sudo iptables -I FORWARD 1 -p tcp --tcp-flags SYN SYN -j ACCEPT
```

# Client-1
GENI will automatically add routes to local-net2 through client-2 with the shortcut link we established, we want to force local-net2 to go through NAT-1 instead, so we need to add an outbound route for all 10.10.0.0/16 through nat-1-link and delete the 10.10.3.0 that goes through client-2

```
sudo route add -net 10.10.0.0 netmask 255.255.0.0 gw 10.10.2.1
sudo route del -net 10.10.3.0 netmask 255.255.255.254
```

# NAT-2 
Same as NAT-1 but with swapped out IP

```
sudo iptables -t nat -A POSTROUTING -o eth2 -j SNAT --to-source "10.10.1.2"
sudo iptables -t nat -A PREROUTING -i eth2 -j DNAT --to-destination "10.10.3.1"
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state NEW -j DROP
sudo iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT
sudo iptables -A OUTPUT -p icmp -m icmp --icmp-type port-unreachable -j DROP
sudo iptables -I FORWARD 1 -p tcp --tcp-flags SYN SYN -j ACCEPT
```

# Client-2
Same with Client-1 but with swapped out IP
```
sudo route add -net 10.10.0.0 netmask 255.255.0.0 gw 10.10.3.2
sudo route del -net 10.10.3.0 netmask 255.255.255.254
```
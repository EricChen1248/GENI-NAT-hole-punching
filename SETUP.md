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
sudo iptables -t nat -R POSTROUTING -o eth2 -p udp -j SNAT --to-source "10.10.1.3"
sudo iptables -t nat -R PREROUTING -i eth2 -p udp -j DNAT --to-destination "10.10.2.1"
```

We also want to only allow networks bound for the local net to be dropped unless it was a response from a previous connection 
Just to make the tcpdump cleaner and easier to analyze, we also drop the icmp port-unreachable message responded by the machine
when the port is unbound. Most consumer routers drop packets instead of rejecting them anyways.

```
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state NEW -j DROP
sudo iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT
sudo iptables -I OUTPUT -p icmp -m icmp --icmp-type port-unreachable -j DROP
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
sudo iptables -t nat -R POSTROUTING -o eth2 -p udp -j SNAT --to-source "10.10.1.2"
sudo iptables -t nat -R PREROUTING -i eth2 -p udp -j DNAT --to-destination "10.10.3.1"
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth2 -o eth1 -m state --state NEW -j DROP
sudo iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT
sudo iptables -I OUTPUT -p icmp -m icmp --icmp-type port-unreachable -j DROP
```

# Client-2
Same with Client-1 but with swapped out IP
```
sudo route add -net 10.10.0.0 netmask 255.255.0.0 gw 10.10.3.2
sudo route del -net 10.10.3.0 netmask 255.255.255.254
```
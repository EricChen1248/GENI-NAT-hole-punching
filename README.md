# GENI-NAT-hole-punching
A simple hole punch client-server application to test performance of TCP and UDP hole-punching compared to direct and relay connections.


On server nodes: `python3 server.py`

On client nodes:
`python3 client.py <MODE> <CLIENT_ID> udp -m <MESSAGE_SIZE>`

`<MODE>`
* direct, for direct communication.
* relay, for relay communication.
* punch, for NAT hole punching.

`<CLIENT_ID>`
* id of the client running it on (1 or 2)


`<MESSAGE_SIZE>`
* size of the message it uses to send, default 10 and is optional flag


Use tc-routes to simulate network delay and loss to gather statistics. 

https://man7.org/linux/man-pages/man8/tc-route.8.html 

import argparse

import socket
import time

relay_mapping = {}
pending_relay_mapping = {}

def udp():
    UDP_IP = "0.0.0.0"
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        mode, target, message = data.decode().split(',', 2)
        if mode == 'relay-setup':
            pending_relay_mapping[target] = addr
            print(f"pending: {pending_relay_mapping}")
            if len(pending_relay_mapping) == 2:
                for k, v in pending_relay_mapping.items():
                    sock.sendto(b"connection made", v)
                    relay_mapping[k] = v
                

                relay_mapping.clear()
                mappings = list(pending_relay_mapping.items())
                relay_mapping[mappings[0][0]] = mappings[1][1]
                relay_mapping[mappings[1][0]] = mappings[0][1]
                pending_relay_mapping.clear()

                print(f"relay setup, mapping: {relay_mapping}\n")
            

        if mode == 'relay':
            sock.sendto(message.encode(), relay_mapping[target])
            print(f'relaying message: "{message}" from {addr} to {relay_mapping[target]}')
                
def tcp():
    TCP_IP = '0.0.0.0'
    TCP_PORT = 5006
    BUFFER_SIZE = 1024

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    conn, addr = s.accept()
    print('Connection address:', addr)
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data: 
            print("connection broken")
            break
        print("received data:", data)

        
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.connect((addr[0], addr[1]))
        # s.send(data)

        conn.send(data)  # echo
        

    conn.close()

udp()
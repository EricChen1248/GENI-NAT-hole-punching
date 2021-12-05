import argparse

from _thread import *
import socket
import time

udp_relay_mapping = {}
udp_pending_relay_mapping = {}

tcp_relay_mapping = {}
tcp_pending_relay_mapping = {}

udp_punch_mapping = {}
tcp_punch_mapping = {}

def udp():
    UDP_IP = "0.0.0.0"
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    print('Listening for UDP connections')
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        mode, target, message = data.decode().split(',', 2)
        if mode == 'relay-setup':
            udp_pending_relay_mapping[target] = addr
            print(f"pending: {udp_pending_relay_mapping}")
            if len(udp_pending_relay_mapping) == 2:
                for k, v in udp_pending_relay_mapping.items():
                    sock.sendto(b"connection made", v)
                    udp_relay_mapping[k] = v
                

                udp_relay_mapping.clear()
                mappings = list(udp_pending_relay_mapping.items())
                udp_relay_mapping[mappings[0][0]] = mappings[1][1]
                udp_relay_mapping[mappings[1][0]] = mappings[0][1]
                udp_pending_relay_mapping.clear()

                print(f"relay setup, mapping: {udp_relay_mapping}\n")
            

        if mode == 'relay':
            sock.sendto(message.encode(), udp_relay_mapping[target])
            print(f'relaying message: "{message}" from {addr} to {udp_relay_mapping[target]}')

        if mode == 'punch':
            udp_punch_mapping[addr[0]] = addr
            if len(udp_punch_mapping) == 2:
                print(f"punch setup, mapping: {udp_punch_mapping}\n")
                mappings = list(udp_punch_mapping.values())
                sock.sendto(f'{mappings[0][0]},{mappings[0][1]}'.encode(), mappings[1])
                sock.sendto(f'{mappings[1][0]},{mappings[1][1]}'.encode(), mappings[0])

                udp_punch_mapping.clear()

def tcp_relay_thread(conn: socket.socket):
    while True:
        data = conn.recv(8192)
        if not data:
            print("connection terminated")
            return
        mode, target, message = data.decode().split(',')
        forward = tcp_relay_mapping[target]
        forward.sendall(data)


def tcp():
    TCP_IP = '0.0.0.0'
    TCP_PORT = 6006
    BUFFER_SIZE = 8192

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    print('Listening for TCP connections')
    while True:
        conn, addr = s.accept()
        print('Connection address:', addr)
        data = conn.recv(BUFFER_SIZE)
        if not data: 
            print("connection broken")
            break

        mode, target, message = data.decode().split(',')
        if mode == 'relay-setup':
            tcp_pending_relay_mapping[target] = conn
            if len(tcp_pending_relay_mapping) == 2:
                tcp_relay_mapping.clear()
                
                for _, conn in tcp_pending_relay_mapping.items():
                    conn.send(b"connection made")
                    start_new_thread(tcp_relay_thread, (conn,))

                mappings = list(tcp_pending_relay_mapping.items())
                tcp_relay_mapping[mappings[0][0]] = mappings[1][1]
                tcp_relay_mapping[mappings[1][0]] = mappings[0][1]
                tcp_pending_relay_mapping.clear()
        elif mode == 'punch':
            tcp_punch_mapping[conn] = addr
            if len(tcp_punch_mapping) == 2:
                print(f"punch setup, mapping: {tcp_punch_mapping}\n")
                mappings = list(tcp_punch_mapping.items())
                mappings[0][0].send(f'{mappings[1][1][1]}'.encode())
                mappings[1][0].send(f'{mappings[0][1][1]}'.encode())

                tcp_punch_mapping.clear()




if __name__ == '__main__':
    start_new_thread(tcp, ())
    udp()
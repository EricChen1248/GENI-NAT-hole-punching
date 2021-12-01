import socket
import argparse
import sys
import time
import string
import random

parser = argparse.ArgumentParser(description='Create clients that can communicate over relay, direct, or hole punch')
parser.add_argument('mode', metavar='M', type=str,
                    help='mode of communication, direct, relay, punch', choices={"direct", "relay", "punch"})
parser.add_argument('client', metavar='C', type=int, help='id of current client (0, 1)')
parser.add_argument('protocol', metavar='P', type=str, help='protocol to communicate (udp, tcp)', choices={'udp', 'tcp'})
parser.add_argument('--messagesize', '-m', metavar='m', type=int, help='size of message used to test', default=10)

args = parser.parse_args()
mode = args.mode
client = args.client
protocol = args.protocol
input = ''.join(random.choice(string.ascii_letters) for _ in range(args.messagesize))

def exit():
    sys.exit()

def create_udp_sock(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind(("0.0.0.0", port))
    return sock
            
target_ip = None
target_port = None

def setup_direct() -> socket.socket:
    global target_ip, target_port, input
    if client == 1:
        target_ip = "10.10.4.2"
        target_port = 5005
    else:
        target_ip = "10.10.4.1"
        target_port = 5006

    input = f"direct,{input}".encode()
    
    if protocol == "udp":
        sock = create_udp_sock(5006 if client == 1 else 5005)

    connected = False
    while not connected:
        if client == 1:
            sock.sendto(str(client).encode(), (target_ip, 5005))
            sock.settimeout(10)
            try:
                sock.recvfrom(1024)
            except socket.timeout:
                continue
        else:
            _, addr = sock.recvfrom(1024)
            sock.sendto(str(client).encode(), addr)
        connected = True

    return sock

def setup_relay():
    global target_ip, target_port, input
    target_ip = "10.10.1.1"
    target_port = 5005
    
    if client == 1:
        relay_target = "10.10.1.2"
    else:
        relay_target = "10.10.1.3"

    setup = f'relay-setup,{relay_target},{input}'.encode()
    input = f'relay,{relay_target},{input}'.encode()

    if protocol == 'udp':
        sock = create_udp_sock(0)

    sock.sendto(setup, (target_ip, target_port))
    sock.recvfrom(1024)

    return sock

def setup_punch() -> socket.socket:
    global target_ip, target_port, input
    server_ip = "10.10.1.1"
    target_port = 5005
    
    if client == 1:
        target_ip = "10.10.1.2"
    else:
        target_ip = "10.10.1.3"

    input = f'punch,{target_ip},{input}'.encode()

    if protocol == 'udp':
        sock = create_udp_sock(0)

    sock.sendto(input, (server_ip, target_port))
    data, _ = sock.recvfrom(1024)
    target_ip, target_port = data.decode().split(',')
    target_port = int(target_port)


    # Punch to target
    sock.sendto(input, (target_ip, target_port))
    
    if client == 1:
        time.sleep(0.5)
        sock.sendto(input, (target_ip, target_port))
        data, addr = sock.recvfrom(1024)
    else:
        data, addr = sock.recvfrom(1024)
        time.sleep(0.5)
        sock.sendto(input, (target_ip, target_port))

    
    return sock


def send_round_trip_message(sock: socket.socket, message: bytes = b'') -> int:
    if client == 1: 
        start = time.time()
        sock.sendto(message , (target_ip, target_port))
        sock.recvfrom(1024)
        end = time.time()
        return end - start
    else:
        _, addr = sock.recvfrom(1024)
        sock.sendto(input, addr)
        return None

def communicate(sock: socket.socket):
    count = 100
    total_time = 0
    for _ in range(count):
        time = send_round_trip_message(sock, input)
        if client == 1:
            total_time += time
            # print(time)
            
    if client == 1:
        print("Average:", total_time / count)






def main():
    if mode == 'direct':
        sock = setup_direct()
    if mode == 'relay':
        sock = setup_relay()
    if mode == 'punch':
        sock = setup_punch()

    print("connection setup success")

    communicate(sock)


    

if __name__ == "__main__":
    main()


exit()

import socket
import argparse
import sys
import time

parser = argparse.ArgumentParser(description='Create clients that can communicate over relay, direct, or hole punch')
parser.add_argument('mode', metavar='M', type=str,
                    help='mode of communication, direct, relay, punch', choices={"direct", "relay", "punch"})
parser.add_argument('client', metavar='C', type=int, help='id of current client (0, 1)')
parser.add_argument('protocol', metavar='P', type=str, help='protocol to communicate (udp, tcp)', choices={'udp', 'tcp'})
parser.add_argument('--message', metavar='m', type=str, help='message used to test', default='Hello World')
# parser.add_argument('--sum', dest='accumulate', action='store_const',
#                     const=sum, default=max,
#                     help='sum the integers (default: find the max)')

args = parser.parse_args()
mode = args.mode
client = args.client
protocol = args.protocol
input = args.message

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
    for _ in range(10):
        time = send_round_trip_message(sock, input)
        if client == 1:
            print(time)





def main():
    if mode == 'direct':
        sock = setup_direct()
    if mode == 'relay':
        sock = setup_relay()

    print("connection setup success")

    communicate(sock)


    

if __name__ == "__main__":
    main()


exit()

UDP_IP = "10.10.1.2"
UDP_PORT = 5006
MESSAGE = b"Hello, World!"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.bind(("0.0.0.0", 5006))

sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
addr = sock.getsockname()
print("sending from:", addr)

data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
print("received message: %s" % data)
print(f"received from {addr}")
    


TCP_IP = '10.10.1.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = b"Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
print("sent from", s.getsockname())
data = s.recv(BUFFER_SIZE)
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print("received data:", data)
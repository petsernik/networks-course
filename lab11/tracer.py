import socket
import struct
import time
import sys


def get_icmp_info(data):
    icmp_type, icmp_code = struct.unpack("!BB", data[20:22])
    return icmp_type, icmp_code


def get_checksum(data):
    checksum = 0
    for i in range(0, 8, 2):
        checksum += struct.unpack("!H", data[i: i + 2])[0]
    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum += (checksum >> 16)
    checksum = ~checksum & 0xFFFF
    return checksum


class Tracer:
    def __init__(self, target, packet_count):
        self.ICMP_HEADER_FORMAT = "!BBHHH"
        self.target = (socket.gethostbyname(target), 42)
        self.packet_count = packet_count
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.socket.settimeout(2)

    def generate_icmp_packet(self):
        packet_number = 0
        while True:
            packet_number += 1
            unverified_packet = struct.pack(self.ICMP_HEADER_FORMAT, 8, 0, 0, 1, packet_number)
            checksum = get_checksum(unverified_packet)
            yield struct.pack(self.ICMP_HEADER_FORMAT, 8, 0, checksum, 1, packet_number)

    def send_ping(self, packet, ttl):
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        try:
            self.socket.sendto(packet, self.target)
            start_time = time.time()
            data, address = self.socket.recvfrom(1024)
            end_time = time.time()
            rtt = (end_time - start_time) * 1000
            return address[0], rtt, data
        except socket.timeout:
            return None

    def trace(self):
        print(f"Tracing route to {self.target[0]}")

        ttl = 1
        current_packet = 0
        current_ip = None
        current_rtt = "{:4}".format("*")
        stop = False

        print(f"{ttl})", end="\t")

        for packet in self.generate_icmp_packet():
            result = self.send_ping(packet, ttl)
            if result is not None:
                current_ip, current_rtt, data = result
                current_rtt = "{:4.2f}".format(current_rtt)
                icmp_type, icmp_code = get_icmp_info(data)
                stop |= icmp_type == 0 & icmp_code == 0

            print(f"{current_rtt}", end="\t")

            current_packet += 1
            current_rtt = "{:4}".format("*")
            if current_packet >= self.packet_count:
                try:
                    name = socket.gethostbyaddr(current_ip)
                    print(f"{name[0]} [{current_ip}]")
                except socket.herror:
                    print(f"{current_ip}")
                except TypeError:
                    print("Request timed out")

                current_packet = 0
                current_ip = None
                ttl += 1
                if stop:
                    break
                print(f"{ttl})", end="\t")

        self.socket.close()
        print()
        print("Trace complete.")


if __name__ == "__main__":
    tracer = Tracer(sys.argv[1], int(sys.argv[2]))
    tracer.trace()

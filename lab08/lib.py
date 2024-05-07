import socket
import struct
import signal
import random


# Transmission controlling + data
class TCD:
    _header_format = "!b"

    def _make_header(self):
        return struct.pack(self._header_format, self.ack)

    def __init__(self, acknowledgment_number, data):
        self.ack = acknowledgment_number
        self.data = data

    def encode(self):
        return self._make_header() + self.data

    @staticmethod
    def decode(raw_pkg):
        if len(raw_pkg) < 1:
            raise RuntimeError("This can't be TCD package")

        (ack,) = struct.unpack(TCD._header_format, raw_pkg[:1])

        return TCD(ack, raw_pkg[1:])

    def empty(self):
        return TCD(self.ack, b"")

    def __repr__(self):
        return f"| ACK: {self.ack} [length: {len(self.data)}] |"


class Slicer:
    def __init__(self, data, bin_size):
        self.bin_size = bin_size
        self.data = data
        self.end = len(data)
        self.current = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.current += 1
        start = self.current * self.bin_size
        if start >= self.end:
            raise StopIteration
        return self.data[start: start + self.bin_size]


class TCManager:
    localhost = "127.0.0.1"

    class Timeout(Exception):
        pass

    class TransferTimeout(Exception):
        pass

    def _casino_send(self, data, dst):
        if random.randint(0, 2) > 0:
            self.sock.sendto(data, dst)
        else:
            print("[[ packet loss simulation ]]")

    def __init__(self, port, pkg_size=256, wait_ttl=1, listen_ttl=3, transfer_ttl=10):
        self.port = port
        self.wait_ttl = wait_ttl
        self.listen_ttl = listen_ttl
        self.transfer_ttl = transfer_ttl
        self.pkg_size = pkg_size
        self.ack = 0

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.localhost, self.port))
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.sock.close()

    def _rdt_rcv(self):
        pkt, addr = self.sock.recvfrom(self.pkg_size)
        return TCD.decode(pkt), addr

    def _wait_ack(self, ack, dst):
        while True:
            try:
                rcvpkt, addr = self._rdt_rcv()
            except RuntimeError:
                continue
            if addr != dst or rcvpkt.ack != ack:
                continue
            break

    def _rdt_send(self, chunk, dst):
        def timeout(signum, stack):
            print("It looks like packet is lost")
            raise self.Timeout

        ack = self.ack
        while True:
            sndpkt = TCD(ack, chunk)
            print(f"Send packet {sndpkt}")
            self._casino_send(sndpkt.encode(), dst)
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(self.wait_ttl)
            try:
                self._wait_ack(ack, dst)
            except self.Timeout:
                continue
            signal.alarm(0)
            break

        self.ack = 1 - ack

    def sendto(self, filepath, dst):
        def timeout(signum, stack):
            print("Transfer took too long")
            raise self.TransferTimeout

        with open(filepath, "rb") as entry:
            data = entry.read()

        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(self.transfer_ttl)
        try:
            for number, chunk in enumerate(Slicer(data, self.pkg_size - 1)):
                print(f"Sending chunk #{number}")
                self._rdt_send(chunk, dst)
        except self.TransferTimeout:
            return False
        print("Sent!")
        signal.alarm(0)
        return True

    def _listen(self, src):
        while True:
            try:
                rcvpkt, addr = self._rdt_rcv()
            except RuntimeError:
                continue
            if addr != src:
                continue
            return rcvpkt

    def recvfrom(self, src):
        def timeout(signum, stack):
            print("Cancel listening, finalizing result")
            raise self.TransferTimeout

        data = b""

        prev_ack = -1
        while True:
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(self.listen_ttl)
            try:
                pkt = self._listen(src)
            except self.TransferTimeout:
                return data
            signal.alarm(0)
            if pkt.ack != prev_ack:  # not a duplicate
                print(f"Receive new packet: {pkt}")
                prev_ack = pkt.ack
                data += pkt.data
            else:
                print("Receive a duplicate")
            print(f"Send acknowledgment: {pkt.empty()}")
            self._casino_send(pkt.empty().encode(), src)  # acknowledgment
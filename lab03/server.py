from threading import Thread
from queue import Queue
import socket
import re
import os
import sys

HOST = "127.0.0.1"
PORT, concurrency_level = int(sys.argv[1]), int(sys.argv[2])

available_ports = Queue()
threads_sockets = {}


def get_open_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def init_available_ports():
    for _ in range(concurrency_level):
        port = get_open_port()
        available_ports.put(port)
        threads_sockets[port] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threads_sockets[port].bind((HOST, port))
        threads_sockets[port].listen()


def handle_process(port):
    def handle():
        global available_ports
        s = threads_sockets[port]
        conn, addr = s.accept()
        with conn:
            request_raw = b''
            while True:
                batch = conn.recv(1024)
                request_raw = request_raw + batch
                if len(batch) < 1024:
                    break

            request = request_raw.decode("utf-8")
            print(request)
            filematch = re.match('.*GET /(.*) HTTP.*', request)
            filename = ""

            if filematch:
                filename = str(filematch.group(1))
            if not os.path.exists(filename):
                conn.send(f"HTTP/1.1 404 Not Found\n\n".encode())
            else:
                with open(filename, 'rb') as file:
                    data = f"HTTP/1.1 200 OK\n\n".encode()
                    conn.send(data + file.read())

        available_ports.put(port)

    return handle


def main_process():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(1000)
        init_available_ports()
        while True:
            conn, addr = sock.accept()
            with conn:
                request_raw = b''
                while True:
                    batch = conn.recv(1024)
                    request_raw = request_raw + batch
                    if len(batch) < 1024:
                        break

                request = request_raw.decode("utf-8")
                filematch = re.match('.*GET /(.*) HTTP.*', request)

                if filematch:
                    filepath = filematch.group(1)

                while available_ports.empty():
                    pass

                port = available_ports.get()
                thread = Thread(target=handle_process(port))
                conn.send(f"HTTP/1.1 307 Temporary Redirect\n"
                          f"Location: http://{HOST}:{port}/{filepath}".encode())

                thread.start()


main_thread = Thread(target=main_process())

main_thread.start()
main_thread.join()

for _ in threads_sockets:
    threads_sockets[_].close()

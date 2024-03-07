import socket
import re
import sys

host, port, filename = sys.argv[1], int(sys.argv[2]), sys.argv[3]

request = f"GET /{filename} HTTP/1.1\n\
Host: {host}:{port}\n\
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7\n\
Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(request.encode())

        received_raw = b''
        while True:
            batch = client.recv(1024)
            received_raw = received_raw + batch
            if len(batch) < 1024:
                break

        received = received_raw.decode("utf-8")

        print(received)
        print()

        if received.splitlines()[0] == "HTTP/1.1 200 OK":
            break
        else:
            port = int(re.search(f"Location: http://{host}:(.*)/{filename}",
                                 received.splitlines()[1]).group(1))

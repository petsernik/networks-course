import argparse
import time

from lib import TCManager


def main():
    parser = argparse.ArgumentParser("HW8")
    parser.add_argument("wait_timeout", type=int)
    parser.add_argument("listen_timeout", type=int)
    parser.add_argument("transfer_timeout", type=int)
    args = parser.parse_args()

    with TCManager(8572, 4, args.wait_timeout, args.listen_timeout, args.transfer_timeout) as server:
        data = server.recvfrom((TCManager.localhost, 8017))
        with open("server_received.txt", "wb") as file:
            file.write(data)
        time.sleep(2)
        server.sendto("server_data.txt", (TCManager.localhost, 8017))


if __name__ == "__main__":
    main()

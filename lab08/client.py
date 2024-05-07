import argparse
import time

from lib import TCManager


def main():
    parser = argparse.ArgumentParser("HW8")
    parser.add_argument("wait_timeout", type=int)
    parser.add_argument("listen_timeout", type=int)
    parser.add_argument("transfer_timeout", type=int)
    args = parser.parse_args()

    with TCManager(8017, 4, args.wait_timeout, args.listen_timeout, args.transfer_timeout) as client:
        client.sendto("client_data.txt", (TCManager.localhost, 8572))
        time.sleep(args.transfer_timeout // 2)
        data = client.recvfrom((TCManager.localhost, 8572))
        with open("client_received.txt", "wb") as file:
            file.write(data)


if __name__ == "__main__":
    main()

import threading
import argparse
import socket
import re
import os
import time

LOCALHOST = "127.0.0.1"
HOST_HEADER = b"Host: "
CACHE_FOLDER = "cache"
LAST_MODIFIED_HEADER = b"Last-Modified: "
ETAG_HEADER = b"ETag: "
IF_MODIFIED_SINCE_HEADER = b"If-Modified-Since: "
IF_NONE_MATCH_HEADER = b"If-None-Match: "
ENDL = "\r\n"
DOUBLE_ENDL = ENDL + ENDL

RESPONSE_500 = "HTTP/1.1 500 Internal Server Error" + DOUBLE_ENDL
RESPONSE_423 = "HTTP/1.1 423 Locked" + DOUBLE_ENDL
RESPONSE_400 = "HTTP/1.1 400 Bad Request" + DOUBLE_ENDL
RESPONSE_404 = "HTTP/1.1 404 Not Found" + DOUBLE_ENDL
REQUEST_RE = r"(\w*) \/([^\s\/]*)(.*)"
RESPONSE_RE = r"HTTP\/\d\.\d (\d*) .*"
RESPONSE_502 = "HTTP/1.1 502 Bad Gateway" + DOUBLE_ENDL
RESPONSE_504 = "HTTP/1.1 504 Gateway Timeout" + DOUBLE_ENDL


def get(host, request):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # server.settimeout(20)
            print(f"[MESSAGE] Trying connect to {host}")
            server.connect((host, 80))
            print(f"[MESSAGE] Connection accepted. Send request")
            server.sendall(_replace_host(request, host))

            response_raw = b''
            while True:
                batch = server.recv(1024)
                response_raw = response_raw + batch
                if len(batch) < 1024:
                    break

            if len(response_raw) == 0:
                return False, RESPONSE_502.encode()

            return True, response_raw
    except socket.timeout:
        return False, RESPONSE_504.encode()
    except Exception as e:
        return False, RESPONSE_404


def _replace_host(request, new_host):
    host_lb = request.find(HOST_HEADER)
    if host_lb == -1:
        return request

    host_rb = request[host_lb:].find(ENDL.encode())
    if host_rb == -1:
        host_rb = len(request) - host_lb
        request += DOUBLE_ENDL

    ret = request[:host_lb] + HOST_HEADER + new_host.encode() + request[host_lb + host_rb:]
    return ret


def get_main_part(request):
    main_part_end = request.find(ENDL.encode())
    if main_part_end == -1:
        main_part_end = len(request)

    return request[:main_part_end].decode()


def get_code(response):
    code_end = response.find(ENDL.encode())
    if code_end == -1:
        code_end = len(response)
    matched = re.match(RESPONSE_RE, response[:code_end].decode())
    if not matched:
        return None

    return int(matched.group(1))


def _is_expired(host, request, expiration, etag):
    headers_end = request.find(DOUBLE_ENDL)
    if headers_end == -1:
        headers_end = len(request)

    updated_request = request[:headers_end]

    if_modified_since_begin = updated_request.find(ENDL + "If-Modified-Since: ")
    if if_modified_since_begin == -1:
        if_modified_since_begin = len(updated_request)

    if_modified_since_end = updated_request[if_modified_since_begin + 2:].find(ENDL)
    if if_modified_since_end == -1:
        if_modified_since_end = len(updated_request) - (if_modified_since_begin + 2)

    updated_request = (updated_request[:if_modified_since_begin]
                       + ENDL + f"If-Modified-Since: {expiration}"
                       + updated_request[if_modified_since_begin + 2 + if_modified_since_end:])

    if_none_match_begin = updated_request.find(ENDL + "If-None-Match: ")
    if if_none_match_begin == -1:
        if_none_match_begin = len(updated_request)

    if_none_match_end = updated_request[if_none_match_begin + 2:].find(ENDL)
    if if_none_match_end == -1:
        if_none_match_end = len(updated_request) - (if_none_match_begin + 2)

    updated_request = (updated_request[:if_none_match_begin]
                       + ENDL + f'If-None-Match: "{etag}"'
                       + updated_request[if_none_match_begin + 2 + if_none_match_end:])

    if request.find(ENDL + "Host: ") == -1:
        updated_request += ENDL + f"Host: {host}"

    updated_request += DOUBLE_ENDL

    successful, res = get(host, updated_request.encode())

    return not successful or get_code(res) != 304


def _remove_header(http, header):
    header_begin = http.find(header)
    if header_begin == -1:
        return http

    header_end = http[header_begin:].find(ENDL.encode())
    if header_end == -1:
        header_end = len(http) - header_begin

    return http[:header_begin] + http[header_begin + header_end + 2:]


def get_url(request):
    return get_main_part(request)[len('GET /'):][:-len(' HTTP/1.1')]


class CachingProxy:
    def __init__(self, cache_folder, logger, blacklist):
        self.cache_folder = cache_folder
        self.cache_map = dict()
        self.blacklist = blacklist
        self.logger = logger

    def save(self, request, response, last_modified, etag):
        with open(os.path.join(self.cache_folder, f"{etag}"), "wb") as f:
            print(f"[SAVED TO CACHE] {request}")
            f.write(response)
            self.cache_map[request] = (last_modified, etag)

    def _load(self, etag):
        with open(os.path.join(self.cache_folder, etag), "rb") as f:
            return f.read()

    def _acquire(self, method, request, host, inner_request):
        successful, res = get(host,
                              _remove_header(
                                  _remove_header(inner_request, IF_MODIFIED_SINCE_HEADER),
                                  IF_NONE_MATCH_HEADER)
                              )
        if not successful:
            print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
            return res

        if method == "GET":
            expiration_lb = res.find(LAST_MODIFIED_HEADER)
            etag_lb = res.find(ETAG_HEADER)

            if expiration_lb == -1 or etag_lb == -1:
                print("[MESSAGE] Can't cache this request")
                print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
                return res

            expiration_rb = res[expiration_lb:].find(ENDL.encode())
            etag_rb = res[etag_lb:].find(ENDL.encode())

            expiration = res[expiration_lb:][len(LAST_MODIFIED_HEADER): expiration_rb].decode()
            etag = res[etag_lb:][len(ETAG_HEADER) + 1: etag_rb - 1].decode()

            self.save(get_main_part(request), res, expiration, etag)

            res = _remove_header(_remove_header(res, LAST_MODIFIED_HEADER), ETAG_HEADER)

        print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
        return res

    def _is_url_in_blacklist(self, request):
        url = get_url(request)
        urls = url.split('/')
        ans = False
        cur = ''
        for part in urls:
            cur += part
            ans = ans or (cur in self.blacklist)
            cur += '/'
            ans = ans or (cur in self.blacklist)
        return ans

    def get(self, request):
        try:
            main_end = request.find(ENDL.encode())
            if main_end == -1:
                main_end = len(request)
            try:
                matched = re.match(REQUEST_RE, request[:main_end].decode())
            except:
                matched = False
            if not matched:
                res = RESPONSE_400.encode()
                try:
                    print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
                except Exception as e:
                    pass
                return res

            method, host, tail = [matched.group(i) for i in range(1, 4)]

            if self._is_url_in_blacklist(request):
                res = RESPONSE_502.encode()

                try:
                    print(f"[MESSAGE] Access to {get_url(request)} not allowed")
                    print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
                except Exception as e:
                    pass
                return res

            maybe_slash = ''
            if tail[0] != '/':
                maybe_slash = '/'

            inner_request = f"{method} {maybe_slash}{tail}".encode() + request[main_end:]
            main_part = get_main_part(request)

            if method == 'GET' and main_part in self.cache_map:
                expiration, etag = self.cache_map[main_part]
                if not _is_expired(host, inner_request.decode(), expiration, etag):
                    res = self._load(etag)
                    print(f"[GET FROM CACHE] {main_part} - {get_code(res)}")
                    return res
                else:
                    del self.cache_map[inner_request]
                    os.remove(os.path.join(self.cache_folder, etag))

            return self._acquire(method, request, host, inner_request)
        except Exception as e:
            res = RESPONSE_404.encode()
            try:
                print(f"{get_main_part(request)} - {get_code(res)}", file=self.logger)
            except Exception as e:
                pass
            return res


class Proxy:
    def __init__(self, port, cache_folder, logger, __blacklist):
        self.host = LOCALHOST
        self.port = port
        self.cacher = CachingProxy(cache_folder, logger, __blacklist)
        self.logger = logger

    def listen(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.bind((self.host, self.port))
                # listener.settimeout(20)
                listener.listen(5)
                while running:
                    conn, addr = listener.accept()
                    with conn:
                        try:
                            request_raw = b''
                            while True:
                                batch = conn.recv(1024)
                                request_raw = request_raw + batch
                                if len(batch) < 1024:
                                    break
                            ret = self.cacher.get(request_raw)
                            conn.sendall(ret)
                        except socket.timeout:
                            print("[TIMEOUT EXCEED]")
                            continue
        except KeyboardInterrupt:
            print("[STOP SERVER]")
            return


def run_server():
    with open(args.logfile, "w") as logger:
        server = Proxy(args.port, CACHE_FOLDER, logger, blacklist)
        server.listen()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('logfile', type=str)
    parser.add_argument('blacklist', type=str)
    args = parser.parse_args()

    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    with open(args.blacklist, "r") as config:
        hosts = config.read().split('\n')
        blacklist = set(hosts)

    running = True
    thread = threading.Thread(target=run_server())
    thread.start()

    try:
        while thread.isAlive():
            time.sleep(1)
    except Exception:
        running = False
        print("[EXIT]")

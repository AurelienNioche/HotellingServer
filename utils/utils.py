from datetime import datetime
import inspect
import socket


def function_name():
    return inspect.stack()[1][3]


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.0.0.8', 2155))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


class Logger:

    name = "Logger"

    @classmethod
    def log(cls, msg):

        print("{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), cls.name, msg))

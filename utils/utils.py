from datetime import datetime
import inspect
import socket
import click


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
    debug = 0

    @classmethod
    def log(cls, msg, level=0):

        stamp = "{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), cls.name, msg)

        # Colour codes for different error levels
        colors = ["cyan", "green", "yellow", "red"]

        # Labels for different log levels
        log_levels = ["[Debug]   ", "[Info]    ", "[Warning] ", "[Error]   "]

        # Display error level of log event, current time and log description
        # If debug is enabled print all logs
        if cls.debug:
            click.echo(click.style(log_levels[level], fg=colors[level]) + stamp)

        # If debug is disabled only print errors, warnings, and infos
        elif not cls.debug and level > 0:
            click.echo(click.style(log_levels[level], fg=colors[level]) + stamp)


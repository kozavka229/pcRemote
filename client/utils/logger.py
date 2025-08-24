import os
from typing import BinaryIO

from client import config

LOGS_DIR = 'logs'
__f: BinaryIO | None = None

def setfile(name: str):
    global __f

    if not os.path.exists(LOGS_DIR):
        os.mkdir(LOGS_DIR)
    __f = open(os.path.join(LOGS_DIR, name), 'ab')

def log(data: bytes, end: bytes = '\n'.encode()):
    if config.LOG and __f:
        __f.write(data)
        __f.write(end)
        __f.flush()

def closefile():
    global __f
    if __f is None or __f.closed:
        return

    __f.close()
    __f = None

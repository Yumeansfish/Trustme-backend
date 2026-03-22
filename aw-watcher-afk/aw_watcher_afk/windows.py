import ctypes
import time
from ctypes.wintypes import BOOL, DWORD, UINT


class LastInputInfo(ctypes.Structure):
    _fields_ = [("cbSize", UINT), ("dwTime", DWORD)]


def _getLastInputTick() -> int:
    prototype = ctypes.WINFUNCTYPE(BOOL, ctypes.POINTER(LastInputInfo))
    paramflags = ((1, "lastinputinfo"),)
    c_GetLastInputInfo = prototype(("GetLastInputInfo", ctypes.windll.user32), paramflags)  # type: ignore

    lastinput = LastInputInfo()
    lastinput.cbSize = ctypes.sizeof(LastInputInfo)
    assert 0 != c_GetLastInputInfo(lastinput)
    return lastinput.dwTime


def _getTickCount() -> int:
    prototype = ctypes.WINFUNCTYPE(DWORD)
    paramflags = ()
    c_GetTickCount = prototype(("GetTickCount", ctypes.windll.kernel32), paramflags)  # type: ignore
    return c_GetTickCount()


def seconds_since_last_input():
    seconds_since_input = (_getTickCount() - _getLastInputTick()) / 1000
    return seconds_since_input


if __name__ == "__main__":
    while True:
        time.sleep(1)
        print(seconds_since_last_input())

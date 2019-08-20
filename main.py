from os import path, mkdir
import atexit


import pytest


from private import auth
from trabot import trader
from trabot import data as d
from trabot.side import Side


def main():
    t = trader.Trader(auth, 'DOGEBTC', silent=False, need_confirmation=False)
    atexit.register(t.at_exit)
    t.start(Side(d.BUY))


if __name__ == "__main__":
    ERRNO = pytest.main(['-vv'])
    print('Tests finished with code', ERRNO)
    if ERRNO == 0:
        if not path.exists('data'):
            mkdir('data')
        main()

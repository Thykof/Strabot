from os import path, mkdir
import atexit


import pytest


from private import auth
from trabot.trader import Trader
from trabot import data as d
from trabot.side import Side


def main():
    trader = Trader(auth, 'BTCUSD', silent=False, need_confirmation=False,
                    price_depth=1, security_level=60, expire_time=20,
                    min_margin=10)
    atexit.register(trader.at_exit)
    trader.start(Side(d.SELL))
    # TODO: limit order doesn't expire, but modify it when usefull i.e.
    # price from orderbook above profitable price


if __name__ == "__main__":
    ERRNO = pytest.main(['-vv'])
    print('Tests finished with code', ERRNO)
    if ERRNO == 0:
        if not path.exists('data'):
            mkdir('data')
        main()

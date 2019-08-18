from os import path, mkdir
import atexit


from trabot import trader
from private import auth
from trabot import data as d
from trabot.side import Side


def main():
    t = trader.Trader(auth, 'DOGEBTC', silent=False, need_confirmation=False)
    atexit.register(t.at_exit)
    t.start(Side(d.SELL))
    # TODO: don't move position in a no profitable zone, look at to the previous trade


if __name__ == "__main__":
    if not path.exists('data'):
        mkdir('data')
    main()

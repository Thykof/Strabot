from trabot import data as d
from trabot.exception import TraderError


class Side:
    def __init__(self, side, order=None, spread=None):
        if order:
            assert side in (d.SELL, d.BUY)
        elif spread:
            assert side in (d.ASK, d.BID)
        else:
            assert side in (d.SELL, d.BUY, d.ASK, d.BID)

        self.s = side

    def __str__(self):
        return self.s

    def oposite(self):
        if self.s == d.BUY:
            return Side(d.SELL)
        if self.s == d.SELL:
            return Side(d.BUY)
        if self.s == d.ASK:
            return Side(d.BID)
        if self.s == d.BID:
            return Side(d.ASK)
        raise TraderError('invalid side')

    def to_spread(self):
        if self.s == d.BUY:
            return Side(d.BID)
        if self.s == d.SELL:
            return Side(d.ASK)
        raise TraderError('invalid side')

    def to_order(self):
        if self.s == d.BID:
            return Side(d.BUY)
        if self.s == d.ASK:
            return Side(d.SELL)
        raise TraderError('invalid side')

    def switch(self):
        if self.s == d.BUY:
            return Side(d.ASK)
        if self.s == d.SELL:
            return Side(d.BID)
        if self.s == d.ASK:
            return Side(d.BUY)
        if self.s == d.BID:
            return Side(d.SELL)
        raise TraderError('invalid side')

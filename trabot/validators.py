import math


from trabot import data as d
from trabot.helpers import log
from trabot.exception import TraderError


def validate_price(symbol, price):
    if math.modf(price / symbol['tickSize'])[0] != 0:
        raise TraderError('price should be divided by tickSize without residue')
    # TODO: buy price can't be the best ask price and vice versa

def validate_quantity(symbol, quantity):
    if math.modf(quantity / symbol['quantityIncrement'])[0] != 0:
        msg = 'quantity should be divided by quantityIncrement without residue'
        raise TraderError(msg)

def validate_stop_price(stop_price, price, side):
    log(str(side))
    if str(side) not in [d.BUY, d.SELL]:
        log(str(side))
        raise TraderError('invalid side')
    if (str(side) == d.BUY and stop_price >= price or
        str(side) == d.SELL and stop_price <= price):
        msg = 'invalid stop price: stop: {}, limit: {}'.format(
            str(stop_price), str(price))
        raise TraderError(msg)

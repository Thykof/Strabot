import datetime
from decimal import Decimal
import json


from trabot.helpers import log
from trabot.exception import TraderError
from trabot import data as d


def confirm(name, message=None, data=None):
    if data:
        log(data)
    m = str()
    if message is not None:
        m = message
    else:
        m = {
            'order': 'about to place an order... ',
            'retry': 'retry previous operation ? '
        }[name]
    log('CONFIRMATION')
    response = input(m)
    if response != 'y':
        log('confirmation aborted')
        return False
    return True

def get_now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def get_now_plus(seconds, days=0, microseconds=0, hours=0):
    return (datetime.datetime.utcnow() + datetime.timedelta(
        seconds=seconds,
        days=days,
        microseconds=microseconds,
        hours=hours
        )).replace(microsecond=0).isoformat()

def get_fee(order, symbol):
    return (Decimal(order['quantity'])
            * Decimal(order['price'])
            * Decimal(symbol['provideLiquidityRate'])
            ).quantize(Decimal('0.000000000001'))

def get_breakeven(order, side, min_margin, symbol):
    assert order['tradesReport']['fee'] == get_fee({
        'quantity': order['tradesReport']['quantity'],
        'price': order['tradesReport']['price']
    }, symbol)
    if str(side) == d.BUY:
        breakeven_price = (
            min_margin / order['tradesReport']['quantity']
            - (order['tradesReport']['price']
               * (1 - symbol['takeLiquidityRate']))
            / (1 + symbol['takeLiquidityRate'])
        )
    elif str(side) == d.SELL:
        breakeven_price = (
            min_margin / order['tradesReport']['quantity']
            + (order['tradesReport']['price']
               * (1 + symbol['takeLiquidityRate']))
            / (1 - symbol['takeLiquidityRate'])
        )
    else:
        raise TraderError("side must be 'buy' or 'sell'")
    return breakeven_price

def get_profitable_price(filled_order, price, side, min_margin, symbol):
    breakeven_price = get_breakeven(filled_order, side, min_margin, symbol)
    log(breakeven_price)
    if str(side) == d.BUY:
        return min(breakeven_price, price)
    if str(side) == d.SELL:
        return max(breakeven_price, price)
    raise TraderError("side must be 'buy' or 'sell'")

def store_order(current_position, current_stop, orders):
    with open('data/orders.json', 'w+') as json_file:
        content = json_file.read()
        if content:
            orders = json.loads(content)
        else:
            orders = []
        orders.extend(current_position or [])
        orders.extend(current_stop or [])
        orders.extend(orders)
        json.dump(orders, json_file, indent=2)

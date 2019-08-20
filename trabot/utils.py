import datetime
from decimal import Decimal
import json


from trabot.helpers import log
from trabot.exception import TraderError
from trabot import data as d


def confirm(name, message=None, data=None):
    if data:
        log(data)
    msg = str()
    if message is not None:
        msg = message
    else:
        msg = {
            'order': 'about to place an order... ',
            'retry': 'retry previous operation ? '
        }[name]
    log('CONFIRMATION')
    response = input(msg)
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
            ).quantize(Decimal(symbol['tickSize']))


def get_breakeven(order, side, symbol):
    if str(side) == d.BUY:
        breakeven_price = (
            (Decimal(order['tradesReport'][0]['price'])
             * (1 - Decimal(symbol['provideLiquidityRate'])))
            / (1 + Decimal(symbol['provideLiquidityRate']))
        )
    elif str(side) == d.SELL:
        breakeven_price = (
            (Decimal(order['tradesReport'][0]['price'])
             * (1 + Decimal(symbol['provideLiquidityRate'])))
            / (1 - Decimal(symbol['provideLiquidityRate']))
        )
    else:
        raise TraderError("side must be 'buy' or 'sell'")
    return Decimal(breakeven_price).quantize(Decimal(symbol['tickSize']))


def get_profitable_price(filled_order, price, side, min_margin, symbol):
    breakeven_price = get_breakeven(filled_order, side, symbol)
    log('breakeven_price ' + str(breakeven_price))
    if str(side) == d.BUY:
        return min(
            breakeven_price - Decimal(str(min_margin))
            * Decimal(symbol['tickSize']), price)
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

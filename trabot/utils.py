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


def get_profitable_price(filled_order, orderbook_price, side, min_margin,
                         symbol):
    breakeven_price = get_breakeven(filled_order, side, symbol)
    log('breakeven_price ' + str(breakeven_price))
    if str(side) == d.BUY:
        profitable_price = breakeven_price - Decimal(str(min_margin)) * (
            Decimal(filled_order['tradesReport'][0]['price'])
            - breakeven_price
        )
        return min(profitable_price, orderbook_price)
    if str(side) == d.SELL:
        profitable_price = breakeven_price + Decimal(str(min_margin)) * (
            breakeven_price
            - Decimal(filled_order['tradesReport'][0]['price'])
        )
        return max(profitable_price, orderbook_price)
    # TODO: instead of + ticksize, + min_margin * (Pv - PBE)
    raise TraderError("side must be 'buy' or 'sell'")


def store_orders(current_position, current_stop, new_orders,
                 filename='data/orders.json'):
    with open(filename, 'w+') as json_file:
        content = json_file.read()
        if content:
            orders = json.loads(content)
        else:
            orders = []
        if current_position:
            orders.append(current_position)
        if current_stop:
            orders.append(current_stop)
        orders.extend(new_orders)
        orders_ = list()
        for order in orders:
            for key in order.keys():
                if isinstance(order[key], Decimal):
                    order[key] = str(order[key])
                elif isinstance(order[key], dict):
                    for k in order[key].keys():
                        if isinstance(order[key][k], Decimal):
                            order[key][k] = str(order[key][k])
            orders_.append(order)
        json.dumps(orders_, indent=2)

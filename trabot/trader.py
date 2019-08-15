"""Trader"""

import json
import atexit
import datetime
import math
import threading
import dateutil.parser


from private import auth as keys
from trabot.client import Client
from trabot import utils
from trabot.utils import tell


TRUE = 'true'
FALSE = 'flase'

class Side:
    def __init__(self, side, order=None, spread=None):
        if order:
            assert side in ('sell', 'buy')
        elif spread:
            assert side in ('ask', 'bid')
        else:
            assert side in ('sell', 'buy', 'ask', 'bid')

        self.s = side

    def __str__(self):
        return self.s

    def oposite(self):
        if self.s == 'buy':
            return Side('sell')
        if self.s == 'sell':
            return Side('buy')
        if self.s == 'ask':
            return Side('bid')
        if self.s == 'bid':
            return Side('ask')

    def to_spread(self):
        assert self.s in ('sell', 'buy')
        if self.s == 'buy':
            return Side('bid')
        if self.s == 'sell':
            return Side('ask')

    def to_order(self):
        assert self.s in ('ask', 'bid')
        if self.s == 'bid':
            return Side('buy')
        if self.s == 'ask':
            return Side('sell')

    def switch(self):
        if self.s == 'buy':
            return Side('ask')
        if self.s == 'sell':
            return Side('bid')
        if self.s == 'ask':
            return Side('buy')
        if self.s == 'bid':
            return Side('sell')

class WaitThread(threading.Thread):
    def __init__(self, func, *args, **kargs):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kargs = kargs
        self.done = False  # True when result is available
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kargs)
        self.done = True


def get_now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def get_now_plus(seconds, days=0, microseconds=0, hours=0):
    return (datetime.datetime.utcnow() + datetime.timedelta(
        seconds=seconds,
        days=days,
        microseconds=microseconds,
        hours=hours
        )).replace(microsecond=0).isoformat()

def confirm(name, message=None, data=None):
    if data:
        utils.print_obj(data)
    m = str()
    if message is not None:
        m = message
    else:
        m = {
            'order': 'about to place an order... '
        }[name]
    tell('CONFIRMATION')
    response = input(m)
    if response != 'y':
        tell('confirmation aborted')
        return False
    return True

def validate_price(self, **kargs):
    if math.modf(kargs['price'] % self.symbol['tickSize'])[1] != 0:
        raise ValueError('price should be divided by tickSize without residue')

def validate_quantity(self, **kargs):
    if math.modf(kargs['quantity'] % self.symbol['quantityIncrement'])[1] != 0:
        raise ValueError('quantity should be divided by quantityIncrement without residue')

def validate_stop_price(stop_price, price, side):
    if str(side) == 'buy':
        assert stop_price < price
    elif str(side) == 'sell':
        assert stop_price > price
    else:
        tell(str(side))
        raise ValueError('invalid side object')


class Trader:
    def __init__(self, auth, symbol_code, silent=True, expire_time=None, wait=None, need_confirmation=True):
        self.c = Client("https://api.hitbtc.com", auth[0], auth[1])
        self.symbol_code = symbol_code
        self.silent = silent
        self.symbol = self.c.get_symbol(self.symbol_code)
        self.symbol['quantityIncrement'] = float(self.symbol['quantityIncrement'])
        self.symbol['tickSize'] = float(self.symbol['tickSize'])
        self.symbol['takeLiquidityRate'] = float(self.symbol['takeLiquidityRate'])
        self.symbol['provideLiquidityRate'] = float(self.symbol['provideLiquidityRate'])
        self.price_range = 10
        self.trade_price = self.price_range * self.symbol['tickSize']
        self.relative_quantity = 1
        self.trade_quantity = (self.relative_quantity
            * float(self.symbol['quantityIncrement']))
        self.security_level = 4
        self.price_depth = 1
        self.expire_time = expire_time or 60
        self.wait = wait or 20
        self.orders = list()
        # self.orders_stop = list()
        self.current_position = list()
        self.need_confirmation = need_confirmation

    # Validators
    def validate_price(func):
        def valid(self, **kargs):
            validate_price(self, **kargs)
            return func(self, **kargs)
        return valid

    def validate_quantity(func):
        def valid(self, **kargs):
            validate_quantity(self, **kargs)
            return func(self, **kargs)
        return valid

    def set_price_range(self, price_range):
        self.price_range = price_range
        self.trade_price = self.price_range * self.symbol['tickSize']

    def get_min_past_trade(self):
        trades = self.c.get_trades_public(self.symbol_code)
        if not self.silent:
            utils.print_obj(trades, 10)
        min_price = trades[0]['price']
        for trade in trades:
            if min_price > trade['price']:
                min_price = trade['price']
        return float(min_price)

    def get_min_orderbook(self, side, limit):
        tell('get_min_orderbook ' + str(side))
        orderbook = self.c.get_orderbook(self.symbol_code, limit)
        if not self.silent:
            utils.print_obj(orderbook, 10)
        return float(orderbook[side.s][-1]['price'])

    def store_order(self):
        with open('data/orders.json', 'w+') as json_file:
            content = json_file.read()
            if content:
                orders = json.loads(content)
            else:
                orders = []
            orders.extend(self.current_position)
            orders.extend(self.orders)
            json.dump(orders, json_file, indent=2)

    def cancel_orders(self):
        for order in self.current_position:
            if order['status'] not in ['filled', 'expired', 'cancel']:
                response = self.c.cancel_order(order['clientOrderId'])
                if not self.silent:
                    utils.print_obj(response, 10)

    def place_order(self, side):
        validate_quantity(self, quantity=self.trade_quantity)
        price = self.get_min_orderbook(side.to_spread(), self.price_depth)
        validate_price(self, price=price)
        data = {
            'symbol': self.symbol_code,
            'side': side.s,
            'quantity': self.trade_quantity,
            'type': 'limit',
            'price': price,
            'timeInForce': 'GTD',
            'expireTime': get_now_plus(seconds=self.expire_time),
            'strictValidate': TRUE,
            'postOnly': TRUE
        }
        stop_price = self.get_min_orderbook(
            side.to_spread(),
            self.price_depth + self.security_level
        )
        validate_stop_price(stop_price, price, side)
        data_stop = {
            'symbol': self.symbol_code,
            'side': str(side.oposite()),
            'quantity': self.trade_quantity,
            'type': 'stopLimit',
            'price': stop_price,
            'stopPrice': stop_price,
            'timeInForce': 'GTD',
            'expireTime': get_now_plus(seconds=self.expire_time * 2),
            'strictValidate': TRUE,
            'postOnly': TRUE
        }
        if self.need_confirmation:
            go = confirm('order', data=(data, data_stop))
        else:
            go = True
        if go:
            order = self.c.place_order(data)
            order_stop = self.c.place_order(data_stop)
            tell('------ current_position')
            self.current_position = [order, order_stop]
            utils.print_obj(self.current_position, 4)
            return order, order_stop
        return None
        # return self.c.place_order(data) if confirm('order', data=data) else None

    def get_order_status(self, order):
        done = False
        while not done:
            order_status = self.c.get_order(order['clientOrderId'], self.wait * 1000)
            if 'error' in order_status:
                utils.print_obj(order_status, 7)
                tell('error in order_status')
                return order_status
            if not self.silent:
                tell('      order status:')
                utils.print_obj(order_status, 15)
            tell(order_status['side'] + ' ' + order_status['status'])
            if order_status['status'] == 'filled':
                self.orders.append(order_status)
                self.store_order()

            outdated = (datetime.datetime.utcnow()
                        > dateutil.parser.parse(order_status['expireTime']).replace(tzinfo=None))
            if order_status['status'] in ['filled', 'expired'] or outdated:
                done = True
        return order_status

    def take_position(self, side):
        tell('attempting to take a position: ' + str(side))
        next_position = 'abort'
        stop = False # stop trader (error or stop filled, ...)
        position = self.place_order(side=side)
        if position:
            watcher_order = WaitThread(self.get_order_status, position[0])
            watcher_order_stop = WaitThread(self.get_order_status, position[1])
            watcher_order.start()
            watcher_order_stop.start()
            done = False
            watcher_order_done = False
            watcher_order_stop_done = False
            while not done and not stop:
                if watcher_order.done and not watcher_order_done:
                    tell('watcher_order.done')
                    watcher_order.join()
                    watcher_order_done = True
                    utils.print_obj(watcher_order.result, 2)
                    if not 'error' in watcher_order.result:
                        if watcher_order.result['status'] == 'filled':
                            tell('order filled')
                            next_position = side.oposite()
                            self.c.cancel_order(position[1]['clientOrderId'])
                            watcher_order_stop_done = True
                        elif watcher_order.result['status'] == 'expired':
                            tell('order expired')
                            next_position = side
                        else:
                            tell('order status: ' + watcher_order_stop.result['status'])
                    else:
                        tell('error in get stop status')
                        stop = True
                if watcher_order_stop.done and not watcher_order_stop_done:
                    tell('watcher_order_stop.done')
                    watcher_order_stop.join()
                    watcher_order_stop_done = True
                    utils.print_obj(watcher_order_stop.result, 2)
                    if not 'error' in watcher_order_stop.result:
                        if watcher_order_stop.result['status'] == 'filled':
                            tell('stop order filled')
                            stop = True
                        else:
                            tell('stop order status: ' + watcher_order_stop.result['status'])
                    else:
                        tell('error in get stop status')
                        stop = True
                if watcher_order_done and watcher_order_stop_done:
                    tell('both stop order and limit order done')
                    done = True
        return next_position

    def at_exit(self):
        tell('SAFE EXIT')
        self.cancel_orders()
        self.store_order()
        active_orders = self.c.get_orders(self.symbol_code)
        if active_orders:
            tell('# WARNING: {} active order(s)'.format(str(len(active_orders))))
            utils.print_obj(active_orders)
        tell('EXITED SAFELY')

    def start(self):
        nb_positions = 0
        next_position = Side('sell')
        stop = False
        while not stop:
            next_position = self.take_position(next_position)
            if isinstance(next_position, str):
                tell(30 * '=' + ' POSITION RESULT: ' + next_position)
                stop = True
            else:
                nb_positions += 1
            if nb_positions > 10:
                tell('position number target reached')
                stop = True

def main():
    t = Trader(keys, 'DOGEBTC', silent=False, need_confirmation=False)
    atexit.register(t.at_exit)
    t.start()

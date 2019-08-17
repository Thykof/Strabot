"""Trader"""


import json
import atexit
import datetime
import math
from threading import Thread
import sys
import dateutil.parser
from decimal import Decimal


from private import auth as keys
from trabot.client import Client
from trabot import utils
from trabot.utils import tell


# Response
ERROR = 'error'
# JSON boolean
TRUE = 'true'
FALSE = 'flase'
# Order status
FILLED = 'filled'
EXPIRED = 'expired'
CANCELED = 'canceled'
NEW = 'new'
# Side
BUY = 'buy'
SELL = 'sell'
ASK = 'ask'
BID = 'bid'

class Side:
    def __init__(self, side, order=None, spread=None):
        if order:
            assert side in (SELL, BUY)
        elif spread:
            assert side in (ASK, BID)
        else:
            assert side in (SELL, BUY, ASK, BID)

        self.s = side

    def __str__(self):
        return self.s

    def oposite(self):
        if self.s == BUY:
            return Side(SELL)
        if self.s == SELL:
            return Side(BUY)
        if self.s == ASK:
            return Side(BID)
        if self.s == BID:
            return Side(ASK)
        raise ValueError('invalid side')

    def to_spread(self):
        if self.s == BUY:
            return Side(BID)
        if self.s == SELL:
            return Side(ASK)
        raise ValueError('invalid side')

    def to_order(self):
        if self.s == BID:
            return Side(BUY)
        if self.s == ASK:
            return Side(SELL)
        raise ValueError('invalid side')

    def switch(self):
        if self.s == BUY:
            return Side(ASK)
        if self.s == SELL:
            return Side(BID)
        if self.s == ASK:
            return Side(BUY)
        if self.s == BID:
            return Side(SELL)
        raise ValueError('invalid side')


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

def validate_price(symbol, price):
    if math.modf(price / symbol['tickSize'])[0] != 0:
        raise ValueError('price should be divided by tickSize without residue')

def validate_quantity(symbol, quantity):
    if math.modf(quantity / symbol['quantityIncrement'])[0] != 0:
        raise ValueError('quantity should be divided by quantityIncrement without residue')

def validate_stop_price(stop_price, price, side):
    tell(str(side))
    if str(side) not in [BUY, SELL]:
        tell(str(side))
        raise TraderError('invalid side')
    if str(side) == BUY and stop_price >= price or str(side) == SELL and stop_price <= price:
        raise TraderError('invalide stop price: stop: {}, limit: {}'.format(str(stop_price), str(price)))


class TraderError(Exception):
    pass

class Trader:
    def __init__(self, auth, symbol_code, silent=True, expire_time=None, wait=None, need_confirmation=True):
        self.c = Client("https://api.hitbtc.com", auth[0], auth[1])
        self.symbol_code = symbol_code
        self.silent = silent
        self.symbol = self.c.get_symbol(self.symbol_code)
        self.symbol['quantityIncrement'] = Decimal(self.symbol['quantityIncrement'])
        self.symbol['tickSize'] = Decimal(self.symbol['tickSize'])
        self.symbol['takeLiquidityRate'] = Decimal(self.symbol['takeLiquidityRate'])
        self.symbol['provideLiquidityRate'] = Decimal(self.symbol['provideLiquidityRate'])
        self.price_range = 10
        self.trade_price = self.price_range * self.symbol['tickSize']
        self.relative_quantity = 1
        self.trade_quantity = (self.relative_quantity
            * Decimal(self.symbol['quantityIncrement']))
        self.security_level = 4
        self.price_depth = 1
        self.expire_time = expire_time or 60
        self.wait = wait or 20
        self.n_target = 10
        self.orders = list()
        # self.orders_stop = list()
        self.current_position = None # position order
        self.current_stop = None # stop loss order
        self.need_confirmation = need_confirmation
        self.current_side = None
        self.watcher_stop = None
        self.watcher_order = None
        self.n = 0

    #### Setters
    def set_price_range(self, price_range):
        self.price_range = price_range
        self.trade_price = self.price_range * self.symbol['tickSize']

    #### Helpers
    def get_min_past_trade(self):
        trades = self.c.get_trades_public(self.symbol_code)
        if not self.silent:
            utils.print_obj(trades, 10)
        min_price = trades[0]['price']
        for trade in trades:
            if min_price > trade['price']:
                min_price = trade['price']
        return Decimal(min_price)

    def get_price_from_orderbook(self, side, limit):
        tell('get_price_from_orderbook ' + str(side))
        orderbook = self.c.get_orderbook(self.symbol_code, limit)
        if not self.silent:
            utils.print_obj(orderbook, 10, True)
        price = Decimal(orderbook[str(side)][-1]['price'])
        print(price, self.symbol['tickSize'])
        if str(side) == BID:
            price += self.symbol['tickSize']
        elif str(side) == ASK:
            price -= self.symbol['tickSize']
        else:
            raise TraderError('invalid side')
        return price

    #### Hitsory
    def store_order(self):
        with open('data/orders.json', 'w+') as json_file:
            content = json_file.read()
            if content:
                orders = json.loads(content)
            else:
                orders = []
            orders.extend(self.current_position)
            orders.extend(self.current_stop)
            orders.extend(self.orders)
            json.dump(orders, json_file, indent=2)

    #### Order handling
    def cancel_orders(self):
        if (self.current_position and
            self.current_position['status'] not in [FILLED, EXPIRED, CANCELED]):
            response = self.c.cancel_order(self.current_position['clientOrderId'])
            if not self.silent:
                utils.print_obj(response, 10)
        if (self.current_stop and
            self.current_stop['status'] not in [FILLED, EXPIRED, CANCELED]):
            response = self.c.cancel_order(self.current_stop['clientOrderId'])
            if not self.silent:
                utils.print_obj(response, 10)

    def place_stop_order(self, stop_price, side):
        """price is not the stop price, it's the price of the position."""
        validate_stop_price(stop_price, Decimal(self.current_position['price']), side)
        validate_quantity(self.symbol, self.trade_quantity)
        validate_price(self.symbol, stop_price)
        data_stop = {
            'symbol': self.symbol_code,
            'side': str(side.oposite()),
            'quantity': self.trade_quantity,
            'type': 'stopLimit',
            'price': stop_price,
            'stopPrice': stop_price,
            'timeInForce': 'GTD',
            'expireTime': get_now_plus(seconds=self.expire_time),
            'strictValidate': TRUE,
            'postOnly': TRUE
        }
        if self.need_confirmation:
            go = confirm('order', data=data_stop)
        else:
            go = True
        if go:
            tell(data_stop, 0, True)
            order_stop = self.c.place_order(data_stop)
            self.current_stop = order_stop
            tell('------ stop loss order')
            utils.print_obj(self.current_stop, 4)
            self.watcher_stop = Thread(target=self.watch_stop)
            self.watcher_stop.start()
            return order_stop
        return None

    def place_order(self, price, side):
        validate_quantity(self.symbol, self.trade_quantity)
        validate_price(self.symbol, price)
        data = {
            'symbol': self.symbol_code,
            'side': str(side),
            'quantity': self.trade_quantity,
            'type': 'limit',
            'price': price,
            'timeInForce': 'GTD',
            'expireTime': get_now_plus(seconds=self.expire_time),
            'strictValidate': TRUE,
            'postOnly': TRUE
        }

        if self.need_confirmation:
            go = confirm('order', data=data)
        else:
            go = True
        if go:
            tell(data, 0, True)
            order = self.c.place_order(data)
            self.current_position = order
            tell('------ current_position')
            utils.print_obj(self.current_position, 4)
            self.watcher_order = Thread(target=self.watch_order)
            self.watcher_order.start()
            return order
        return None

    #### Watchers
    def get_order_status(self, order):
        """Blocking methods as its call get_order with `wait` parameter."""
        while True:
            order_status = self.c.get_order(order['clientOrderId'], self.wait * 1000)
            # tell('-------- order_status ---------------')
            # tell(order_status)
            # tell('-------------------------------------')
            if ERROR in order_status:
                if order_status[ERROR]['code'] == 20002 and order_status[ERROR]['message'] == 'Order not found':
                    tell('WARNING: order not found')
                    return order_status
                utils.print_obj(order_status, 7)
                tell('error in order_status')
                raise TraderError('error in get_order_status in watch_position')
            if not self.silent:
                tell('      order status:')
                utils.print_obj(order_status, 15)
            tell(order_status['side'] + ' ' + order_status['status'])
            outdated = (datetime.datetime.utcnow()
                > dateutil.parser.parse(order_status['expireTime']).replace(tzinfo=None))
            if order_status['status'] in [FILLED, EXPIRED] or outdated:
                return order_status

    def watch_order(self):
        while True:
            current_position = self.get_order_status(self.current_position)
            if not ERROR in current_position:
                if current_position['status'] == FILLED:
                    self.on_order_filled(current_position)
                    break
                elif current_position['status'] == EXPIRED:
                    self.on_order_expired(current_position)
                    break
                elif current_position['status'] != NEW:
                    raise ValueError("order status should be 'new', 'filled' or 'expired'")

    def watch_stop(self):
        while True:
            current_stop = self.get_order_status(self.current_stop)
            if not ERROR in current_stop:
                if current_stop['status'] == FILLED:
                    self.on_stop_filled(current_stop)
                    break
                elif current_stop['status'] == EXPIRED:
                    self.on_stop_expired(current_stop)
                    break
                elif current_stop['status'] != NEW:
                    raise ValueError("order stop status should be 'new', 'filled' or 'expired'")
            else:
                raise TraderError('error in get_order_status in watch_stop')

    #### Event handlers
    def on_order_filled(self, order):
        # change current_side
        self.orders.append(order)
        self.current_side = self.current_side.oposite()
        # Cancel stop order
        self.current_stop = self.c.cancel_order(self.current_stop['clientOrderId'])
        self.watcher_stop.join() # wait for the thread watcher to finish
        if not self.silent:
            tell('------ canceled stop')
            utils.print_obj(self.current_stop)
        if not ERROR in self.current_stop:
            assert self.current_stop['status'] == CANCELED # TODO: do this elsewhere (a methods?)

        self.take_position()

    def on_order_expired(self, order):
        # Stop order has also expired
        # Keep the same current_side
        self.watcher_stop.join() # wait for the thread watcher to finish
        self.take_position()

    def on_stop_filled(self, order):
        # Several possible decisions
        # 1. exit
        # 2. continue to the oposite side
        # 3. analyse the trend line and choose a side
        self.orders.append(order)
        tell('Stop loss filled, exit')
        self.watcher_order.join()
        sys.exit()

    def on_stop_expired(self, order):
        # Position order has also expired
        tell('Stop loss exipred')
        # self.watcher_order.join()

    #### Positions
    def take_position(self):
        tell('take_position')
        if self.n > self.n_target:
            tell('position number target reached')
        else:
            # Get the stop price
            #
            if self.current_stop and self.current_stop['side'] == str(self.current_side.oposite()): # TODO: or current_stop side != self.current_side...
                stop_price = self.raise_stop()
            else:
                stop_price = self.get_price_from_orderbook(
                    self.current_side.to_spread(),
                    self.price_depth + self.security_level
                )
            # Get the limit price
            price = self.get_price_from_orderbook(self.current_side.to_spread(), self.price_depth)

            self.n += 1
            self.place_order(price, self.current_side)
            self.place_stop_order(stop_price, self.current_side)

    def raise_stop(self):
        tell('raise_stop')
        # Raise stop price if possible (take profit)
        if str(self.current_side) == BUY:
            select_func = max
        elif str(self.current_side) == SELL:
            select_func = min
        else:
            raise ValueError("side should be 'buy' or 'sell'")

        # if self.current_stop[CANCELED]:
        # Keep the same stop price as before if the new potential stop price
        # is bellow the previous stop price
        stop_price = select_func(
            self.get_price_from_orderbook(
                self.current_side.to_spread(),
                self.price_depth + self.security_level
            ),
            Decimal(self.current_stop['price'])
        )
        return stop_price

    def start(self, side):
        self.current_side = side
        self.take_position()

    def at_exit(self):
        tell('SAFE EXIT')
        self.cancel_orders()
        self.store_order()
        active_orders = self.c.get_orders(self.symbol_code)
        if active_orders:
            tell('##############################################')
            tell('WARNING: {} active order(s)'.format(str(len(active_orders))))
            utils.print_obj(active_orders)
        tell('EXITED SAFELY')

def main():
    t = Trader(keys, 'DOGEBTC', silent=False, need_confirmation=False)
    atexit.register(t.at_exit)
    t.start(Side(BUY))

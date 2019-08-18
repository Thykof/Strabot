"""Trader"""


import time
import datetime
from threading import Thread, active_count
from decimal import Decimal
import dateutil.parser


from trabot.client import Client
from trabot import utils
from trabot.utils import log
from trabot import validators
from trabot import data as d
from trabot.exception import TraderError


class Trader:
    def __init__(self,
            auth,
            symbol_code,
            silent=True,
            expire_time=None,
            wait=None,
            need_confirmation=True,
            min_margin=None
        ):
        self.auth = auth
        self.connect()
        self.symbol_code = symbol_code
        self.silent = silent
        self.symbol = self.c.get_symbol(self.symbol_code)
        self.symbol['quantityIncrement'] = Decimal(
            self.symbol['quantityIncrement'])
        self.symbol['tickSize'] = Decimal(self.symbol['tickSize'])
        self.symbol['takeLiquidityRate'] = Decimal(
            self.symbol['takeLiquidityRate'])
        self.symbol['provideLiquidityRate'] = Decimal(
            self.symbol['provideLiquidityRate'])
        self.price_range = 10
        self.trade_price = self.price_range * self.symbol['tickSize']
        self.relative_quantity = 1
        self.trade_quantity = (self.relative_quantity
                               * Decimal(self.symbol['quantityIncrement']))
        self.security_level = 8
        self.price_depth = 1  # 2
        self.expire_time = expire_time or 60
        self.wait = wait or 20
        self.min_margin = min_margin or 1
        self.n_target = 30
        self.orders = list()
        # self.orders_stop = list()
        self.current_position = None # position order
        self.current_stop = None # stop loss order
        self.need_confirmation = need_confirmation
        self.current_side = None
        self.watcher_stop = None
        self.watcher_order = None
        self.n = 0

    def connect(self):
        self.c = Client("https://api.hitbtc.com", self.auth[0], self.auth[1])


    #### Setters
    def set_price_range(self, price_range):
        self.price_range = price_range
        self.trade_price = self.price_range * self.symbol['tickSize']


    #### Helpers
    def get_min_past_trade(self):
        trades = self.c.get_trades_public(self.symbol_code)
        if not self.silent:
            log(trades, 10)
        min_price = trades[0]['price']
        for trade in trades:
            if min_price > trade['price']:
                min_price = trade['price']
        return Decimal(min_price)

    def get_price_from_orderbook(self, side, limit):
        log('get_price_from_orderbook ' + str(side))
        orderbook = self.c.get_orderbook(self.symbol_code, limit)
        if not self.silent:
            log(orderbook, 10, True)
        price = Decimal(orderbook[str(side)][-1]['price'])
        # if str(side) == d.BID:
        #     price += self.symbol['tickSize']
        # elif str(side) == d.ASK:
        #     price -= self.symbol['tickSize']
        # else:
        #     raise TraderError('invalid side')
        return price

    def get_stop_price(self, side=None):
        if not side:
            side = self.current_side
        # Raise stop price if possible (take profit)
        stop_price = self.get_price_from_orderbook(
            side.to_spread(),
            self.price_depth + self.security_level
        )
        log('stop price from orderbook ' + str(stop_price))
        if self.current_stop and d.ERROR not in self.current_stop:
            log('current stop price ' + self.current_stop['price'])
        if self.current_position and d.ERROR not in self.current_position:
            log('current position price ' + self.current_position['price'])
            log('current position side ' + self.current_position['side'])
        log('current side ' + str(side))
        if self.current_stop and not d.ERROR in self.current_stop:
            return Decimal(self.current_stop['price'])
        return stop_price
        # return stop_price

    def push_order(self, order):
        order['tradesReport'][0]['quantity'] = Decimal(
            order['tradesReport'][0]['quantity'])
        order['tradesReport'][0]['price'] = Decimal(order['tradesReport'][0]['price'])
        order['tradesReport'][0]['fee'] = Decimal(order['tradesReport'][0]['fee'])
        self.orders.append(order)


    #### Order
    def cancel_orders(self):
        STATES = [d.FILLED, d.EXPIRED, d.CANCELED]
        if (self.current_position and d.ERROR not in self.current_position and
                self.current_position['status'] not in STATES):
            log('canceling position')
            response = self.c.cancel_order(
                self.current_position['clientOrderId'])
            if not self.silent:
                log(response, 10)
        if (self.current_stop and d.ERROR not in self.current_stop and
                self.current_stop['status'] not in STATES):
            log('canceling stop')
            response = self.c.cancel_order(self.current_stop['clientOrderId'])
            if not self.silent:
                log(response, 10)

    def place_stop_order(self, stop_price, side):
        """price is not the stop price, it's the price of the position."""
        validators.validate_stop_price(
            stop_price, Decimal(self.current_position['price']), side)
        validators.validate_quantity(self.symbol, self.trade_quantity)
        validators.validate_price(self.symbol, stop_price)
        data_stop = {
            'symbol': self.symbol_code,
            'side': str(side.oposite()),
            'quantity': self.trade_quantity,
            'type': 'stopLimit',
            'price': stop_price,
            'stopPrice': stop_price,
            'timeInForce': 'GTC',
            'strictValidate': d.TRUE,
            'postOnly': d.TRUE
        }
        if self.need_confirmation:
            go = utils.confirm('order', data=data_stop)
        else:
            go = True
        if go:
            log(data_stop, 0, True)
            order = self.c.place_order(data_stop)
            if not d.ERROR in order:
                self.current_stop = order
                log('------ stop loss order')
                log(self.current_stop, 4)
                if order['status'] != d.SUSPENDED:
                    log('Strange stop order status: ' + order['status'])
                    if utils.confirm('retry', data=data_stop):
                        time.sleep(self.wait)
                        self.connect()
                        return self.place_stop_order(stop_price, side)
                self.watcher_stop = Thread(target=self.watch_stop)
                self.watcher_stop.start()
            return order
        return None

    def place_order(self, price, side):
        validators.validate_quantity(self.symbol, self.trade_quantity)
        validators.validate_price(self.symbol, price)
        data = {
            'symbol': self.symbol_code,
            'side': str(side),
            'quantity': self.trade_quantity,
            'type': 'limit',
            'price': price,
            'timeInForce': 'GTD',
            'expireTime': utils.get_now_plus(seconds=self.expire_time),
            'strictValidate': d.TRUE,
            'postOnly': d.TRUE
        }

        if self.need_confirmation:
            go = utils.confirm('order', data=data)
        else:
            go = True
        if go:
            log(data, 0, True)
            order = self.c.place_order(data)
            if not d.ERROR in order:
                self.current_position = order
                log('------ current_position')
                log(self.current_position, 4)
                if order['status'] != d.NEW:
                    log('Strange order status: ' + order['status'])
                    if utils.confirm('retry', data=data):
                        time.sleep(self.wait)
                        self.connect()
                        return self.place_order(price, side)
                self.watcher_order = Thread(target=self.watch_order)
                self.watcher_order.start()
            return order
        return None


    #### Watchers
    def get_order_status(self, order):
        """Blocking methods as its call get_order with `wait` parameter."""
        while True:
            order_status = self.c.get_order(
                order['clientOrderId'], self.wait * 1000)
            if d.ERROR in order_status:
                if (order_status[d.ERROR]['code'] == 20002 and
                        order_status[d.ERROR]['message'] == 'Order not found'):
                    log('WARNING: order not found ' + order['clientOrderId'])
                    return order_status
                log(order_status, 7)
                log('error in order_status')
                raise TraderError('error in get_order_status in watch_position')
            if not self.silent:
                log('      order status:')
                log(order_status, 15)
            log(order_status['side'] + ' ' + order_status['status'])
            if d.STOP not in order_status['type']:
                expire_time = dateutil.parser.parse(
                    order_status['expireTime']).replace(tzinfo=None)
                outdated = (datetime.datetime.utcnow()
                            > expire_time)
            else:
                outdated = False  # Stop order never expire
            if order_status['status'] in [d.FILLED, d.EXPIRED] or outdated:
                return order_status

    def watch_order(self):
        while True:
            if self.current_position['status'] != d.CANCELED:
                current_position = self.get_order_status(self.current_position)
                if not d.ERROR in current_position:
                    if current_position['status'] == d.FILLED:
                        self.on_order_filled(current_position)
                        break
                    elif current_position['status'] == d.EXPIRED:
                        self.on_order_expired(current_position)
                        break
                    elif current_position['status'] != d.NEW:
                        msg = "order status should be 'new', 'filled' or 'expired'"
                        raise TraderError(msg)
                else:
                    if (current_position[d.ERROR]['message'] == 'Order not found'
                            and current_position[d.ERROR]['code'] == 20002):
                        log('watched limit order not found, exit watcher')
                        break
            else:
                log('attempting to watch a stop canceled order')
                break

    def watch_stop(self):
        while True:
            if self.current_stop['status'] != d.CANCELED:
                current_stop = self.get_order_status(self.current_stop)
                if not d.ERROR in current_stop:
                    if current_stop['status'] == d.FILLED:
                        self.on_stop_filled(current_stop)
                        break
                    elif current_stop['status'] != d.NEW:
                        msg = "order stop status should be 'new', 'filled' or 'expired'"
                        raise TraderError(msg)
                else:
                    if (current_stop[d.ERROR]['message'] == 'Order not found'
                            and current_stop[d.ERROR]['code'] == 20002):
                        log('watched stop order not found, exit watcher')
                        break
            else:
                log('attempting to watch a stop canceled order')
                break


    #### Event handlers
    def on_order_filled(self, order):
        self.push_order(order)
        # Cancel stop order
        if self.current_stop:
            self.current_stop = self.c.cancel_order(
                self.current_stop['clientOrderId'])
            if not self.silent:
                log('------ canceled stop')
                log(self.current_stop)
            if not d.ERROR in self.current_stop:
                assert self.current_stop['status'] == d.CANCELED
                # TODO: do this elsewhere (a methods?)

        # Get the stop price
        stop_price = self.get_stop_price()
        self.place_stop_order(stop_price, self.current_side)

        # Switch position side
        self.current_side = self.current_side.oposite()
        self.take_position()

    def on_order_expired(self, order):
        # Keep the same current_side
        log('limit order expired')
        # re take position is the same side
        self.take_position()
        # TODO: look at prices for possible take profit order: move current stop

    def on_stop_filled(self, order):
        # Continue to the oposite side
        self.push_order(order)
        log('Stop loss filled')
        self.current_side = self.current_side.oposite()
        self.take_position()


    #### Positions
    def take_position(self):
        """"""
        log('take_position ' + str(self.current_side))
        if self.n > self.n_target:
            log('position number target reached')
        else:
            price = self.get_price_from_orderbook(
                self.current_side.to_spread(), self.price_depth)
            if self.orders:
                previous_order = self.orders[-1]
                price = utils.get_profitable_price(
                    previous_order, price, self.current_side, self.min_margin,
                    self.symbol)
            self.n += 1
            self.place_order(price, self.current_side)
            log('number of active threads:' + str(active_count()))


    def start(self, side):
        self.current_side = side
        self.take_position()

    def at_exit(self):
        log('SAFE EXIT')
        self.cancel_orders()
        utils.store_order(self.current_position, self.current_stop, self.orders)
        active_orders = self.c.get_orders(self.symbol_code)
        if active_orders:
            log('##############################################')
            log('WARNING: {} active order(s)'.format(str(len(active_orders))))
            log(active_orders)
        log('EXITED SAFELY')

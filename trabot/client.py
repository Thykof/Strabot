# Inspired by https://github.com/hitbtc-com/hitbtc-api/blob/master/example_rest.py
import uuid
import time
import requests

from trabot import utils

class Client(object):
    def __init__(self, url, public_key, secret):
        self.url = url + "/api/2"
        self.session = requests.session()
        self.session.auth = (public_key, secret)

    def log(self, msg):
        utils.log(msg, 'client.log')

    def __str__(self):
        return 'Client, url: ' + self.url

    def get_symbol(self, symbol_code):  # symbol_code: ETHBTC
        """Get symbol."""
        response = self.session.get("%s/public/symbol/%s" % (self.url, symbol_code))
        print(response)
        # self.log(response)
        return response.json() # TODO: log evrywhere

    def get_orderbook(self, symbol_code, limit=1):
        """Get orderbook. """
        return self.session.get(
            "%s/public/orderbook/%s%s" % (self.url, symbol_code, '?limit=' + str(limit))
        ).json()

    def get_trades_public(self, symbol_code, limit=10, sort='DESC'):
        query = 'limit={}&sort={}'.format(str(limit), sort)
        return self.session.get(
            "{}/public/trades/{}?{}".format(
                self.url,
                symbol_code,
                query
            )).json()

    def get_address(self, currency_code):
        """Get address for deposit."""
        return self.session.get("%s/account/crypto/address/%s" % (self.url, currency_code)).json()

    def get_account_balance(self):
        """Get main balance."""
        return self.session.get("%s/account/balance" % self.url).json()

    def get_trading_balance(self):
        """Get trading balance."""
        return self.session.get("%s/trading/balance" % self.url).json()

    def transfer(self, currency_code, amount, to_exchange):
        return self.session.post("%s/account/transfer" % self.url, data={
            'currency': currency_code, 'amount': amount,
            'type': 'bankToExchange' if to_exchange else 'exchangeToBank'
            }).json()

    def place_order(self, data):
        return self.session.post('{}/order'.format(self.url), data=data).json()

    def new_order(self, client_order_id, symbol_code, side, quantity, price=None):
        """Place an order."""
        data = {'symbol': symbol_code, 'side': side, 'quantity': quantity}

        if price is not None:
            data['price'] = price

        data['timeInForce'] = 'IOC'

        return self.session.put("%s/order/%s" % (self.url, client_order_id), data=data).json()

    def open_order(self, quantity, price):
        assert 0
        client_order_id = uuid.uuid4().hex
        order = self.new_order(client_order_id, 'ETHBTC', 'buy', quantity, price)
        if 'error' not in order:
            if order['status'] == 'filled':
                print("Order filled", order)
            elif order['status'] == 'new' or order['status'] == 'partiallyFilled':
                print("Waiting order...")
                for _ in range(0, 4):  # 1 min
                    order = self.get_order(client_order_id, 15000)
                    print(order)

                    if 'error' in order:
                        print(order['error'])
                        break
                    elif order['status'] == 'filled':
                        print('filled')
                        break

                # cancel order if it isn't filled
                if 'status' in order and order['status'] != 'filled':
                    cancel = self.cancel_order(client_order_id)
                    print('Cancel order result', cancel)
                    # open buy order with highter price
        else:
            print(order['error'])

    def get_order(self, client_order_id, wait=None):
        """Get order info."""
        data = {'wait': wait} if wait is not None else {}
        return self.session.get("%s/order/%s" % (self.url, client_order_id), params=data).json()

    def get_orders(self, symbol_code=None):
        """Get all orders info."""
        data = {'symbol': symbol_code} if symbol_code is not None else {}
        return self.session.get("%s/order/" % (self.url), params=data).json()

    def cancel_order(self, client_order_id):
        """Cancel order."""
        return self.session.delete("%s/order/%s" % (self.url, client_order_id)).json()

    def withdraw(self, currency_code, amount, address, network_fee=None):
        """Withdraw."""
        data = {'currency': currency_code, 'amount': amount, 'address': address}

        if network_fee is not None:
            data['networkfee'] = network_fee

        return self.session.post("%s/account/crypto/withdraw" % self.url, data=data).json()

    def get_transaction(self, transaction_id):
        """Get transaction info."""
        return self.session.get("%s/account/transactions/%s" % (self.url, transaction_id)).json()

    def get_trade(self, clientOrderId=None, id=None):
        trades = self.session.get("{}/history/trades".format(self.url)).json()
        if 'error' not in trades:
            for trade in trades:
                if clientOrderId is not None:
                    if trade['clientOrderId'] == clientOrderId:
                        return trade
                if id is not None:
                    if int(trade['id']) == id:
                        return trade
        else:
            return trades

    def calculate_profit(self, trade1_id, trade2_id):
        """calculate profit in BTC, for two trades of same quantity, long side."""
        trade1 = self.get_trade(id=trade1_id)
        trade2 = self.get_trade(id=trade2_id)
        if 'error' not in trade1 and 'error' not in trade2:
            fees = float(trade1['fee']) + float(trade2['fee'])
            sell_price = float(trade2['price'])
            buy_price = float(trade1['price'])
            profit = (float(trade2['quantity']) * sell_price) - (float(trade1['quantity']) * buy_price) - fees
            return round(profit, 9)
        return 'error'

    def estimate_profit(self, symbol, quantity, sell, buy, side='long', type_='tm'):
        # quantity in quote currency
        if 'error' not in symbol:
            if type_ == 'tm':
                #fees = fee_taker + fee_maker
                fees = utils.trunc(quantity * float(symbol['takeLiquidityRate']), 9)
                fees += utils.trunc(quantity * float(symbol['provideLiquidityRate']), 9)
            elif type_ == 'mm':
                #fees = 2 * fee_maker
                fees = utils.trunc(quantity * float(symbol['provideLiquidityRate']), 9)
                fees += utils.trunc(quantity * float(symbol['provideLiquidityRate']), 9)
            elif type_ == 'tt':
                #fees = 2 * fee_taker
                fees = utils.trunc(quantity * float(symbol['takeLiquidityRate']), 9)
                fees += utils.trunc(quantity * float(symbol['takeLiquidityRate']), 9)

            fees = utils.trunc(fees, 9)
            if side == 'long':
                profit = float(quantity * ((sell / buy) -1 ))
            elif side == 'short':
                profit = float(quantity * ((buy / sell) -1 ))
            earn = float(profit - fees)

            return earn, round(profit, 9), fees

        return 'error'

    def wait_for_price(self, symbol_code, price, side='long', wait=5):
        stop = False
        while not stop:
            time.sleep(wait)
            orderbook = self.get_orderbook(symbol_code)
            if side == 'long':
                if float(orderbook['ask'][0]['price']) <= price:
                    stop = True
                    print('best ask: ' + str(orderbook['ask'][0]))
            elif side == 'short':
                if float(orderbook['bid'][0]['price']) >= price:
                    stop = True
                    print('best bid: ' + str(orderbook['ask'][0]))

    def find_profitable_price(self, symbol, price, quantity, side='sell', productivity=2):
        side = 'long' if side == 'sell' else 'short'
        profit = 0
        profit_price = price
        fees = 0
        while profit <= (productivity * fees):
            profit_price += float(symbol['tickSize'])
            earn, profit, fees = self.estimate_profit(symbol, quantity, profit_price, price, side)
        return round(profit_price, 9), profit

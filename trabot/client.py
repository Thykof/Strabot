# Inspired by https://github.com/hitbtc-com/hitbtc-api/blob/master/example_rest.py
import requests


class Client:
    def __init__(self, url, public_key, secret):
        self.url = url + "/api/2"
        self.session = requests.session()
        self.session.auth = (public_key, secret)

    def __str__(self):
        return 'Client, url: ' + self.url

    def get_symbol(self, symbol_code):  # symbol_code: ETHBTC
        """Get symbol."""
        return self.session.get("%s/public/symbol/%s" % (self.url, symbol_code)).json()

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

    def get_trade(self, client_order_id=None, id=None):
        trades = self.session.get("{}/history/trades".format(self.url)).json()
        if 'error' not in trades:
            for trade in trades:
                if client_order_id is not None:
                    if trade['clientOrderId'] == client_order_id:
                        return trade
                if id is not None:
                    if int(trade['id']) == id:
                        return trade
        return trades

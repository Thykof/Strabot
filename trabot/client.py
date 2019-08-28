# Inspired by https://github.com/hitbtc-com/hitbtc-api/blob/master/example_rest.py
import requests


from trabot.helpers import log


error_count = 0


def get_error(status_code):
    return {'error': {
        'code': status_code
    }}


def request_wrapper(func):
    global error_count

    def wrapper(self, *args, **kargs):
        global error_count
        resp = func(self, *args, **kargs)
        if resp.status_code != 200 and resp.status_code != 400:
            log(['request error', resp.status_code, resp, resp.text])
            error_count += 1
            if error_count < 5:
                return wrapper(self, *args, **kargs)
            return get_error(resp.status_code)
        try:
            j = resp.json()
        except ValueError as err:
            log(['get_symbol', err, resp, resp.text])
            error_count += 1
            if error_count < 5:
                return wrapper(self, *args, **kargs)
            return get_error(resp.status_code)
        else:
            error_count = 0
            return j
    return wrapper


class Client:
    def __init__(self, url, public_key, secret, max_error=None):
        self.url = url + "/api/2"
        self.session = requests.session()
        self.session.auth = (public_key, secret)
        # self.error_count = 0
        # self.max_error = max_error or 5

    def __str__(self):
        return 'Client, url: ' + self.url

    @request_wrapper
    def get_symbol(self, symbol_code):  # symbol_code: ETHBTC
        """Get symbol."""
        return self.session.get(
            "{}/public/symbol/{}".format(self.url, symbol_code))

    @request_wrapper
    def get_orderbook(self, symbol_code, limit=1):
        """Get orderbook. """
        url = "{}/public/orderbook/{}{}".format(
            self.url, symbol_code, '?limit=' + str(limit))
        return self.session.get(url)

    @request_wrapper
    def get_trades_public(self, symbol_code, limit=10, sort='DESC'):
        query = 'limit={}&sort={}'.format(str(limit), sort)
        return self.session.get(
            "{}/public/trades/{}?{}".format(self.url, symbol_code, query))

    @request_wrapper
    def get_address(self, currency_code):
        """Get address for deposit."""
        return self.session.get(
            "{}/account/crypto/address/{}".format(self.url, currency_code))

    @request_wrapper
    def get_account_balance(self):
        """Get main balance."""
        return self.session.get("{}/account/balance".format(self.url))

    @request_wrapper
    def get_trading_balance(self):
        """Get trading balance."""
        return self.session.get("{}/trading/balance".format(self.url))

    @request_wrapper
    def transfer(self, currency_code, amount, to_exchange):
        return self.session.post("{}/account/transfer".format(self.url, data={
            'currency': currency_code, 'amount': amount,
            'type': 'bankToExchange' if to_exchange else 'exchangeToBank'
        }))

    @request_wrapper
    def place_order(self, data):
        return self.session.post('{}/order'.format(self.url), data=data)

    @request_wrapper
    def get_order(self, client_order_id, wait=None):
        """Get order info."""
        data = {'wait': wait} if wait is not None else {}
        return self.session.get(
            "{}/order/{}".format(self.url, client_order_id), params=data)

    @request_wrapper
    def get_orders(self, symbol_code=None):
        """Get all orders info."""
        data = {'symbol': symbol_code} if symbol_code is not None else {}
        return self.session.get("{}/order/".format((self.url), params=data))

    @request_wrapper
    def cancel_order(self, client_order_id):
        """Cancel order."""
        return self.session.delete(
            "{}/order/{}".format(self.url, client_order_id))

    @request_wrapper
    def withdraw(self, currency_code, amount, address, network_fee=None):
        """Withdraw."""
        data = {'currency': currency_code, 'amount': amount, 'address': address}

        if network_fee is not None:
            data['networkfee'] = network_fee

        return self.session.post(
            "{}/account/crypto/withdraw".format(self.url), data=data)

    @request_wrapper
    def get_transaction(self, transaction_id):
        """Get transaction info."""
        return self.session.get(
            "{}/account/transactions/{}".format(self.url, transaction_id))

    def get_trade(self, client_order_id=None, id_=None):
        """id_ is int"""
        resp = self.session.get("{}/history/trades".format(self.url))
        if resp.status_code != 200:
            return get_error(resp.status_code)
        try:
            trades = resp.json()
        except ValueError as err:
            log(['get_transaction', err, resp])
            return 'error'
        if 'error' not in trades:
            for trade in trades:
                if client_order_id is not None:
                    if trade['clientOrderId'] == client_order_id:
                        return trade
                if id_ is not None:
                    if int(trade['id']) == id_:
                        return trade
        return trades

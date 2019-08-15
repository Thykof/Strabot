from os import path


from private import auth
from trabot.client import Client


class BaseTestMod(object):
    def setup_method(self, test_method):
        self.client = Client("https://api.hitbtc.com", auth[0], auth[1])
        self.maid_btc = self.client.get_symbol('MAIDBTC')

class TestClient(BaseTestMod):
    def test_get_trade(self):
        trade = self.client.get_trade(id=220204390)
        assert trade == {'id': 220204390,
        'clientOrderId': 'dca99ba1f94a45949ba5e614dff10c1e',
        'orderId': 19564058759,
        'symbol': 'MANAETH', 'side': 'buy', 'quantity': '2',
        'price': '0.00012', 'fee': '-0.00000002',
        'timestamp': '2018-03-08T03:56:48.011Z'}

    def test_calculate_profit(self):
        client = Client("https://api.hitbtc.com", auth[0], auth[1])
        profit = client.calculate_profit(218085273, 218650747)
        assert profit == 2.56e-07

    def test_estimate_profit(self):
        client = Client("https://api.hitbtc.com", auth[0], auth[1])
        earn, profit, fees = client.estimate_profit(self.maid_btc, 0.00003405,
        0.00003430, 0.00003405, type_='mm')
        print(earn, profit, fees)
        assert profit == 2.5e-07
        assert fees == -6e-09

    def test_find_profitable_price(self):
        client = Client("https://api.hitbtc.com", auth[0], auth[1])
        price, profit = client.find_profitable_price(self.maid_btc, price=0.00003405,
            quantity=1, side='sell', productivity=1)
        print(price, profit)
        assert price == 3.409e-05
        assert profit == 0.001174743

        price, profit = client.find_profitable_price(self.maid_btc, price=0.00003405,
            quantity=1, side='buy', productivity=1)
        print(price, profit)
        assert price == 3.406e-05
        assert profit == 0.002936551

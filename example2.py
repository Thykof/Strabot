import requests


from trabot.client import Client


url_api = 'https://api.hitbtc.com/api/2/'

auth = ('', '')

def tests():
    r = requests.get('https://api.hitbtc.com/api/2/trading/balance', auth=auth)
    # for info in dir(r):
    #     print(info)
    # print()
    infos = r.json()
    print(infos)

    for info in infos:
        if info['currency'] == 'BTC':
            print('\n infos about BTC trading:')
            print(info)
            print('DONE')
        if info['currency'] == 'DSH':
            print('\n infos about DSH trading:')
            print(info)
            print('DONE')

    r = requests.get('https://api.hitbtc.com/api/2/account/balance', auth=auth)
    for info in infos:
        if info['currency'] == 'BTC':
            print('\n infos about BTC account:')
            print(info)
            print('DONE')
        if info['currency'] == 'DSH':
            print('\n infos about DSH account:')
            print(info)
            print('DONE')

    #
    cmd = ""
    while cmd != "exit":
        cmd = input()
        exec(cmd)

def print_obj(dict_, itend=0):
    for key in dict_.keys():
        msg = ' '*itend
        msg += key + ': ' + str(dict_[key])
        print(msg)

    # test
    # print_obj(dict({
    #     'ask': '0.000002',
    #     'bid': '0.000001',
    #     'last': '0.000002',
    #     'open': '0.000002',
    #     'low': '0.000001',
    #     'high': '0.000002',
    #     'volume': '1834280',
    #     'volumeQuote': '1.92012',
    #     'timestamp': '2017-12-31T16:02:42.138Z',
    #     'symbol': 'SISABTC'
    # }))
    # a = input()
    # if a == 'y':
    #     main()
    # else:
    #     print('done')

def main():
    session = requests.session()
    session.auth = ('', '')

    orders = session.get(url_api + 'order').json()
    for order in orders:
        print('ORDER ' + order['symbol'])
        print_obj(order)
        print('TICKER')
        print_obj(session.get(url_api + 'public/ticker/' + order['symbol']).json(), 4)
        print('======')

        if order['symbol'] == 'SISABTC':
            if order['status'] == 'new':
                print('not filled yet')
            elif order['status'] == 'partiallyFilled':
                print('partially filled')
            else:
                print(order['status'])

    # trades = session.get(url_api + 'history/trades').json()
    # for trade in trades:
    #     print_obj(trade)
    #     if order['side'] == 'sell':
    #         print('create new order buy side')
    #     else:
    #         print('create new order sell side')


def get_orders(symbol):
    session = requests.session()
    session.auth = ('', '')

    orders = session.get(url_api + 'order').json()
    for order in orders:
        if order['symbol'] == symbol:
            print('ORDER ' + order['symbol'])
            print_obj(order)
            print('TICKER')
            print_obj(session.get(url_api + 'public/ticker/' + order['symbol']).json(), 4)
            print('======')

def creat_order(session, symbol, side, amount, price):
    data = {
        'symbol': symbol,
        'side': side,
        'quantity': amount,
        'price': price,
        'timeInForce': 'GTC',
        'strictValidate': 'true'
    }
    print('create order data:')
    print(data)
    print('open this order ? (\'yy\' for yes)')
    response = input()
    if response == 'yy':
        response = session.put(url_api + "order", data=data)
        print(response.status_code)
        print(response._content)
        print(response.text)
        if response.status_code == 202:
            json_response = response.json()
            print('open order resuslt: ')
            print_obj(json_response)
    print('DONE create order')
    return response

def open_order():
    session = requests.session()
    session.auth = ('', '')
    symbol = "SCLBTC"
    print_obj(session.get(url_api + 'public/symbol/' + symbol).json())
    balances = session.get(url_api + 'trading/balance').json()
    for balance in balances:
        #if balance['currency'] == symbol[:-3]:
        if balance['currency'] == 'SCL':
            amount = float(balance['available'])
            if amount > 0:
                ticker = session.get(url_api + 'public/ticker/' + symbol).json()
                print_obj(ticker)
                current_price = ticker['last']
                creat_order(session, symbol, 'sell', amount, float(current_price) * 3)
            else:
                print('no funds')

def status():
    session = requests.session()
    session.auth = ('', '')
    response = session.get(url_api + 'trading/balance')
    if response.status_code != 200:
        print(response)
        return
    balances = response.json()

    response = session.get(url_api + 'account/balance')
    if response.status_code != 200:
        print(response)
        return
    account = response.json()

    currencies = list()
    for balance in balances:
        if float(balance['available']) != 0 or float(balance['reserved']) != 0:
            currencies.append(balance)

    print(currencies)
    currencies = list()
    for balance in account:
        if float(balance['available']) != 0 or float(balance['reserved']) != 0:
            currencies.append(balance)
    print(currencies)


    for currency in currencies:
        print(currency['currency'] + " : " + currency['available'] + '   ' + currency['reserved'])

def transfer():
    session = requests.session()
    session.auth = ('', '')

    response = session.get(url_api + 'account/balance')
    if response.status_code != 200:
        print(response)
        return
    account = response.json()
    for balance in account:
        if balance['currency'] == 'BCN':
            amount = balance['available']

    data = {'currency': 'BCN', 'amount': amount, 'type': 'bankToExchange'}
    print(data)
    yes = input('ok ?')
    if yes == 'yy':
        response = session.post(url_api + 'account/transfer', data=data)
        print(response)
        print(response.json())

def get_order():
    session = requests.session()
    session.auth = ('', '')
    b = session.get('https://api.hitbtc.com/api/2/order').json()
    return b


if __name__ == "__main__":
    client = Client("https://api.hitbtc.com", auth[0], auth[1])
    print(client)
    trade = client.get_trade(id=int(220204390))
    print(trade)
    tests()

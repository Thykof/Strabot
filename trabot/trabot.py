import atexit


from trabot.client import Client
from private import auth
from trabot.utils import *
from trabot.stream import *


def algo():
    """Trading bot algorithm.
    It simulate the orders.
    """
    print("Start algo")
    url_api = 'https://api.hitbtc.com/api/2/'
    symbol_code = 'ETHBTC'
    client = Client("https://api.hitbtc.com", auth[0], auth[1])

    stream = HitBTC()
    stream.start()  # start the websocket connection
    time.sleep(0.25)  # Give the socket some time to connect
    # Varaibles:
    orders = dict()
    orders['buy'] = list()
    orders['sell'] = list()
    profit = dict()
    profit['sell'] = list()
    profit['buy'] = list()

    # Algo:
    eth_btc = client.get_symbol(symbol_code)
    nb_dec = len(str(eth_btc['tickSize']).split('.')[1])
    orderbook = client.get_orderbook(symbol_code)
    # calculate average bid:
    bids = list()
    for price in orderbook['bid']:
        bids.append(float(price['price']))
    print(len(bids))
    average_bid = average(bids)

    #buy_price = round(float(orderbook['bid'][0]['price']) - 0.001 * float(orderbook['bid'][0]['price']), nb_dec)
    buy_price = average_bid - 0.001 * average_bid
    tell('best bid: ' + orderbook['bid'][0]['price'])
    tell('buy price: ' + str(buy_price))

    quantity = float(eth_btc['quantityIncrement'])
    quantity_btc = quantity * buy_price
    if quantity_btc > 0.0001:
        tell('quantity too high: ' + str(quantity_btc))

    # BUY
    #client.open_order('buy', buy_price, quantity)
    orders['buy'].append((quantity, buy_price))
    # waiting for the defined buy_price:
    tell('waiting for ' + str(buy_price))
    response = wait_for(stream, buy_price)
    # this simulate that the order get filled
    if 'timeout' in response:
        tell('timeout')
        sys.exit()

    stop = False
    while not stop:
        # SELL
        # define sell_price:
        sell_price, profit_sell = client.find_profitable_price(eth_btc, buy_price, quantity, 'sell')
        earn, profit_buy, fees = client.estimate_profit(eth_btc, quantity, sell_price, buy_price, side='long', type='tt')
        # wait for sell price:
        tell('waiting for ' + str(sell_price))
        wait_for(stream, sell_price, 'ask')

        #client.open_order('sell', sell_price, quantity)
        tell('open sell order')
        orders['sell'].append((quantity, sell_price))

        # BUY
        # define buy_price:
        buy_price, profit_buy = client.find_profitable_price(eth_btc, sell_price, quantity, 'buy')
        # wait for sell price:
        tell('waiting for ' + str(buy_price))
        wait_for(stream, buy_price)
        # sell at buy_price:
        #client.open_order('buy', buy_price, quantity)
        tell('open buy order')
        orders['buy'].append((quantity, buy_price))

        # get trade info
        # calculate profit
        profit['buy'].append(profit_buy)
        profit['sell'].append(profit_sell)
        tell('profit: ' + str(profit_buy + profit_sell))
        tell('buy profit: ' + str(profit_buy))
        tell('sell profit: ' + str(profit_sell))

    #stream.stop()
    atexit.register(goodbye, orders, profit)

    # get orderbook
    # define a price
    # open buy order
    # wait
    # LOOP
    # get current price
    # calculate fee and profit if sell at current price
    # if profitable: open sell order, else: wait

    # get current price
    # calculate fee and profit if buy at current price
    # if profitable: open buy order, else wait

    # if price move to fast: pause

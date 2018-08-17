import time
import queue


from hitbtc import HitBTC


def wait_for(stream, target, timeout=60, side='bid'):
    """Wait for a price (target).
    return type: str
    """
    begin = time.time()
    while True:
        try:
            data = stream.recv()
        except queue.Empty:
            continue
        else:
            tell(data[2][side])
            price = data[2][side]
            if float(price) <= target:
                return price
            elif (time.time() - begin) >= timeout:
                return 'timeout'

def price_average(stream, period=20):
    """Return the average price during the given period.
    Currently not used.
    """
    begin = time.time()
    prices = list()
    while True:
        try:
            data = stream.recv()
        except queue.Empty:
            continue
        else:
            price = data[2][side]
            tell(price)
            prices.append(price)
            if (time.time() - begin) >= period:
                return average(prices)

def demo():
    """Recieve ticker and print results.
    It is the example of https://github.com/Crypto-toolbox/hitbtc"""
    c = HitBTC()
    c.start()  # start the websocket connection
    time.sleep(2)  # Give the socket some time to connect
    c.subscribe_ticker(symbol='ETHBTC') # Subscribe to ticker data for the pair ETHBTC

    while True:
        try:
            data = c.recv()
        except queue.Empty:
            continue
        print(data)
        # process data from websocket
        ...

    c.stop()


# Those following functions are used by fft.py

def get_prices_from_list_tickers(list_tickers):
    """Return a list of (ask) prices."""
    prices = list()
    for ticker in list_tickers:
        prices.append(ticker['ask'])
    return prices

def get_seq(delta=-1, n_seq=-1):
    """Subscribe to ticker, return a list of ask prices from period.
    delta: the period is define by a duration.
    n_seq: the period is define by a number of price.
    """
    stream = HitBTC()
    print('Start connection')
    stream.start()  # start the websocket connection
    time.sleep(0.25)  # Give the socket some time to connect
    # Subscribe to ticker data for the pair ETHBTC:
    print('Subscribe')
    response = stream.subscribe_ticker(symbol='ETHBTC')
    print(response)
    response = stream.recv() # the first value is different
    print(response)

    steps = list()
    time_begin = time.time()
    list_tickers = list()
    n = 0
    while True:
        time_before = time.time()
        try:
            data = stream.recv()
        except queue.Empty:
            continue
        step = time.time() - time_before
        steps.append(step)
        list_tickers.append(data[2])
        print(data[2])
        if(time.time() - time_begin > delta) and delta != -1:
            break
        if n >= n_seq:
            break
        if n_seq != -1:
            n += 1

    stream.stop()

    prices = get_prices_from_list_tickers(list_tickers)
    return steps, prices

def read_seq(filename='data/seq'):
    """Get a seq of price from a file.
    x and y axis.
    """
    seq = list()
    with open(filename) as seq_file:
        seq_str = seq_file.readlines()
    for string in seq_str:
        seq.append(float(string[:-1]))

    steps = list()
    with open(filename+"-x") as seq_file:
        step_str = seq_file.readlines()
    for string in step_str:
        steps.append(float(string[:-1]))

    return steps, seq

def save_seq(seq, steps, filename='data/seq'):
    """Save a seq of prices, x and y axis."""
    with open(filename, 'w') as seq_file:
        for elt in seq:
            seq_file.write(str(elt) + "\n")
    with open(filename+"-x", 'w') as seq_file:
        for elt in steps:
            seq_file.write(str(elt) + "\n")

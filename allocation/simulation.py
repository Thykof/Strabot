import pandas


from utils.utils import raw_data_to_numeric

BTC_PRICES_FILENAME = 'data/prices-btc.txt'

def format_prices_and_save():
    df = pandas.read_csv("predict/bitcoin-price-all-2.csv", sep=',')
    df = df[['Close**']]
    df = df.applymap(raw_data_to_numeric)

    with open(BTC_PRICES_FILENAME, 'w') as mf:
        for index, data in df.iterrows():
            mf.write(str(data[0]) + '\n')

def get_prices():
    prices = list()
    with open(BTC_PRICES_FILENAME) as mf:
        lines = mf.readlines()
    for line in lines:
        prices.append(float(line[:-1]))
    return prices

def get_value(btc, eur, price):
    return round(btc * price + eur, 3)

def global_values(btc, eur):
    prices = get_prices()
    values = list()
    for price in prices:
        values.append(get_value(btc, eur, price))
    return values

def re_allocate():
    pass

def get_distribution(btc, eur, price):
    return round(eur / (btc * price), 5)

def find_amount_to_spend(btc, eur, price, distribution, frequency):
    amount_eur_to_spend = 1
    d = (eur - amount_eur_to_spend)  / (btc * price)
    while d > distribution:
        amount_eur_to_spend += 1
        # print("amount_eur_to_spend", amount_eur_to_spend)
        d = (eur - amount_eur_to_spend)  / (btc * price)
        # print("d", d)
        if d == float(0):
            break
    return amount_eur_to_spend

def find_amount_to_get(btc, eur, price, distribution, frequency):
    amount_eur_to_get = 1
    d = (eur + amount_eur_to_get)  / (btc * price)
    while d < distribution:
        amount_eur_to_get += 1
        # print("amount_eur_to_get", amount_eur_to_get)
        d = (eur + amount_eur_to_get)  / (btc * price)
        # print('d', d)
        if d == float(0):
            break
    return amount_eur_to_get

def simulate(btc, eur, distribution, frequency):
    prices = get_prices()[:1100]
    prices.reverse()
    values = list()
    for n, price in enumerate(prices):
        # print("price", price)
        if n % frequency == 0:
            d = get_distribution(btc, eur, price)
            # print("d 73", d)
            if d > distribution:
                # buy some btc
                amount_eur_to_spend = find_amount_to_spend(btc, eur, price, distribution, frequency)
                eur -= amount_eur_to_spend
                btc += amount_eur_to_spend / price
                # print(f'buy for {amount_eur_to_spend} eur')
            else:
                # sell some btc
                amount_eur_to_get = find_amount_to_get(btc, eur, price, distribution, frequency)
                eur += amount_eur_to_get
                btc -= amount_eur_to_get / price
                # print(f'sell for {amount_eur_to_get} eur')
            value = get_value(btc, eur, price)
            # print(f'distribution: eur: {eur} ; btc: {btc} | value: {value}')
            values.append(value)
            # input()
    return values

if __name__ == '__main__':
    # r = global_values(0.046, 20)
    # r = simulate(0.04645, 20.22, 0.036, 2)
    # for r_ in r:
    #     print(r_)

    for i in range(1, 60):
        r = simulate(0.04645, 20.22, 0.036, i)
        print(i, str(r[-1]).replace(".", ","))

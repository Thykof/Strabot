import csv
import json


amount_BTC = 0
amount_ETH = 0
amount_DOGE = 0

PRICE = dict()
# PRICE['XXBTZEUR'] = 1
# PRICE['XETHZEUR'] = 1
# PRICE['XXDGXXBT'] = 1


def divide(a, b):
    if b != 0:
        return a / b
    return 0


def read_csv(filename='trades.csv'):
    csv_file = open(filename, newline='')

    content = csv.DictReader(csv_file)

    trades = list()

    for trade in content:
        trades.append(trade)

    with open('data/trades.json', 'w') as json_file:
        json.dump(trades, json_file, indent=2)

    print(len(trades))
    return trades


def read_json():
    with open('data/trades.json') as json_file:
        trades = json.load(json_file)

    return trades


def agregate_pairs(trades):
    pairs = dict()

    for trade in trades:
        if trade['pair'] not in pairs:
            pairs[trade['pair']] = list()
        pairs[trade['pair']].append(trade)

    with open('data/tradesByPairs.json', 'w') as json_file:
        json.dump(pairs, json_file, indent=2)

    return pairs


def agregate_sides(pairs):
    sides = dict()

    for pair in pairs:
        sides[pair] = dict()
        sides[pair]['sell'] = list()
        sides[pair]['buy'] = list()
        for trade in pairs[pair]:
            if trade['type'] == 'sell':
                sides[pair]['sell'].append(trade)
            elif trade['type'] == 'buy':
                sides[pair]['buy'].append(trade)
            else:
                print('type error')

    with open('data/tradesByPairsBySides.json', 'w') as json_file:
        json.dump(sides, json_file, indent=2)

    return sides


def convert(number):
    if ','in number:
        number = number.replace(',', '')
    return float(number)


def calculate(pair_trades, pair):
    r = dict()

    fees = float()
    avg_sell_price = float()
    avg_buy_price = float()
    # position_quote = float()
    position_base = float()
    total_sells_quote = float()
    total_sells_base = float()
    total_buys_quote = float()
    total_buys_base = float()

    for trade in pair_trades:
        fees += convert(trade['fee'])
        if trade['type'] == 'sell':
            total_sells_quote += convert(trade['cost'])
            total_sells_base += convert(trade['vol'])
            avg_sell_price += convert(trade['cost']) * convert(trade['price'])
            # position_quote -= convert(trade['cost']) #
            position_base -= convert(trade['vol'])

        if trade['type'] == 'buy':
            total_buys_quote += convert(trade['cost'])
            total_buys_base += convert(trade['vol'])
            avg_buy_price += convert(trade['cost']) * convert(trade['price'])
            # position_quote += convert(trade['cost'])
            position_base += convert(trade['vol'])

    r['fees'] = fees
    r['position_base'] = position_base
    # r['position_quote'] = position_quote
    # r['total_sells_quote'] = total_sells_quote
    r['total_sells_base'] = total_sells_base
    # r['total_buys_quote'] = total_buys_quote
    r['total_buys_base '] = total_buys_base

    avg_sell_price = divide(avg_sell_price, total_sells_quote)
    avg_buy_price = divide(avg_buy_price, total_buys_quote)

    r['avg_sell_price'] = avg_sell_price
    r['avg_buy_price'] = avg_buy_price

    coef = divide(avg_sell_price, avg_buy_price)

    r['coef'] = coef
    # remains_base = total_sells_base - total_buys_base
    # r['remains_base'] = remains_base
    # remains_quote = total_sells_quote - total_buys_quote
    # r['remains_quote'] = remains_quote
    # r['pnl_base'] = abs(remains_base) * (coef - 1)
    r['pnl_base'] = total_buys_base * (coef - 1)
    # pnl_quote = abs(remains_quote) * (coef - 1)
    pnl_quote = total_buys_quote * (coef - 1)
    r['pnl_quote'] = pnl_quote
    r['pnl_quote_net'] = pnl_quote - fees

    pc = divide(total_sells_base, total_buys_base)
    r['pc'] = pc

    r['realized_pnl'] = total_sells_quote - pc * total_buys_quote

    if pair in PRICE:
        r['unrealized_pnl'] = (total_buys_base - total_sells_base) * \
            PRICE[pair] - total_buys_quote * (1 - pc)

    return r


def compute(filename):
    read_csv(filename)
    trades = read_json()
    pairs = agregate_pairs(trades)
    # sides = agregate_sides(pairs)

    pnl = float()
    realized_pnl = float()
    unrealized_pnl = float()

    pl = dict()  # profits and loses
    for pair in pairs:
        pl[pair] = calculate(pairs[pair], pair)
        if pair.endswith('EUR'):
            # if pair.endswith('BTC'):
            pnl += pl[pair]['pnl_quote']
            realized_pnl += pl[pair]['realized_pnl']
            if 'unrealized_pnl' in pl[pair]:
                unrealized_pnl += pl[pair]['unrealized_pnl']

    print(pnl)
    print(realized_pnl)
    print(unrealized_pnl)
    print(realized_pnl + unrealized_pnl)

    with open('data/pnlByPairs.json', 'w') as json_file:
        json.dump(pl, json_file, indent=2)


if __name__ == '__main__':
    for filename in ['data/trades_hitbtc.csv', 'data/trades.csv']:
        print(filename)
        compute(filename)

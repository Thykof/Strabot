from decimal import Decimal as D


from trabot import utils
from trabot.side import Side
from trabot import data as d


SYMBOL = {
    'provideLiquidityRate': '0.001',
    'quantityIncrement': '10',
    'tickSize': '0.000000000001'
}

ORDER = {
    'tradesReport': [
        {
            'fee': D('0.033'),
            'quantity': D('3'),
            'price': D('11')
        }
    ]
}

ORDER2 = {
    'tradesReport': [
        {
            'fee': D('0.000000002606'),
            'quantity': D('10'),
            'price': D('0.00000026055')
        }
    ]
}


def test_get_fee():
    assert utils.get_fee({
        'quantity': D('10'),
        'price': D('0.00000025647')
    }, SYMBOL) == D('0.000000002565')
    assert utils.get_fee({
        'quantity': ORDER['tradesReport'][0]['quantity'],
        'price': ORDER['tradesReport'][0]['price']
    }, SYMBOL) == D('0.033')
    assert utils.get_fee({
        'quantity': D('10'),
        'price': D('0.00000026055')
    }, SYMBOL) == D('0.000000002606')
    assert utils.get_fee({
        'quantity': D('50'),
        'price': D('0.00000026904')
    }, SYMBOL) == D('1.3452e-8')


def test_get_breakeven():
    # order, side, min_margin, symbol
    assert utils.get_breakeven(
        order={
            'tradesReport': [
                {
                    'fee': D('0.033'),
                    'quantity': D('3'),
                    'price': D('11')
                }
            ]
        },
        side=Side(d.SELL),
        symbol=SYMBOL
    ) == D('11.022022022022')

    assert utils.get_breakeven(
        order={
            'tradesReport': [
                {
                    'fee': D('0.000000002606'),
                    'quantity': D('10'),
                    'price': D('0.00000026055')
                }
            ]
        },
        side=Side(d.SELL),
        symbol=SYMBOL
    ) == D('2.61072E-7')
    assert utils.get_breakeven(
        order=ORDER2,
        side=Side(d.BUY),
        symbol=SYMBOL
    ) == D('2.60029E-7')
    assert utils.get_breakeven(
        order=ORDER2,
        side=Side(d.SELL),
        symbol=SYMBOL
    ) == D('2.61072E-7')

    assert utils.get_breakeven(
        order={
            'tradesReport': [
                {
                    'fee': D('1.3452e-8'),
                    'quantity': D('50'),
                    'price': D('0.00000026904')
                }
            ]
        },
        side=Side(d.BUY),
        symbol=SYMBOL
    ) == D('2.68502E-7')
    assert utils.get_breakeven(
        order={
            'tradesReport': [
                {
                    'fee': D('1.3452e-8'),
                    'quantity': D('50'),
                    'price': D('0.00000026904')
                }
            ]
        },
        side=Side(d.BUY),
        symbol=SYMBOL
    ) == D('2.68502E-7')
    assert utils.get_breakeven(
        order={
            'tradesReport': [
                {
                    'fee': D('0.000000002569'),
                    'quantity': D('10'),
                    'price': D('0.00000025686')
                }
            ]
        },
        side=Side(d.BUY),
        symbol=SYMBOL
    ) == D('2.56347E-7')


def test_get_profitable_price():
    assert utils.get_profitable_price(
        filled_order={
            'tradesReport': [
                {
                    'fee': D('0.000000002569'),
                    'quantity': D('10'),
                    'price': D('0.00000025686')
                }
            ]
        },
        orderbook_price=D('0.00000026555'),
        side=Side(d.BUY),
        min_margin=1,
        symbol=SYMBOL
    ) == D('2.55834E-7')
    assert utils.get_profitable_price(
        filled_order=ORDER2,
        orderbook_price=D('2.57374E-7'),
        side=Side(d.SELL),
        min_margin=2,
        symbol=SYMBOL
    ) == D('2.62116E-7')


def test_store_orders(tmpdir):
    tmpdir.mkdir("data")
    utils.store_orders(
        {
            'id': '155845037985',
            'clientOrderId': '3c2dc822dabd1e9c52e521e8116000b7',
            'symbol': 'BTCUSD',
            'side': 'sell',
            'status': 'filled',
            'type': 'limit',
            'timeInForce': 'GTD',
            'quantity': '0.00001',
            'price': '10748.88',
            'cumQuantity': '0.00001',
            'createdAt': '2019-08-20T19: 54: 40.264Z',
            'updatedAt': '2019-08-20T19: 54: 56.514Z',
            'postOnly': True,
            'expireTime': '2019-08-20T19: 55: 00.000Z',
            'tradesReport': {
                'id': '647395668',
                'quantity': '0.00001',
                'price': '10748.88',
                'fee': '0.000107488800',
                'timestamp': '2019-08-20T19: 54: 56.514Z',
            }
        },
        {},
        [],
        'data/orders'
    )

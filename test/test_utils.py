from decimal import Decimal


from trabot import utils

def test_get_fee():
    assert utils.get_fee({
        'quantity': 10,
        'price': 0.00000025647
    }, {
        'provideLiquidityRate': 0.001
    }) == Decimal('0.000000002565')

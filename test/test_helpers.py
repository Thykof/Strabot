from trabot import helpers


def test_obj_to_string():
    in_ = [
        {
            "id": 6,
            "clientOrderId": "pkjhvgc",
            "symbol": "ETHBTC",
            "side": "buy",
            "status": "partiallyFilled",
            "type": "limit",
            "timeInForce": "GTC",
            "quantity": "0.020",
            "price": "0.046001",
            "cumQuantity": "0.005",
            "postOnly": "false",
            "createdAt": "2017-05-12T17:17:57.437Z",
            "updatedAt": "2017-05-12T17:18:08.610Z"
        }
    ]
    out = helpers.obj_to_string(in_)
    expected_out = """
id: 6
clientOrderId: pkjhvgc
symbol: ETHBTC
side: buy
status: partiallyFilled
type: limit
timeInForce: GTC
quantity: 0.020
price: 0.046001
cumQuantity: 0.005
postOnly: false
createdAt: 2017-05-12T17:17:57.437Z
updatedAt: 2017-05-12T17:18:08.610Z"""
    assert out == expected_out

from threading import Lock
from datetime import datetime
from decimal import Decimal


l = Lock()

def trunc(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return float('{0:.{1}f}'.format(f, n))
    i, _, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))

def average(stack):
    #return sum(stack) / len(stack)
    sum_ = float()
    for elt in stack:
        sum_ += elt
    return sum_ / len(stack)

def log(msg, filename):
    with open(filename, 'a') as log_file:
        # TODO: split lines
        log_file.write(str(datetime.now()) + '  ' + msg + '\n')

def tell(msg, indent=0, very_silent=False):
    if not isinstance(msg, str):
        msg = obj_to_string(msg)
    msg = '  ' * indent + msg
    with l:
        log(msg, 'data/client.log')
    if not very_silent:
        with l:
            print(msg)

def print_obj(obj, indent=0, very_silent=False):
    tell(obj_to_string(obj), indent, very_silent)

def obj_to_string(obj, msg='', indent=0):
    if isinstance(obj, str):
        return msg + '  ' * indent + obj
    if isinstance(obj, (float, int, bool, Decimal)):
        return msg + '  ' * indent + str(obj)
    if isinstance(obj, (list, tuple)):
        result = ''
        for item in obj:
            result += '  ' * indent + obj_to_string(item, msg, indent + 2)
        return result
    result = ''
    for key in obj.keys():
        result += '\n' + '  ' * indent + key + ': ' + obj_to_string(obj[key], msg, indent + 2)
    return result

def goodbye(orders, profit):
    """Save orders and profit dictionnaries."""
    with open('data/profit.txt', 'a') as myfile:
        myfile.write('\n' + str(profit))
    with open('data/orders', 'a') as myfile:
        myfile.write('\n' + str(orders))

from threading import Lock


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

def tell(msg, indent=0):
    if not isinstance(msg, str):
        msg = str(msg)
    msg = '  ' * indent + msg
    with l:
        with open('data/client.log', 'a') as log:
            log.write(str(msg) + '\n')
    with l:
        print(msg)

def print_obj(obj, indent=0):
    if isinstance(obj, str):
        tell(obj, indent)
    elif isinstance(obj, (float, int)):
        tell(obj, indent)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            print_obj(item, indent)
    else:
        for key in obj.keys():
            if isinstance(obj[key], str):
                tell(key + ': ' + obj[key], indent)
            else:
                tell(key + ': ', indent)
                print_obj(obj[key], indent+2)

def goodbye(orders, profit):
    """Save orders and profit dictionnaries."""
    with open('data/profit.txt', 'a') as myfile:
        myfile.write('\n' + str(profit))
    with open('data/orders', 'a') as myfile:
        myfile.write('\n' + str(orders))

def trunc(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return float('{0:.{1}f}'.format(f, n))
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))

def average(stack):
    #return sum(stack) / len(stack)
    sum = float()
    for elt in stack:
        sum += elt
    return sum / len(stack)

def tell(msg):
    with open('data/client.log', 'a') as log:
        log.write(str(msg) + '\n')
    print(msg)

def print_dict(dict_, itend=0):
    for key in dict_.keys():
        msg = ' '*itend
        msg += key + ': ' + str(dict_[key])
        tell(msg)

def goodbye(orders, profit):
    """Save orders and profit dictionnaries."""
    with open('data/profit.txt', 'a') as myfile:
        myfile.write('\n' + str(profit))
    with open('data/orders', 'a') as myfile:
        myfile.write('\n' + str(orders))

from threading import Lock
from datetime import datetime
from decimal import Decimal


LOCK = Lock()


def log_store(msg, filename):
    with open(filename, 'a') as log_file:
        # TODO: split lines
        log_file.write(str(datetime.now()) + '  ' + msg + '\n')


def log(msg, indent=0, very_silent=False):
    if not isinstance(msg, str):
        msg = obj_to_string(msg)
    msg = '  ' * indent + msg
    with LOCK:
        log_store(msg, 'data/client.log')
    if not very_silent:
        with LOCK:
            print(msg)


def obj_to_string(obj, msg='', indent=0):
    if isinstance(obj, str):
        return msg + '  ' * indent + obj
    if isinstance(obj, (float, int, bool, Decimal)):
        return msg + '  ' * indent + str(obj)
    if isinstance(obj, (list, tuple)):
        result = ''
        for item in obj:
            result += '  ' * indent + obj_to_string(item, msg, indent)
        return result
    if isinstance(obj, dict):
        result = ''
        for key in obj.keys():
            result += '\n' + '  ' * indent + key + ': ' + \
                obj_to_string(obj[key], msg, indent)
        return result
    return msg + '  ' * indent + str(obj)


def store_stats(value, filename='data/stats.txt'):
    if not filename.startswith('data/'):
        filename = 'data/' + filename
    with open(filename, 'a') as file_stat:
        file_stat.write(str(value) + '\n')

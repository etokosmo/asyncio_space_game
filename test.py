import time
from random import choice


def get_all_symbols_in_list():
    start_time = time.time()
    symbols = ['+', '*', '.', ':']
    for symbol in symbols:
        pass
    print("--- %s seconds ---" % (time.time() - start_time))


def get_all_symbols_in_str():
    start_time = time.time()
    symbols = '+*.:'
    for symbol in symbols:
        pass
    print("--- %s seconds ---" % (time.time() - start_time))


get_all_symbols_in_list()
get_all_symbols_in_str()



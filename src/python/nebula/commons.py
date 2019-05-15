import os
import json
import time
import functools

import colorama

colorama.init()

# ============================================================================================================================ #
# Decorators
# ============================================================================================================================ #

def measure_time(f):
    def wrapper(*argv):
        start = time.clock()
        result = f(*argv)
        end = time.clock()
        print(colorama.Fore.YELLOW + 'took ', '{:10.9f}'.format(end - start))
        return result
    return wrapper

class Memoize:
    def __init__(self, f):
        self.f = f
        self.cache = {}

    def __call__(self, *args):
        if not args[0] in self.cache:
            self.cache[args[0]] = self.f(*args)
        return self.cache[args[0]]

# ============================================================================================================================ #
# STDIO Wrappers/Helpers
# ============================================================================================================================ #

def colorize(*vargs):
    s = ''.join(functools.reduce(lambda x, y: x + str(y) + ' ', vargs))
    return s.strip() + colorama.Fore.WHITE

def red(*args):
    return colorize(colorama.Fore.RED, *args)

def cyan(*args):
    return colorize(colorama.Fore.CYAN, *args)

def blue(*args):
    return colorize(colorama.Fore.BLUE, *args)

def white(*args):
    return colorize(colorama.Fore.WHITE, *args)

def green(*args):
    return colorize(colorama.Fore.GREEN, *args)

def yellow(*args):
    return colorize(colorama.Fore.YELLOW, *args)

def magenta(*args):
    return colorize(colorama.Fore.MAGENTA, *args)

def pretty_print(*args):
    def inner(*vargs):
        return ''.join(functools.reduce(lambda x, y: x + str(y) +  colorama.Fore.WHITE + ' ', vargs))
    print(inner(colorama.Fore.WHITE, *args))

def json_print(d):
    print(json.dumps(d, sort_keys = True, indent = 4, separators = (',', ': ')))

def jsonify(s):
    return json.dumps(s, sort_keys = True, indent = 4, separators = (',', ': '))

def compactify(l):
    return '[' + ','.join(map(lambda t: str(t), l)) + ']'
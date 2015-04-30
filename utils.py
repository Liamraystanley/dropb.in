import sys
sys.path += ['lib']
import flask
import functools
import random
import string
import re
import time
from dateutil.relativedelta import relativedelta


def auth(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        if 'authed' in flask.session:
            return method(*args, **kwargs)
        else:
            return flask.redirect('/')
    return wrapper


def gen_word(min, max):
    # gen_word(2, 3)
    vowels = list('aeiou')
    word = ''
    syllables = min + int(random.random() * (max - min))

    def word_part(type):
        if type is 'c':
            return random.sample([ch for ch in list(string.lowercase) if ch not in vowels], 1)[0]
        if type is 'v':
            return random.sample(vowels, 1)[0]

    for i in range(0, syllables):
        ran = random.random()
        if ran < 0.333:
            word += word_part('v') + word_part('c')
        elif ran < 0.666:
            word += word_part('c') + word_part('v')
        else:
            word += word_part('c') + word_part('v') + word_part('c')
    return word


def gen_rand(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def validate(id):
    try:
        id_encoded = id.encode('utf-8')
        if not re.match(r'^[A-Za-z0-9]+', id):
            return False
        if sys.getsizeof(id_encoded) < 1 or sys.getsizeof(id_encoded) > 50:
            return False
        return True
    except:
        return False

# Time convert usage
# date(relativedelta(seconds=1207509))
attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
date = lambda delta: [
    '%d %s' % (
        getattr(delta, attr), getattr(delta, attr) > 1 and
        attr or attr[:-1]
    ) for attr in attrs if getattr(delta, attr)]


def relative(**kwargs):
    return date(relativedelta(**kwargs))


def hrt(tmp_time):
    return relative(seconds=int(time.time()) - int(tmp_time))
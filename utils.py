import flask
import functools
import random
import string


def login_required(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        if 'authed' in flask.session:
            return method(*args, **kwargs)
        else:
            # pass for now, however we're going to need to ensure that we can
            # forcefully pull up the login prompt on the main page. (Possibly)
            # by injecting javascript into an onload only when they're unauthed?
            pass
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

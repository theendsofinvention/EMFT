# coding=utf-8
"""Simple Lua Python Parser"""
import re
# from collections import OrderedDict
import mpmath
# from custom_logging.custom_logging import make_logger

# LOGGER = make_logger('slpp')

ERRORS = {
    'unexp_type_str'    : 'decoding error: string expected',
    'unexp_end_string'  : 'Unexpected end of string while parsing Lua string.',
    'unexp_end_table'   : 'Unexpected end of table while parsing Lua string.',
    'mfnumber_minus'    : 'Malformed number (no digits after initial minus).',
    'mfnumber_dec_point': 'Malformed number (no digits after decimal point).',
    'mfnumber_sci'      : 'Malformed number (bad scientific format).',
}


class SLPPErrors:
    """Container class for SLPP exceptions"""

    class BaseSLPPError(Exception):
        """Base exception for SLPP module"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class ParsingError(BaseSLPPError):
        """Error during parsing"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


class SLPP:
    """Simple Lua Python Parser"""

    def __init__(self):
        # LOGGER.debug("instantiating parser")
        self.text = ''
        self.ch = ''
        self.at = 0
        self.len = 0
        self.depth = 0
        self.space = re.compile('\s', re.M)
        self.alnum = re.compile('\w', re.M)
        self.newline = '\n'
        self.tab = '\t'
        self.tab = '    '

    def decode(self, text):
        """Decode a Lua string to an Ordered Dictionary object
        :type text: str
        :rtype: OrderedDict
        :param text: string to decode
        :return: Ordered Dictionary
        """
        # LOGGER.debug("decoding text to dictionnary")
        if not text or type(text) is not str:
            raise SLPPErrors.ParsingError(ERRORS['unexp_type_str'])
        # FIXME: only short comments removed
        reg = re.compile('--.*$', re.M)
        text = reg.sub('', text)
        self.text = text
        self.at, self.ch, self.depth = 0, '', 0
        self.len = len(text)
        self.next_chr()
        result = self.value()
        return result

    def encode(self, obj):
        """Encodes a dictionary-like object to a Lua string
        :param obj: object to encode
        :return: valid Lua string
        """
        # LOGGER.debug("encoding dictionary to text")
        if not obj:
            # LOGGER.error('missing object to encode')  # TODO manage error
            return
        self.depth = 0
        return self.__encode(obj)

    def __encode(self, obj):
        s = ''
        tab = self.tab
        newline = self.newline
        if isinstance(obj, str):
            s += '"%s"' % obj.replace('"', '\\"')
        elif isinstance(obj, bool):
            s += str(obj).lower()
        elif isinstance(obj, (int, float, complex, mpmath.mpf)):
            s += str(obj)
        elif isinstance(obj, (list, tuple, dict)):
            self.depth += 1
            # noinspection PyTypeChecker
            if not isinstance(obj, dict) and len(filter(
                    lambda x: isinstance(x, (int, float, mpmath.mpf)) or (isinstance(x, str) and len(x) < 10), obj
            )) == len(obj):
                newline = tab = ''
            dp = tab * self.depth
            s += "%s%s{%s" % (newline, tab * (self.depth - 1), newline if len(obj) > 0 else '')
            if isinstance(obj, dict):
                s += (',%s' % newline).join([dp + '[{}] ={}{}'.format(k,
                                                                      '' if isinstance(v, (list, tuple, dict)) else ' ',
                                                                      self.__encode(v)) if type(
                    k) is int else dp + '["{}"] ={}{}'.format(k, '' if isinstance(v, (list, tuple, dict)) else ' ',
                                                              self.__encode(v))
                                             for k, v in obj.items()])
            else:
                s += (',%s' % newline).join([dp + self.__encode(el) for el in obj])
            self.depth -= 1
            if len(obj) > 0:
                s += ','
            s += "%s%s}" % (newline, tab * self.depth)
        return s

    # noinspection PyMissingOrEmptyDocstring
    def white(self):
        while self.ch:
            if self.space.match(self.ch):
                self.next_chr()
            else:
                break

    # noinspection PyMissingOrEmptyDocstring
    def next_chr(self):
        if self.at >= self.len:
            self.ch = None
            return None
        self.ch = self.text[self.at]
        self.at += 1
        return True

    # noinspection PyMissingOrEmptyDocstring
    def value(self):
        self.white()
        if not self.ch:
            return
        if self.ch == '{':
            return self.object()
        if self.ch == "[":
            self.next_chr()
        if self.ch in ['"', "'", '[']:
            return self.string(self.ch)
        if self.ch.isdigit() or self.ch == '-':
            return self.number()
        return self.word()

    # noinspection PyMissingOrEmptyDocstring
    def string(self, end=None):
        s = ''
        start = self.ch
        if end == '[':
            end = ']'
        if start in ['"', "'", '[']:
            while self.next_chr():
                if self.ch == end:
                    self.next_chr()
                    if start != "[" or self.ch == ']':
                        return s
                if self.ch == '\\' and start == end:
                    self.next_chr()
                    if self.ch != end:
                        s += '\\'
                s += self.ch
        print(ERRORS['unexp_end_string'])

    # noinspection PyMissingOrEmptyDocstring
    def object(self):
        o = dict()
        k = ''
        idx = 0
        numeric_keys = False
        self.depth += 1
        self.next_chr()
        self.white()
        if self.ch and self.ch == '}':
            self.depth -= 1
            self.next_chr()
            return o  # Exit here
        else:
            while self.ch:
                self.white()
                if self.ch == '{':
                    o[idx] = self.object()
                    idx += 1
                    continue
                elif self.ch == '}':
                    self.depth -= 1
                    self.next_chr()
                    if k:
                        o[idx] = k
                    if not numeric_keys and len(
                            [key for key in o if type(key) in (str, float, bool, tuple, mpmath.mpf)]) == 0:
                        ar = []
                        for key in o:
                            ar.insert(key, o[key])
                        o = ar
                    return o  # or here
                else:
                    if self.ch == ',':
                        self.next_chr()
                        continue
                    else:
                        k = self.value()
                        if self.ch == ']':
                            numeric_keys = True
                            self.next_chr()
                    self.white()
                    if self.ch == '=':
                        self.next_chr()
                        self.white()
                        o[k] = self.value()
                        idx += 1
                        k = ''
                    elif self.ch == ',':
                        self.next_chr()
                        self.white()
                        o[idx] = k
                        idx += 1
                        k = ''
        print(ERRORS['unexp_end_table'])  # Bad exit here

    # noinspection PyMissingOrEmptyDocstring
    def word(self):
        s = ''
        if self.ch != '\n':
            s = self.ch
        while self.next_chr():
            if self.alnum.match(self.ch):
                s += self.ch
            else:
                if re.match('^true$', s, re.I):
                    return True
                elif re.match('^false$', s, re.I):
                    return False
                elif s == 'nil':
                    return None
                return str(s)

    # noinspection PyMissingOrEmptyDocstring
    def number(self):
        # noinspection PyMissingOrEmptyDocstring
        def next_digit(err):
            _n = self.ch
            self.next_chr()
            if not self.ch or not self.ch.isdigit():
                s = []
                for _ in range(10):
                    s.append(self.ch)
                    self.next_chr()
                raise Exception(''.join(s))
                raise SLPPErrors.ParsingError(err)
            return _n

        n = ''
        try:
            if self.ch == '-':
                n += next_digit(ERRORS['mfnumber_minus'])
            n += self.digit()
            if n == '0' and self.ch in ['x', 'X']:
                n += self.ch
                self.next_chr()
                n += self.hex()
            else:
                if self.ch and self.ch == '.':
                    n += next_digit(ERRORS['mfnumber_dec_point'])
                    n += self.digit()
                if self.ch and self.ch in ['e', 'E']:
                    n += self.ch
                    self.next_chr()
                    if not self.ch or self.ch not in ('+', '-'):
                        raise SLPPErrors.ParsingError(ERRORS['mfnumber_sci'])
                    n += next_digit(ERRORS['mfnumber_sci'])
                    n += self.digit()
        except SLPPErrors.ParsingError as e:
            print(e)
            return 0
        try:
            return int(n, 0)
        except:
            pass
        return mpmath.mpf(n)

    # noinspection PyMissingOrEmptyDocstring
    def digit(self):
        n = ''
        while self.ch and self.ch.isdigit():
            n += self.ch
            self.next_chr()
        return n

    # noinspection PyMissingOrEmptyDocstring
    def hex(self):
        n = ''
        while self.ch and \
                (self.ch in 'ABCDEFabcdef' or self.ch.isdigit()):
            n += self.ch
            self.next_chr()
        return n


slpp = SLPP()

__all__ = ['slpp']

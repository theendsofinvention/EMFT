# coding=utf-8
"""Simple Lua Python Parser"""
import re

import mpmath
from natsort import natsorted

from emft.core.logging import make_logger

LOGGER = make_logger(__name__)

# noinspection SpellCheckingInspection
ERRORS = {
    'unexp_type_str': 'decoding error: string expected',
    'unexp_end_string': 'Unexpected end of string while parsing Lua string.',
    'unexp_end_table': 'Unexpected end of table while parsing Lua string.',
    'mfnumber_minus': 'Malformed number (no digits after initial minus).',
    'mfnumber_dec_point': 'Malformed number (no digits after decimal point).',
    'mfnumber_sci': 'Malformed number (bad scientific format).',
}


class BaseSLTPError(Exception):
    """Base exception for SLTP module"""

    def __init__(self, *args):
        super().__init__(*args)


class SLTPParsingError(BaseSLTPError):
    """Error during parsing"""

    def __init__(self, *args):
        super().__init__(*args)


class SLTPEmptyObjectError(BaseSLTPError):
    """Error during parsing"""

    def __init__(self, *args):
        super().__init__(*args)


class SLTP:
    """Simple Lua Python Parser"""

    def __init__(self):
        LOGGER.debug('instantiating parser')
        self.text = ''
        self.ch = ''
        self.at = 0
        self.len = 0
        self.depth = 0
        self.qual = None
        self.space = re.compile(r'\s', re.M)
        self.alnum = re.compile(r'\w', re.M)
        self.line_end = re.compile(r'^(?P<intro>[ \t]*\})(?P<comment> -- end of \[.*\]),$')
        self.newline = '\n'
        self.tab = '\t'
        self.tab = '    '

    def decode(self, text):
        """Decode a Lua string to an dictionary
        :type text: str
        :rtype: dict
        :param text: string to decode
        :return: dictionary
        """
        LOGGER.debug('decoding text to dictionary')

        if not text or type(text) is not str:
            raise SLTPParsingError(ERRORS['unexp_type_str'])

        LOGGER.debug('extracting qualifier')
        qual = re.compile(r'^(?P<value>(dictionary|mission|mapResource) = ?)\n')
        match = qual.match(text)

        if match is None:
            raise ValueError('qualifier not found; first line: {}'.format(text.split('\n')[0]))

        self.qual = match.group('value')
        text = qual.sub('', text)

        reg = re.compile(r' -- .*[^\\]$', re.M)
        text = reg.sub('', text)

        self.text = text
        self.at, self.ch, self.depth = 0, '', 0
        self.len = len(text)
        self.next_chr()
        result = self.value()
        return result, self.qual

    def encode(self, obj, qualifier: str):
        """Encodes a dictionary-like object to a Lua string
        :param qualifier:
        :param obj: object to encode
        :return: valid Lua string
        """
        LOGGER.debug('encoding dictionary to text')
        if not obj:
            if qualifier.replace('=', '').rstrip() == 'mapResource':
                # Accept empty mapResource
                return '{}\n{{\n}} -- end of {}\n'.format(qualifier, qualifier.replace('=', '').rstrip())
            else:
                LOGGER.error('{}\n{{\n}} -- end of {}\n'.format(qualifier, qualifier.replace('=', '').rstrip()))
                raise SLTPEmptyObjectError(qualifier)
                # return '{}\n{{\n}} -- end of {}\n'.format(qualifier, qualifier.replace('=', '').rstrip())
        self.depth = 0
        out = []
        s = self.__encode(obj)
        lines = s.split(self.newline)
        for line in lines:
            m = self.line_end.match(line)
            if m:
                out.append('{},{}'.format(m.group('intro'), m.group('comment')))
            else:
                out.append(line)
        return '{}{} -- end of {}\n'.format(qualifier, self.newline.join(out), qualifier.replace('=', '').rstrip())

    def __encode(self, obj, dict_name=None):  # noqa C901
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
            # Ladies and gentlemen, please take a minute to behold the following code.
            # Breathe slowly, let it sink in for a minute.
            # Yes, I agree, this sucks *so* much I should hang for it.
            # Now, deal with it ^^
            self.depth += 1
            # noinspection PyTypeChecker
            if not isinstance(obj, dict) and len(filter(
                lambda x: isinstance(x, (int, float, mpmath.mpf)) or (isinstance(x, str) and len(x) < 10), obj
            )) == len(obj):
                newline = tab = ''
            dp = tab * self.depth
            s += '%s%s{%s' % (newline, tab * (self.depth - 1), newline if len(obj) > 0 else '')
            if isinstance(obj, dict):
                s += (',%s' % newline).join(
                    [dp + '[{}] ={}{}'.format(k,
                                              '' if isinstance(obj[k], (list, tuple, dict)) else ' ',
                                              self.__encode(obj[k], k)) if type(
                        k) is int else dp + '["{}"] ={}{}'.format(k, '' if isinstance(obj[k],
                                                                                      (list, tuple, dict)) else ' ',
                                                                  self.__encode(obj[k], k))
                     for k in natsorted(obj.keys(), key=str)])
            else:
                s += (',%s' % newline).join([dp + self.__encode(el) for el in obj])
            self.depth -= 1
            if len(obj) > 0:
                s += ','
            s += '%s%s}' % (newline, tab * self.depth)
        if isinstance(obj, dict):
            try:
                int(dict_name)
                s += ' -- end of [{}]'.format(dict_name)
            except (ValueError, TypeError):
                if dict_name is not None:
                    s += ' -- end of ["{}"]'.format(dict_name)
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
            o = self.object()
            ret = dict()
            for k in natsorted(o.keys()):
                ret[k] = o[k]
            return ret
        if self.ch == '[':
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
                    if start != '[' or self.ch == ']':
                        return s
                if self.ch == '\\' and start == end:
                    self.next_chr()
                    if self.ch != end:
                        s += '\\'
                s += self.ch
        raise SLTPParsingError(ERRORS['unexp_end_string'])

    # noinspection PyMissingOrEmptyDocstring
    def object(self):  # noqa C901
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
                        [
                            key for key in o if type(key) in (str, float, bool, tuple, mpmath.mpf)
                        ]
                    ) == 0:
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
        raise SLTPParsingError(ERRORS['unexp_end_table'])  # Bad exit here

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
    def number(self):  # noqa C901
        # noinspection PyMissingOrEmptyDocstring
        def next_digit(err):
            _n = self.ch
            self.next_chr()
            if not self.ch or not self.ch.isdigit():
                raise SLTPParsingError(err)
            return _n

        n = ''
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
                    raise SLTPParsingError(ERRORS['mfnumber_sci'])
                n += next_digit(ERRORS['mfnumber_sci'])
                n += self.digit()
        try:
            return int(n, 0)
        except ValueError:
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
        while self.ch and (self.ch in 'ABCDEFabcdef' or self.ch.isdigit()):
            n += self.ch
            self.next_chr()
        return n


sltp = SLTP()

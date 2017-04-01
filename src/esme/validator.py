# coding=utf-8
"""
Easy to use validator for different values
"""
from os.path import exists
from re import fullmatch as re_full_match

from utils.custom_logging import make_logger

LOGGER = make_logger(__name__)


class ValidatorError(Exception):
    """
    Base Error for the Validator class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Validator:
    """
    Validates many kind of values against pre-defined conditions, raises Exception and logs errors
    """

    def __init__(self, *, _type=None, _instance=None, _min=None, _max=None, _regex=None, _in_list=None, _path_exists=False, exc=None,
                 logger=None):
        self.type = _type
        self.instance = _instance
        self.min = _min
        self.max = _max
        self.regex = _regex
        self.in_list = _in_list
        self.path_exists = _path_exists
        self.exc = exc
        self.logger = logger

    def validate(self, value, param_name, exc=None, logger=None):
        """
        :param value: value to validate
        :param param_name: name of the value (for logging purpose)
        :param exc: exception to raise (default is "ValidatorError")
        :param logger: logger to use (default will be "Validator.logger")
        """
        if exc is None:
            exc = self.exc
            if exc is None:
                exc = ValidatorError
        if logger is None:
            logger = self.logger
        if self.type is not None and not type(value) == self.type:
            error_msg = 'invalid type for parameter "{}": {} (value: {}) -- expected {}'.format(param_name, type(value), value, self.type)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.instance is not None and not isinstance(value, self.instance):
            error_msg = 'invalid instance for parameter "{}": {} (value: {}) -- expected {}'.format(param_name, type(value), value, self.instance)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.min is not None and value < self.min:
            error_msg = 'invalid value for parameter "{}" (under minima): {}'.format(param_name, value)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.max is not None and value > self.max:
            error_msg = 'invalid value for parameter "{}" (over maxima): {}'.format(param_name, value)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.regex is not None and not re_full_match(self.regex, value):
            error_msg = 'invalid value for parameter "{}" (should match: "{}"): {}'.format(param_name, self.regex,
                                                                                           value)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.in_list is not None and value not in self.in_list:
            error_msg = 'invalid value for parameter "{}"; "{}" is not in list: {}'.format(param_name, value,
                                                                                           self.in_list)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)
        if self.path_exists and not exists(value):
            error_msg = '"{}" does not exist: {}'.format(param_name, value)
            if logger is not None:
                logger.error(error_msg)
            if exc is not None:
                raise exc(error_msg)


# noinspection PyShadowingBuiltins
bool = Validator(_type=bool)
# noinspection PyShadowingBuiltins
str = Validator(_type=str)
integer = Validator(_type=int)
positive_integer = Validator(_type=int, _min=0)
# noinspection PyShadowingBuiltins
float = Validator(_type=float)
existing_path = Validator(_path_exists=True)
# noinspection PyShadowingBuiltins
list = Validator(_type=list)
not_a_str = [-1, True, False, None, 1234, {}, []]
not_an_int = [True, False, None, '', 'meh', {}, [], 12.34]
not_a_positive_int = [True, False, None, '', 'meh', {}, [], 12.34, -1, -100000]
not_a_bool = [None, 1, 12.34, 'meh', [], {}]
# noinspection PyShadowingBuiltins
dict = Validator(_type=dict)

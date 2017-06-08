# coding=utf-8

import logging

import pytest
from hypothesis import given
from hypothesis.strategies import text, integers, booleans, floats, one_of

from src.utils.validator import Validator, not_an_int, not_a_str, not_a_positive_int, not_a_bool, valid_bool, \
    valid_int, valid_positive_int, \
    valid_str


# all = [text(), integers(), booleans(), floats(), lists(), sets(), dictionaries(text(), text())]

@given(booleans())
def test_bool(value):
    assert valid_bool.validate(value, 'bool')


@given(one_of(text(), integers(), floats()))
def test_wrong_bool(value):
    with pytest.raises(ValueError):
        valid_bool.validate(value, 'bool')


@pytest.mark.parametrize('value', not_a_bool)
def test_not_a_bool(value):
    with pytest.raises(ValueError):
        valid_bool.validate(value, 'bool')


@given(text())
def test_str(value):
    assert valid_str.validate(value, 'str')


@given(one_of(booleans(), integers(), floats()))
def test_wrong_str(value):
    with pytest.raises(ValueError):
        valid_str.validate(value, 'str')


@pytest.mark.parametrize('value', not_a_str)
def test_not_a_str(value):
    with pytest.raises(ValueError):
        valid_str.validate(value, 'str')


@given(integers())
def test_int(value):
    assert valid_int.validate(value, 'int')


@given(one_of(booleans(), text(), floats()))
def test_wrong_int(value):
    with pytest.raises(ValueError):
        valid_int.validate(value, 'int')


@pytest.mark.parametrize('value', not_an_int)
def test_not_an_int(value):
    with pytest.raises(ValueError):
        valid_int.validate(value, 'int')


@given(integers(min_value=1))
def test_positive_int(value):
    assert valid_positive_int.validate(value, 'int')


@given(one_of(booleans(), text(), floats(), integers(max_value=-1)))
def test_wrong_positive_int(value):
    with pytest.raises(ValueError):
        valid_positive_int.validate(value, 'int')


@pytest.mark.parametrize('value', not_a_positive_int)
def test_not_a_positive_int(value):
    with pytest.raises(ValueError):
        valid_positive_int.validate(value, 'int')


def test_exception():
    class DummyException(Exception):
        pass

    v = Validator(exc=DummyException, _instance=str)
    assert v.exc == DummyException
    with pytest.raises(DummyException):
        v.validate(True, 'exc')
    with pytest.raises(ValueError):
        v.validate(True, 'exc', exc=ValueError)


def test_logger():
    logger = logging.getLogger('__main__')
    other_logger = logging.getLogger('other')
    v = Validator(_instance=int, logger=logger)
    assert v.logger is logger
    v.validate(3, 'logger', logger=other_logger)
    assert v.logger is other_logger


@given(integers(min_value=5, max_value=500))
def test_min_max(value):
    assert Validator(_min=5, _max=500).validate(value, 'min_max')
    with pytest.raises(ValueError):
        Validator(_min=0).validate(-1, 'min_max')
    with pytest.raises(ValueError):
        Validator(_max=0).validate(1, 'min_max')


@pytest.mark.parametrize('str_', ['some_text', 'pre_some_text', 'some_text_suf'])
def test_regex(str_):
    assert Validator(_regex=r'.*some_text.*').validate(str_, 'regex')
    with pytest.raises(ValueError):
        Validator(_regex=r'.*some_other_text.*').validate(str_, 'regex')


def test_in_list():
    assert Validator(_in_list=['some', 'list']).validate('some', 'list')
    with pytest.raises(ValueError):
        assert Validator(_in_list=['some', 'list']).validate('nope', 'list')

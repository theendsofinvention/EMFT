# coding=utf-8

import pytest
from hypothesis import given
from hypothesis.strategies import text, integers, booleans

# noinspection PyProtectedMember
from emft.utils.decorators.typed_property import TypedProperty, _TypedProperty


class SomeClass:
    def __init__(self):
        self._some_int = 0
        self._some_str = 'test'
        self._some_bool = False

    @TypedProperty(int)
    def some_int(self, value):
        return value

    @TypedProperty(str)
    def some_str(self, value):
        return value

    @TypedProperty(bool)
    def some_bool(self, value):
        return value

    @TypedProperty(int)
    def not_set(self, value):
        return value


class TestTypedProperty:
    def test_get(self):
        o = SomeClass()
        assert o.some_bool == o._some_bool
        assert o.some_int == o._some_int
        assert o.some_str == o._some_str

    @given(text())
    def test_set_str(self, value):
        o = SomeClass()
        o.some_str = value
        assert o._some_str == value
        assert o.some_str == value

    @pytest.mark.parametrize('value', [1, False, None, float(42)])
    def test_set_wrong_str(self, value):
        o = SomeClass()
        with pytest.raises(TypeError):
            o.some_str = value

    @given(booleans())
    def test_set_bool(self, value):
        o = SomeClass()
        o.some_bool = value
        assert o._some_bool == value
        assert o.some_bool == value

    @pytest.mark.parametrize('value', [1, 'text', None, float(42)])
    def test_set_wrong_bool(self, value):
        o = SomeClass()
        with pytest.raises(TypeError):
            o.some_bool = value

    @given(integers())
    def test_set_int(self, value):
        o = SomeClass()
        o.some_int = value
        assert o._some_int == value
        assert o.some_int == value

    @pytest.mark.parametrize('value', ['text', None, float(42)])
    def test_set_wrong_int(self, value):
        o = SomeClass()
        with pytest.raises(TypeError):
            o.some_int = value

    def test_delete(self):
        o = SomeClass()
        assert hasattr(o, '_some_int')
        del o.some_int
        assert not hasattr(o, '_some_int')
        # Deleting again should not raise
        del o.some_int

    def test_not_set(self):
        o = SomeClass()
        with pytest.raises(AttributeError):
            return o.not_set

    def test_prop_instance(self):
        o = SomeClass()
        prop = SomeClass.some_bool
        assert isinstance(prop, _TypedProperty)
        assert o.some_bool is not prop

    def test_prop_func(self, mocker):
        mock = mocker.MagicMock(name='some_bool')
        mock.__name__ = 'some_bool'
        o = SomeClass()
        prop = SomeClass.some_bool
        assert isinstance(prop, _TypedProperty)
        assert o.some_bool is False
        prop.func = mock
        o.some_bool = True
        mock.assert_called_with(o, True)

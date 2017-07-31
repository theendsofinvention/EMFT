# coding=utf-8

import pytest
from unittest.mock import MagicMock

from src.utils import WatchedProperty
from src.utils.decorators.watched_property import _WatchedProperty


class Dummy:
    @WatchedProperty()
    def prop(self, value):
        return value

    @WatchedProperty(default_value='default')
    def default_prop(self, value):
        return value


def test_init():
    o = Dummy()
    o.prop = True
    assert o.prop is True


def test_add_watcher():
    callback = MagicMock()
    o = Dummy()
    o.prop = 'some value'
    Dummy.prop.add_watcher(callback)
    o.prop = 'test'
    callback.assert_called_with('test')
    assert o.prop == 'test'
    o.prop = 'caribou'
    callback.assert_called_with('caribou')
    assert o.prop == 'caribou'


def test_remove_watcher():
    callback = MagicMock()
    o = Dummy()
    o.prop = 'some value'
    Dummy.prop.add_watcher(callback)
    o.prop = 'test'
    callback.assert_called_with('test')
    callback.reset_mock()
    Dummy.prop.remove_watcher(callback)
    o.prop = 'nope'
    callback.assert_not_called()
    assert o.prop == 'nope'


def test_watcher_on_same_value():
    callback = MagicMock()
    o = Dummy()
    o.prop = 'some value'
    Dummy.prop.add_watcher(callback)
    o.prop = 'test'
    callback.assert_called_with('test')
    o.prop = 'test'
    assert o.prop == 'test'
    assert callback.call_count == 1


def test_default_value():
    o = Dummy()

    assert o.default_prop == 'default'
    o.default_prop = 'other value'
    assert o.default_prop == 'other value'


def test_no_default_value():
    o = Dummy()
    assert isinstance(Dummy.prop, _WatchedProperty)

    with pytest.raises(AttributeError):
        _ = o.prop


def test_multiple_instances():

    # Reset all watchers
    Dummy.prop._watchers = []

    o1 = Dummy()
    o2 = Dummy()

    callback = MagicMock()

    Dummy.prop.add_watcher(callback)

    assert callback.call_count == 0
    o1.prop = 'test'
    assert callback.call_count == 1
    callback.assert_called_with('test')

    o2.prop = 'caribou'
    assert callback.call_count == 2
    callback.assert_called_with('caribou')

    o2.prop = 'caribou'
    assert callback.call_count == 2

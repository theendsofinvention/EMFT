# coding=utf-8

from .meta_property import MetaProperty, _MetaProperty
from src.global_ import MACHINE_GUID
from .abstract import AbstractMeta


class _MetaGUIDProperty(_MetaProperty):

    def __get__(self, instance, owner=None):
        """
        Retrieves value.

        If instance is None, returns the descriptor object to allow access to "default" and "type"

        If instance is a valid META object, returns instance.__getitem__() if it exists in the META or returns DEFAULT.

        :param instance: instance of AbstractMeta
        :param owner: actual Class of the META instance
        :return: value of this DESCRIPTOR (DEFAULT if it isn't defined)
        """
        if instance is None:
            # Calling from Class object
            return self

        if not isinstance(instance, AbstractMeta):
            raise TypeError('_MetaProperty can only be used with Meta() instances')

        value_holder = instance.__getitem__(self.prop_name)

        if value_holder is None:

            # Not set yet, returns default
            return self.default

        else:

            assert isinstance(value_holder, dict), type(value_holder)

            if MACHINE_GUID not in value_holder:
                # No value for this machine, returns default
                return self.default

            value = value_holder[MACHINE_GUID]

            # Check the value against the setter (I'm being paranoid here)
            value = self.func(instance, value)

            # Return actual value
            return value

    def __set__(self, instance, value):
        """
        Sets value.

        :param instance: instance of AbstractMeta
        :param value: value to set the DESCRIPTOR to
        :return:
        """

        if instance is None:
            # Calling from Class object
            return self

        if not isinstance(instance, AbstractMeta):
            raise TypeError('_MetaProperty can only be used with Meta() instances')

        # noinspection PyTypeChecker
        if not isinstance(value, self.type):
            # Checks for type of "value"
            raise TypeError('expected a {}, got: {} (value: {})'.format(str(self.type), type(value), value))

        previous_value = None
        value_holder = getattr(instance, self.prop_name)

        if value_holder is None:
            value_holder = dict()

        if self.prop_name in value_holder:
            previous_value = value_holder[MACHINE_GUID]

        if value == previous_value:
            return

        # Runs whatever code is inside the decorated method and set the result to the new value
        value = self.func(instance, value)

        # If no exception was thrown, sets the value in the META
        value_holder[MACHINE_GUID] = value
        instance.__setitem__(self.prop_name, value_holder)

        # # Broadcast a Blinker signal that the value has changed
        # signal('{}_{}_value_changed'.format(instance.__class__.__name__, self.prop_name)).send(
        #     instance.__class__.__name__, value=value)

    def __delete__(self, instance):
        if instance is None:
            return self
        try:
            try:
                value_holder = getattr(instance, self.prop_name)
            except AttributeError:
                pass
            if isinstance(value_holder, dict):
                instance.__delitem__(self.prop_name)
        except KeyError:
            pass


class MetaGUIDProperty(MetaProperty):

    def __call__(self, func: callable) -> _MetaProperty:
        """
        Creates a DESCRIPTOR instance for a method of a META instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _MetaProperty
        :rtype: _MetaProperty
        """
        return _MetaGUIDProperty(func, self.default, self.type)
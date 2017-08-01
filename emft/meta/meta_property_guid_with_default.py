# coding=utf-8

from emft.global_ import MACHINE_GUID
from .abstract import AbstractMeta
# noinspection PyProtectedMember
from .meta_property_with_default import MetaPropertyWithDefault, _MetaProperty


class _MetaGUIDProperty(_MetaProperty):
    def __get__(self, instance, owner=None):
        """
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

        try:
            value_holder = getattr(instance, '_data')[self.prop_name]
        except KeyError:
            value_holder = dict()

        if value_holder is None:
            value_holder = dict()

        if MACHINE_GUID in value_holder:
            previous_value = value_holder[MACHINE_GUID]

        # Runs whatever code is inside the decorated method and set the result to the new value
        value = self.func(instance, value)

        if value == previous_value:
            return

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
            else:
                if isinstance(value_holder, dict):
                    instance.__delitem__(self.prop_name)
        except KeyError:
            pass


class MetaGUIDPropertyWithDefault(MetaPropertyWithDefault):
    def __call__(self, func: callable) -> _MetaProperty:
        """
        Creates a DESCRIPTOR instance for a method of a META instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _MetaProperty
        :rtype: _MetaProperty
        """
        return _MetaGUIDProperty(func, self.default, self.type)

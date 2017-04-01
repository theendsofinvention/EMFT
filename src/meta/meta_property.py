# coding=utf-8
from src.meta.abstract import AbstractMeta


class _MetaProperty:
    """
    Actual descriptor object created during MetaProperty.__call___ below.

    Accessing a _MetaProperty from the META class itself (SomeMeta._MetaProperty) gives access to the object itself,
    with "default", "type", "__doc__", "key" and "func".

    """

    def __init__(self, func: callable, default: object, _type: object):
        """
        Initialize the DESCRIPTOR.

        :param func: callable to overwrite
        :param default: default value if there's nothing in the META yet
        :param _type: type of object allowed to be SET
        """
        self.func = func
        self.default = default
        self.type = _type
        self.__doc__ = func.__doc__

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

        if instance.__getitem__(self.func.__name__) is None:
            # Not set yet, returns default
            return self.default
        else:
            # Check the value against the setter (I'm being paranoid here)
            value = self.func(instance, instance.__getitem__(self.func.__name__))

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

        if not isinstance(value, self.type):
            # Checks for type of "value"
            raise TypeError('expected a {}, got: {} (value: {})'.format(str(self.type), type(value), value))

        if value == getattr(instance, self.func.__name__):
            return

        # Runs whatever code is inside the decorated method and set the result to the new value
        value = self.func(instance, value)

        # If no exception was thrown, sets the value in the META
        instance.__setitem__(self.func.__name__, value)

        # # Broadcast a Blinker signal that the value has changed
        # signal('{}_{}_value_changed'.format(instance.__class__.__name__, self.func.__name__)).send(
        #     instance.__class__.__name__, value=value)

    def __delete__(self, instance):
        if instance is None:
            return self
        try:
            instance.__delitem__(self.func.__name__)
        except KeyError:
            pass


class MetaProperty:
    """
    Decorator-class to create properties for META instances.
    """

    def __init__(self, default: object, _type: object):
        """
        Initialize properties of the descriptor.

        :param default: default value of the property if it isn't set yet
        :param _type:
        """
        self.default = default
        self.type = _type

    def __call__(self, func: callable) -> _MetaProperty:
        """
        Creates a DESCRIPTOR instance for a method of a META instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _MetaProperty
        :rtype: _MetaProperty
        """
        return _MetaProperty(func, self.default, self.type)

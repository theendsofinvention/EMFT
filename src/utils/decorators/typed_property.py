# coding=utf-8


class _TypedProperty:
    """
    Actual descriptor object created during MetaProperty.__call___ below.

    Accessing a _MetaProperty from the META class itself (SomeMeta._MetaProperty) gives access to the object itself,
    with "default", "type", "__doc__", "key" and "func".

    """

    # __slots__ = ['func', 'default', 'type', '__doc__']

    def __init__(self, func: callable, type_: object):
        """
        Initialize the DESCRIPTOR.

        :param func: callable to overwrite
        :param default: default value if there's nothing in the META yet
        :param type_: type of object allowed to be SET
        """
        self.func = func
        self.type = type_
        self.attrib = '_{}'.format(self.func.__name__)
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner=None):
        """
        Retrieves value.

        If instance is None, returns the descriptor object to allow access to "type" attribute.

        If instance is valid, returns instance.__getitem__().

        :param instance: instance of AbstractMeta
        :param owner: Class of the instance
        :return: value of this DESCRIPTOR
        """
        if instance is None:
            # Calling from Class object
            return self

        try:
            getattr(instance, self.attrib)
        except AttributeError:
            # Not set yet
            raise AttributeError('property not set: {}'.format(self.attrib))
        else:
            # Check the value against the setter (I'm being paranoid here)
            value = self.func(instance, getattr(instance, self.attrib))

            # Return actual value
            return value

    def __set__(self, instance, value):
        """
        Sets value.

        :param instance: instance
        :param value: value to set the DESCRIPTOR to
        :return:
        """

        if not isinstance(value, self.type):
            # Checks for type of "value"
            raise TypeError('expected a {}, got: {} (value: {})'.format(str(self.type), type(value), value))

        if value == getattr(instance, self.func.__name__):
            # Value hasn't changed, execute nothing
            return

        # Runs whatever code is inside the decorated method and set the result to the new value
        value = self.func(instance, value)

        # If no exception was thrown, sets the value
        setattr(instance, self.attrib, value)

    def __delete__(self, instance):

        try:
            delattr(instance, self.attrib)
        except AttributeError:
            pass


class TypedProperty:
    """
    Decorator-class that yields property of a certain type.
    """

    def __init__(self, type_: object):
        """
        Initialize properties of the descriptor.

        :param type_: enforced property type
        """
        self.type = type_

    def __call__(self, func: callable) -> _TypedProperty:
        """
        Creates a DESCRIPTOR instance for a method of a META instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _MetaProperty
        :rtype: _TypedProperty
        """
        return _TypedProperty(func, self.type)

# coding=utf-8


class _WatchedProperty:
    """
    Actual descriptor object created during WatchedProperty.__call__ below.

    Watchers are set and removed by accessing the property on the class itself.

    Examples:

    class Dummy:
        @WatchedProperty()
        def prop(self, value):
            return value

    Dummy.prop.add_watcher('callable')
    Dummy.prop.remove_watcher('callable')


    Using default initial value for properties:

    class Dummy:
        @WatchedProperty(default_value='default')
        def default_prop(self, value):
            return value

    """

    def __init__(self, func: callable, default):
        """
        Initialize the descriptor.

        :param func: callable to overwrite
        :param default: default return value
        """
        self.func = func
        self._default = default
        self._watchers = []

        # Create a private value with the name of the prop
        self.prop_name = f'__{self.func.__name__}'

        # Mimick the property documentation
        self.__doc__ = func.__doc__

    def add_watcher(self, func: callable):
        """
        Adds a watcher to the list. All watchers will be executed whenever the value of the property changes.

        :param func: function to call upon change
        """
        self._watchers.append(func)

    def remove_watcher(self, func: callable):
        """
        Removes a watcher from the list.

        :param func: function to remove
        """
        self._watchers.remove(func)

    def __get__(self, instance, owner=None):
        """
        If instance is None, returns the descriptor object to allow adding or removing watchers.

        :param instance: instance
        :param owner: Class
        :return: value of the property
        """
        if instance is None:
            # Calling from Class object
            return self

        if not hasattr(instance, self.prop_name):

            # No default set
            if self._default == '__no_default_set__':
                raise AttributeError('"{}" attribute not set yet'.format(self.prop_name))

            # Default has been set, return it
            return self._default
        else:

            # Return actual value
            return getattr(instance, self.prop_name)

    def __set__(self, instance, value):
        """
        Sets value.

        :param instance: instance
        :param value: value to set the property to
        """

        if instance is None:
            # Calling from Class object
            return self

        if hasattr(instance, self.prop_name) and value == getattr(instance, self.prop_name):
            # The value hasn't changed
            return

        # Runs whatever code is inside the decorated method and set the result to the new value
        value = self.func(instance, value)

        # If no exception was thrown, sets the value in the META
        setattr(instance, self.prop_name, value)

        for watcher in self._watchers:
            # Execute all watchers
            watcher(value)


class WatchedProperty:
    """
    Decorator-class that yields property allowing for watchers call back on them.

    The watchers will be called whenever the property changes.
    """

    def __init__(self, default_value='__no_default_set__'):
        """
        Initialize properties of the descriptor.

        :param default_value: optional default value for the property (useful to set initial value)
        """
        self._default = default_value

    def __call__(self, func: callable) -> _WatchedProperty:
        """
        Creates descriptor instance.

        :param func: function to decorate
        :return: decorated function as a descriptor instance of _WatchedProperty
        :rtype: _WatchedProperty
        """
        return _WatchedProperty(func, self._default)

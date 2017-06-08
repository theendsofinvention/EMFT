# coding=utf-8
import abc


class Singleton(abc.ABCMeta):
    """
    When used as metaclass, allow only one instance of a class
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls.__name__]

    # noinspection PyMethodParameters
    @classmethod
    def wipe_instances(cls, cls_to_remove):
        """Only for testing purposes"""
        for instance in cls._instances:
            if cls_to_remove == instance:
                del cls._instances[instance]
                return

# coding=utf-8


from src.utils.singleton import Singleton


class SomeClass(metaclass=Singleton):
    pass


def test_singleton():
    some_class = SomeClass()
    some_other_class = SomeClass()
    assert some_class is some_other_class
    Singleton.wipe_instances('SomeClass')
    some_third_class = SomeClass
    assert some_third_class is not some_class
    assert some_class is some_other_class
    Singleton.wipe_instances('SomeClass')
    and_a_fourth = SomeClass()
    assert and_a_fourth is not some_third_class

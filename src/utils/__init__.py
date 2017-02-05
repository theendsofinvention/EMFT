# coding=utf-8


def nice_exit(*_):
    import os
    # Shameful monkey-patching to bypass windows being a jerk
    # noinspection PyProtectedMember
    os._exit(0)

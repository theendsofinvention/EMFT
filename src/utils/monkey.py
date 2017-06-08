# coding=utf-8


def nice_exit(code: int = 0):
    import os
    # Shameful monkey-patching to bypass windows being a jerk
    # noinspection PyProtectedMember
    os._exit(code)

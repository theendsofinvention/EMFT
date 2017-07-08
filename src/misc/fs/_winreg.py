# coding=utf-8
# TODO: unit test missing packages
try:
    import winreg
except ImportError:
    from unittest.mock import MagicMock

    winreg = MagicMock()

A_REG = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)

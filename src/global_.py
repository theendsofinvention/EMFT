# coding=utf-8

import os
import sys

import src.__version__

FROZEN = hasattr(sys, 'frozen')
try:
    TESTING = os.environ['EMFT_TESTING'] == '1'
except KeyError:
    TESTING = False

DEFAULT_ICON = ':/ico/app.ico'

if 'dev' in src.__version__.__version__:
    LINK_CHANGELOG = r'''https://github.com/132nd-etcher/EMFT/blob/develop/CHANGELOG.rst'''
else:
    LINK_CHANGELOG = r'''https://github.com/132nd-etcher/EMFT/blob/master/CHANGELOG.rst'''

LINK_REPO = r'''https://github.com/132nd-etcher/EMFT'''

PATH_LOG_FILE = 'emft.debug'
PATH_CONFIG_FILE = 'emft.config'

APP_SHORT_NAME = 'EMFT'
APP_FULL_NAME = 'Etcher\'s Mission Files Tools'
APP_VERSION = src.__version__.__version__
APP_AUTHOR = 'etcher'
APP_STATUS = 'ALPHA'
APP_RELEASE_NAME = 'Another Fine Product From The Nonsense Factory'
APP_WEBSITE = r'https://github.com/132nd-etcher/EMFT'

ENCODING = 'iso8859_15'

DCS = {
    'reg_key': {
        'stable': 'DCS World',
        'beta': 'DCS World OpenBeta',
        'alpha': 'DCS World 2 OpenAlpha',
    },
}

QT_APP = None
MAIN_UI = None

try:
    # noinspection PyUnresolvedReferences
    from winreg import ConnectRegistry, HKEY_LOCAL_MACHINE, KEY_READ, KEY_WOW64_64KEY, OpenKey, QueryValueEx

    a_reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    try:
        with OpenKey(a_reg, r"SOFTWARE\Microsoft\Cryptography") as aKey:
            MACHINE_GUID = QueryValueEx(aKey, "MachineGuid")[0]
    except FileNotFoundError:
        try:
            with OpenKey(a_reg, r"SOFTWARE\Microsoft\Cryptography", access=KEY_READ | KEY_WOW64_64KEY) as aKey:
                MACHINE_GUID = QueryValueEx(aKey, "MachineGuid")[0]
        except FileNotFoundError:
            MACHINE_UID = False
except ImportError:
    MACHINE_UID = False

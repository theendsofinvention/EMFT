# coding=utf-8

import sys
import os

import src.__version__

FROZEN = hasattr(sys, 'frozen')
try:
    TESTING = os.environ['EMFT_TESTING'] == '1'
except KeyError:
    TESTING = False

PATH_LOG_FILE = 'emft.debug'
PATH_CONFIG_FILE = 'emft.config'

APP_SHORT_NAME = 'EMFT'
APP_FULL_NAME = 'Etcher\'s Mission Files Tools'
APP_VERSION = src.__version__.__version__
APP_AUTHOR = 'etcher'
APP_STATUS = 'ALPHA'
APP_RELEASE_NAME = 'Refreshingly Unconcerned With the Vulgar Exigencies of Veracity'
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

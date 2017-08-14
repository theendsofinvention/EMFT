# coding=utf-8
# Stolen from: https://github.com/pytest-dev/pytest/blob/a3319ffe802d532e303b232a961bf63b92ec2144/_pytest/pastebin.py

import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen


def create_new_paste(contents):
    """
    Creates a new paste using bpaste.net service.
    :contents: paste contents as utf-8 encoded bytes
    :returns: url to the pasted contents
    """

    params = {
        'code': contents,
        'lexer': 'python3' if sys.version_info[0] == 3 else 'python',
        'expiry': '1week',
    }
    url = 'https://bpaste.net'
    response = urlopen(url, data=urlencode(params).encode('ascii')).read()
    m = re.search(r'href="/raw/(\w+)"', response.decode('utf-8'))
    if m:
        return '%s/show/%s' % (url, m.group(1))
    else:
        return 'bad response: ' + response

# coding=utf-8

import requests


def get_available_branches():
    req = requests.get(
        r'https://api.github.com/repos/132nd-Entropy/132nd-Virtual-Wing-Training-Mission-Tblisi/branches')
    return [b['name'] for b in req.json()]

# coding=utf-8

_radios = {
    'ARC-27': ('ARC-27', 225, 399.9, 18, {'F-86F Sabre'}),
    'ARC51': ('ARC51', 225, 399.97, 20, {'UH-1H'}),
    'ARK22': ('ARK22', 0.15, 1.75, 16, {'Ka-50'}),
    'FM Radio': ('FM Radio', 30, 87.975, 8, {'SA342Mistral', 'SA342M', 'SA342L'}),
    'FuG 16': ('FuG 16', 38.4, 42.4, 4, {'FW-190D9'}),
    'FuG 16 ZY': ('FuG 16 ZY', 38, 156, 5, {'Bf-109K-4'}),
    'R-832': ('R-832', 80, 399.9, 20, {'MiG-21Bis'}),
    'R828': ('R828', 20, 59.9, 10, {'Mi-8MT', 'Ka-50'}),
    'R863': ('R863', 100, 399.9, 20, {'Mi-8MT'}),
    'SCR552': ('SCR552', 100, 156, 4, {'P-51D', 'TF-51D', 'SpitfireLFMkIX'}),
    'UHF': ('UHF', 225, 400, 20, {'M-2000C'}),
    'V/UHF': ('V/UHF', 118, 400, 20, {'M-2000C'}),
}

empty_presets = {k: [_radios[k][1]] * _radios[k][3] for k in _radios}


class _Radio:

    def __init__(self, name, min_, max_, qty, ac):
        self.name = name
        self.min = min_
        self.max = max_
        self.qty = qty
        self.ac = ac

ARC27 = _Radio(*_radios['ARC-27'])
ARC51 = _Radio(*_radios['ARC51'])
ARK22 = _Radio(*_radios['ARK22'])
FM = _Radio(*_radios['FM Radio'])
FuG16 = _Radio(*_radios['FuG 16'])
FuG16ZY = _Radio(*_radios['FuG 16 ZY'])
R832 = _Radio(*_radios['R-832'])
R828 = _Radio(*_radios['R828'])
R863 = _Radio(*_radios['R863'])
SCR552 = _Radio(*_radios['SCR552'])
UHF = _Radio(*_radios['UHF'])
VUHF = _Radio(*_radios['V/UHF'])

radios = [ARC27, ARC51, ARK22, FM, FuG16, FuG16ZY, R832, R828, R863, SCR552, UHF, VUHF]



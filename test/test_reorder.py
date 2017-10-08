# coding=utf-8

import os
from emft.miz.miz import Miz

if os.path.exists('./test_files'):
    BASE_PATH = os.path.abspath('./test_files')
elif os.path.exists('./test/test_files'):
    BASE_PATH = os.path.abspath('./test/test_files')
else:
    raise RuntimeError('cannot find test files')

TEST_FILE = os.path.join(BASE_PATH, 'TRG_KA50.miz')


def test_reorder():
    with Miz(TEST_FILE) as m:
        d1 = dict(m.mission.d)
        m1 = dict(m._map_res)
        w1 = dict(m._warehouses)
        l1 = dict(m.mission.l10n)

    with Miz(TEST_FILE) as m:
        d2 = dict(m.mission.d)
        m2 = dict(m._map_res)
        w2 = dict(m._warehouses)
        l2 = dict(m.mission.l10n)

    assert d1 == d2
    assert m1 == m2
    assert w1 == w2
    assert l1 == l2

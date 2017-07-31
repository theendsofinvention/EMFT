# coding=utf-8

import pytest

from src.utils.updater import CustomVersion

VALID_VERSION_STRINGS = ['0.1.0', '0.1.1', '0.2.0', '0.3.1']
INVALID_VERSION_STRINGS = ['0.1', '0.1.1.0', '0.2.text', 'A.3.1']
PARTIAL_VERSION_STRINGS = [('0.1', [0, 1, None, None, None]),
                           ('1', [1, None, None, None, None]),
                           ('0.2', [0, 2, None, None, None]),
                           ('4', [4, None, None, None, None])]
ORDERED_VERSION_STRINGS = [
    [
        '0.1.0',
        '0.1.1',
        '0.2.0-alpha.1',
        '0.2.0-alpha.2',
        '0.2.0-alpha.2+build1',
        '0.2.0-alpha.2+build2',
        '0.2.0-alpha.2+build1',
        '0.2.0-beta.1',
        '0.2.0-beta.3',
        '0.2.0-exp.1',
        '0.2.0-exp.4',
        '0.2.0-patch.1',
        '0.2.0-patch.5',
        '0.2.0',
        '0.2.1',
        '0.3.0-alpha1',
    ]
]


@pytest.mark.parametrize('version_str', VALID_VERSION_STRINGS)
def test_valid_init(version_str):
    v = CustomVersion(version_str)
    assert str(v) == version_str


@pytest.mark.parametrize('version_str', VALID_VERSION_STRINGS)
def test_to_spec(version_str):
    v = CustomVersion(version_str)
    assert v.to_spec() == '.'.join(map(str, [v.major, v.minor, v.patch]))


@pytest.mark.parametrize('version_str', INVALID_VERSION_STRINGS)
def test_invalid_init(version_str):
    with pytest.raises(ValueError):
        CustomVersion(version_str)


@pytest.mark.parametrize('partial_version', PARTIAL_VERSION_STRINGS)
def test_invalid_init(partial_version):
    version_str, expected_result = partial_version
    v = CustomVersion(version_str, partial=True)
    assert str(v) == version_str
    assert list(v) == expected_result


@pytest.mark.parametrize('ordered_versions', ORDERED_VERSION_STRINGS)
def test_ordered_versions(ordered_versions):
    versions_list = [CustomVersion(version) for version in ordered_versions]
    assert versions_list == sorted(versions_list)
    assert max(versions_list) == versions_list[-1]

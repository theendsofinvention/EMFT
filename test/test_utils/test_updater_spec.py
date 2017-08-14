# coding=utf-8

import pytest

from emft.updater import channel, customspec, customversion

VERSIONS = set(
    customversion.CustomVersion(version) for version in [
        '0.1.0',
        '0.2.1',
        '0.2.2',
        '0.2.3',
        '0.2.4-patch.1',
        '0.2.5-patch.2',
        '0.2.6-patch.3',
        '0.3.0-exp.1',
        '0.3.0-exp.2',
        '0.3.0-exp.3',
        '0.4.0-beta.1',
        '0.4.0-beta.2',
        '0.4.0-beta.3',
        '0.5.0-alpha.Branch.1',
        '0.5.0-alpha.Branch.2',
        '0.5.0-alpha.Branch.3',
        '0.6.0-PullRequest.500.3',
    ]
)


@pytest.mark.parametrize(
    'values',
    [
        ('>0.1.0', channel.STABLE, '0.2.3'),
        ('>0.1.0', channel.PATCH, '0.2.6-patch.3'),
        ('>0.1.0', channel.EXP, '0.3.0-exp.3'),
        ('>0.1.0', channel.BETA, '0.4.0-beta.3'),
        ('>0.1.0', channel.ALPHA, '0.5.0-alpha.Branch.3'),
        ('0', channel.ALPHA, '0.5.0-alpha.Branch.3'),
    ]
)
def test_spec(values):
    spec_str, channel_, expected_result = values
    spec = customspec.CustomSpec(spec_str)
    result = str(spec.select_channel(VERSIONS, channel_))
    assert result == expected_result, f'{spec} should be {expected_result}, got {result}'


@pytest.mark.parametrize(
    'values',
    (
        ('0.1.0', '==0.1.0', True),
        ('0.1.0', '==0.1.1', False),
        ('0.1.0-alpha.1', '>0.1.0', False),
        ('0.2.0-alpha.1', '>0.1.0', True),
        ('0.2.0-alpha.1', '>0.1.0-beta', True),
        ('0.2.0-alpha.1', '>0.2.0', False),
        ('0.2.0-beta.1', '>0.2.0', False),
        ('0.2.0-rc.1', '>0.2.0', False),
        ('0.2.0-patch.1', '>0.2.0', False),
        ('0.2.0-alpha.PullRequest.500.1', '>0.2.0', False),
        ('0.2.0-alpha.1', '>0.1.0', True),
        ('0.2.0-alpha.1', '>0.1.0', True),
    )
)
def test_spec(values):
    version_str, spec_str, expected_result = values
    version = customversion.CustomVersion(version_str)
    spec = customspec.CustomSpec(spec_str)
    result = version in spec
    assert result == expected_result, f'{version} should {"not " if not expected_result else ""}be in {spec}'

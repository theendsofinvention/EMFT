# coding=utf-8

import os
from emft.utils.updater.customversion import CustomVersion
import subprocess
import sys
from json import loads, JSONDecodeError

__version__ = None


def get_gitversion() -> dict:
    """
    Runs the gitversion executable and returns a dictionary of values

    Example "gitversion" output::

        "Major":0,
        "Minor":4,
        "Patch":4,
        "PreReleaseTag":"dev.11",
        "PreReleaseTagWithDash":"-dev.11",
        "PreReleaseLabel":"dev",
        "PreReleaseNumber":11,
        "BuildMetaData":"",
        "BuildMetaDataPadded":"",
        "FullBuildMetaData":"Branch.develop.Sha.b22387288a19ac67641fac2711b940c4cab6d021",
        "MajorMinorPatch":"0.4.4",
        "SemVer":"0.4.4-dev.11",
        "LegacySemVer":"0.4.4-dev11",
        "LegacySemVerPadded":"0.4.4-dev0011",
        "AssemblySemVer":"0.4.4.0",
        "FullSemVer":"0.4.4-dev.11",
        "InformationalVersion":"0.4.4-dev.11+Branch.develop.Sha.b22387288a19ac67641fac2711b940c4cab6d021",
        "BranchName":"develop",
        "Sha":"b22387288a19ac67641fac2711b940c4cab6d021",
        "NuGetVersionV2":"0.4.4-dev0011",
        "NuGetVersion":"0.4.4-dev0011",
        "NuGetPreReleaseTagV2":"dev0011",
        "NuGetPreReleaseTag":"dev0011",
        "CommitsSinceVersionSource":11,
        "CommitsSinceVersionSourcePadded":"0011",
        "CommitDate":"2017-07-18"
    """
    # This is a potential security breach, but I'm leaving it as is as it should only be running either from a dev
    # machine or on Appveyor
    cmd = r'C:\ProgramData\chocolatey\bin\gitversion.exe' if os.environ.get('APPVEYOR') else 'gitversion'
    return loads(subprocess.getoutput([cmd]).rstrip())


if hasattr(sys, 'frozen'):
    from emft.__version_frozen__ import __version__ as frozen_version
    __version__ = frozen_version
else:
    try:
        gitversion = get_gitversion()
        __version__ = f'{gitversion["FullSemVer"]}'
    except JSONDecodeError:
        __version__ = 'ERROR'

try:
    if not __version__ == 'ERROR':
        CustomVersion.coerce(__version__)
except ValueError:
    raise RuntimeError(f'failed to coerce version: {__version__}')

__guid__ = '4ae6dbb7-5b26-43c6-b797-2272f5a074f3'

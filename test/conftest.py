# coding=utf-8
import os
import sys
import traceback
import warnings

import pytest

# noinspection PyUnresolvedReferences
import src.filter_warnings  # noqa: F401

# Fail on any non-ignored warning
warnings.filterwarnings('error', category=ResourceWarning, append=True)
warnings.filterwarnings('error', category=DeprecationWarning, append=True)
warnings.filterwarnings('error', category=SyntaxWarning, append=True)
warnings.filterwarnings('error', category=RuntimeWarning, append=True)
warnings.filterwarnings('error', category=FutureWarning, append=True)
warnings.filterwarnings('error', category=PendingDeprecationWarning, append=True)
warnings.filterwarnings('always', category=ImportWarning, append=True)
warnings.filterwarnings('error', category=UnicodeWarning, append=True)


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    # noinspection PyUnresolvedReferences
    del sys._called_from_test


@pytest.fixture(autouse=True)
def catch_exceptions_in_threads():
    yield
    from src.utils.threadpool import test_exc
    if test_exc:
        print(f'TRACEBACK:\n{"".join([x for x in traceback.format_tb(test_exc[2])])}')
        raise test_exc[0](test_exc[1])


@pytest.fixture(autouse=True)
def cleandir(request, tmpdir):
    if 'nocleandir' in request.keywords:
        yield
    else:
        current_dir = os.getcwd()
        os.chdir(str(tmpdir))
        yield os.getcwd()
        os.chdir(current_dir)


@pytest.fixture(autouse=True)
def reset_progress(request):
    if 'noresetprogress' in request.keywords:
        yield
    else:
        from src.utils.progress import Progress
        Progress.done()
        yield

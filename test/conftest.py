# coding=utf-8
import os

import pytest


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

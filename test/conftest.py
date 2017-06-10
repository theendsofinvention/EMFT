# coding=utf-8
import os

import pytest


@pytest.fixture()
def cleandir(tmpdir):
    current_dir = os.getcwd()
    os.chdir(str(tmpdir))
    yield os.getcwd()
    os.chdir(current_dir)

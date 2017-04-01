# coding=utf-8

import os

import pytest

if os.path.exists('./test_files'):
    BASE_PATH = './test_files'
elif os.path.exists('./test/test_files'):
    BASE_PATH = './test/test_files'
else:
    raise RuntimeError('cannot find test files')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def TEST_FILE():
    yield os.path.join(BASE_PATH, 'TRG_KA50.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def OUT_FILE():
    yield os.path.join(BASE_PATH, 'TRG_KA50_EMFT.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def BAD_ZIP_FILE():
    yield os.path.join(BASE_PATH, 'bad_zip_file.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def MISSING_FILE():
    yield os.path.join(BASE_PATH, 'missing_files.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def ALL_OBJECTS():
    yield os.path.join(BASE_PATH, 'all_objects.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def LARGE_FILE():
    yield os.path.join(BASE_PATH, 'TRMT_2.4.0.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def RADIO_FILE():
    yield os.path.join(BASE_PATH, 'radios.miz')


# noinspection PyPep8Naming
@pytest.fixture(scope='session')
def BAD_FILES():
    yield ['bad_zip_file.miz', 'missing_files.miz']

# coding=utf-8

import os

import pytest
import datadiff

from emft.sltp import SLTP, SLTPParsingError

if os.path.exists('./test_files'):
    BASE_PATH = os.path.abspath('./test_files/sltp')
elif os.path.exists('./test/test_files'):
    BASE_PATH = os.path.abspath('./test/test_files/sltp')
else:
    raise RuntimeError('cannot find test files')

TEST_FILES_DIR = os.path.join(BASE_PATH, 'pass')
TEST_FILES_DIR_FAIL = os.path.join(BASE_PATH, 'fail')
TEST_FILES_DIR_DIFF = os.path.join(BASE_PATH, 'diff')
TEST_FILES_DIR_LONG = os.path.join(BASE_PATH, 'long')

ENCODING = 'iso8859_15'


def _assert_same(input_, output):

    for x in input_:
        try:
            assert x in output
        except AssertionError:
            print(datadiff.diff(input_, output))
            raise

    assert len(input_) == len(output)


def _assert_different(input_, output):

    for x in input_:
        try:
            assert x in output
        except AssertionError:
            break
    else:
        pytest.fail('resulting dicts should be different')


def _do_test(test_file, compare_func):
    parser = SLTP()
    with open(test_file, encoding=ENCODING) as f:
        data = f.read()
    decoded_data, qualifier = parser.decode(data)

    parser = SLTP()
    encoded_data = parser.encode(decoded_data, qualifier)

    output = encoded_data.split('\n')
    input_ = data.split('\n')

    compare_func(input_, output)


@pytest.mark.parametrize('test_file', os.listdir(TEST_FILES_DIR))
def test_encode_decode_files(test_file):
    test_file = os.path.join(TEST_FILES_DIR, test_file)
    _do_test(test_file, _assert_same)


@pytest.mark.long
@pytest.mark.parametrize('test_file', os.listdir(TEST_FILES_DIR_LONG))
def test_encode_decode_files_long(test_file):
    test_file = os.path.join(TEST_FILES_DIR_LONG, test_file)
    _do_test(test_file, _assert_same)


@pytest.mark.parametrize('test_file', os.listdir(TEST_FILES_DIR_FAIL))
def test_encode_decode_files_fail(test_file):
    test_file = os.path.join(TEST_FILES_DIR_FAIL, test_file)
    with pytest.raises(SLTPParsingError):
        _do_test(test_file, _assert_same)


@pytest.mark.parametrize('test_file', os.listdir(TEST_FILES_DIR_DIFF))
def test_encode_decode_files_diff(test_file):
    test_file = os.path.join(TEST_FILES_DIR_DIFF, test_file)
    _do_test(test_file, _assert_different)

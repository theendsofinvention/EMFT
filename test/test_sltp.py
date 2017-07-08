# coding=utf-8

import os

import pytest

from src.sltp import SLTP

TEST_FILES_DIR = './test/test_files/sltp'
ENCODING = 'iso8859_15'


@pytest.mark.nocleandir
@pytest.mark.parametrize('test_file', os.listdir(TEST_FILES_DIR))
def test_encode_decode_files(test_file):
    test_file = os.path.join(TEST_FILES_DIR, test_file)
    parser = SLTP()
    with open(test_file, encoding=ENCODING) as f:
        data = f.read()
    decoded_data, qualifier = parser.decode(data)

    parser = SLTP()
    encoded_data = parser.encode(decoded_data, qualifier)

    output = encoded_data.split('\n')
    input_ = data.split('\n')

    for x in input_:
        try:
            assert x in output
        except AssertionError:
            print(x)
            raise

    assert len(input_) == len(output)

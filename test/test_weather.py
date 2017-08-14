# coding=utf-8

import json
import os

import pytest
from hypothesis import given, strategies as st

from emft.cli.weather import MissionWeather, _set_weather

if os.path.exists('./test_files'):
    BASE_PATH = os.path.abspath('./test_files')
elif os.path.exists('./test/test_files'):
    BASE_PATH = os.path.abspath('./test/test_files')
else:
    raise RuntimeError('cannot find test files')

TEST_FILE = os.path.join(BASE_PATH, 'weather.miz')
OUT_FILE = os.path.join(BASE_PATH, 'weather_output.miz')


@given(heading=st.integers(min_value=0, max_value=359))
def test_reverse_direction(heading):
    val = MissionWeather._reverse_direction(heading)
    assert 1 <= val <= 359
    assert val == heading - 180 or val == heading + 180
    assert type(val) is int


@given(heading=st.integers(min_value=-2000, max_value=2000))
def test_normalize_direction(heading):
    val = MissionWeather._normalize_direction(heading)
    assert 0 <= val <= 359
    assert type(val) is int


@given(base_speed=st.integers(min_value=0, max_value=40))
def test_deviate_wind_speed(base_speed):
    val = MissionWeather._deviate_wind_speed(base_speed)
    assert 0 <= val <= 80
    assert type(val) is int


@pytest.mark.parametrize('icao', ['UGTB', 'UGTO', 'UGKO', 'UGSA', 'UGDT', 'URSS'])
def test_set_weather(icao):
    result = _set_weather(icao, TEST_FILE, OUT_FILE)
    assert isinstance(result, str)
    result = json.loads(result)
    assert isinstance(result, dict)
    assert result['status'] == 'success'
    assert result['icao'] == icao
    assert result['from'] == TEST_FILE
    assert result['to'] == OUT_FILE

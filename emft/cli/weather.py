# coding=utf-8

import json

import click
import requests

from emft.core.logging import make_logger
from emft.miz.mission_weather import Metar, MissionWeather

# DEBUG CODE
# with open('./test/test_files/icaos.txt') as handle:
#     list_of_stations = [icao.strip() for icao in handle.readlines()]

# Ref: http://en.wiki.eagle.ru/wiki/Mission_Editor:_Weather_Modelling

BASE_TAF_URL = r'http://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{station}.TXT'
BASE_METAR_URL = r'http://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT'

LOGGER = make_logger(__name__)


def _retrieve_taf(station_icao):
    url = BASE_TAF_URL.format(station=station_icao)
    with requests.get(url) as resp:
        if not resp.ok:
            raise FileNotFoundError(f'unable to obtain TAF for station {station_icao} from url: {url}')
        return '\n'.join(resp.content.decode().split('\n')[1:])


def _retrieve_metar(station_icao):
    url = BASE_METAR_URL.format(station=station_icao)
    with requests.get(url) as resp:
        if not resp.ok:
            raise FileNotFoundError(f'unable to obtain METAR for station {station_icao} from url: {url}')
        return resp.content.decode().split('\n')[1]


def _set_weather(station_icao, in_file, out_file):
    LOGGER.debug(f'getting METAR for {station_icao}')
    result = {
        'icao': station_icao,
        'from': in_file,
        'to': out_file,
    }
    try:
        metar_str = _retrieve_metar(station_icao)
    except FileNotFoundError:
        result['status'] = 'failed'
        result['error'] = f'unable to obtain METAR for station {station_icao}\n'
        f'Got to "http://tgftp.nws.noaa.gov/data/observations/metar/stations" for a list of valid stations'
    else:
        result['metar'] = metar_str
        try:
            metar = Metar(metar_str)
        except:
            LOGGER.error('Failed to parse METAR string. This is a bug in the METAR library, I will take a look ASAP')
            result['status'] = 'failed'
        else:
            LOGGER.debug(f'METAR: {metar.code}')
            LOGGER.debug(f'applying metar: {in_file} -> {out_file}')
            try:
                if MissionWeather(metar).apply_to_miz(in_file, out_file):
                    result['status'] = 'success'
            except ValueError:
                result['status'] = 'failed'
                result['error'] = f'Unable to apply METAR string to the mission.\n'
                f'This is most likely due to a freak value, this feature is still experimental.\n'
                f'I will fix it ASAP !'

    return json.dumps(result)


@click.command(help='test')
@click.option('-s', '--station-icao', help='Station ICAO code', type=str, required=True)
@click.option('-i', '--in-file', help='Mission file to update', required=True,
              type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('-o', '--out-file', help='Mission file to write (defaults to same file)', required=False,
              type=click.Path(dir_okay=False, writable=True))
def set_weather(station_icao, in_file, out_file):
    click.secho(_set_weather(station_icao, in_file, out_file))

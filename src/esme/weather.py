# coding=utf-8
from re import compile as re_compile, MULTILINE as re_MULTILINE

from bs4 import BeautifulSoup
from metar.metar import Metar
from pytaf import TAF, Decoder
from requests import get as request_get

# from ui.ui_globals import main_window
re_rem1 = re_compile('''[0-9]{6}/ ''')
re_rem2 = re_compile('''R[0-9]{2}([RL])?/[^ ]*''')
valid_airports_by_icao_code = {
    'UGKO': 'Kutaisi',
    'UGSB': 'Batumi',
    'UGSS': 'Sukhumi',
    'UGTB': 'Tbilisi',
    'URMM': 'Mineralnyye Vody',
    'URMN': 'Nalchik',
    'URKA': 'Anapa',
    'URKG': 'Gelendzhik',
    'URKK': 'Krasnodar',
    'URSS': 'Sochi',
    'URKM': 'Maykop',
}

valid_airport_by_name = dict(zip(valid_airports_by_icao_code.values(), valid_airports_by_icao_code.keys()))


class WeatherError:
    class BaseWeatherError(Exception):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class UnknownAirportError(BaseWeatherError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg


def get_metar_of(station):
    station = station.upper()
    if station not in valid_airports_by_icao_code.keys():
        raise WeatherError.UnknownAirportError(station)
    url = "http://weather.noaa.gov/pub/data/observations/metar/stations/{}.TXT".format(station.upper())
    try:
        urlh = request_get(url).content.decode('utf8')
        for line in urlh.split('\n'):
            if line.startswith(station):
                return line.strip()
    except:
        raise WeatherError.BaseWeatherError('error while retrieveing METAR for {}'.format(station))


class Weather():
    def __init__(self):
        self._parsed = False

    def retrieve_online_metar(self, location):
        print(location)
        # html = request_get('http://www.acukwik.com/AirportInfo/{}'.format(location)).content.decode('utf8')
        html = request_get(
            'https://www.aviationweather.gov/adds/tafs?station_ids={}&std_trans=standard&submit_taf=Get+TAFs'.format(
                location.lower())).content.decode('utf8')
        soup = BeautifulSoup(html, 'html.parser')
        taf_string = soup.find('font')
        if taf_string is None:
            print('nope')
            return
        taf_string = taf_string.string
        taf = TAF(taf_string)
        decoder = Decoder(taf)
        print(decoder.decode_taf())
        return
        # # print(html)
        # re_taf_line = re_compile(
        #     r'.*LATEST TAF REPORT FOR {}\s+(?P<taf>.*)\s+LATEST TAF REPORT FOR {}.*'.format(location, location),
        #     re_MULTILINE)
        # m = re_taf_line.match(html)
        # if m:
        #     taf = m.group('taf')
        #     print(taf)
        #     return
        #     metar_string = m.group('metar')
        #     metar_string = re.sub(re_rem1, '', metar_string)
        #     metar_string = re.sub(re_rem2, '', metar_string)
        #     self.__parse_metar_string(metar_string)
        #     # TODO: add check for failure

    def __parse_metar_string(self, metar_string):
        self.metar = Metar(metar_string)
        self.wind_speed = int(self.metar.wind_speed.value("MPS"))
        self.wind_dir = int(self.metar.wind_dir.value())
        self.visibility = int(self.metar.vis.value())
        # cloud base: 300-5000
        # cloud thickness: 200-2000
        if self.metar.sky:
            cloud_coverage = self.metar.sky[0][0]
            if self.metar.sky[0][1]:
                self.cloud_alti = int(self.metar.sky[0][1].value("M"))
            else:
                self.cloud_alti = 300
            if cloud_coverage == "FEW":
                self.clouds = 2
                self.cloud_thickness = 500
            elif cloud_coverage == "SCT":
                self.clouds = 4
                self.cloud_thickness = 1000
            elif cloud_coverage == "BKN":
                self.clouds = 6
                self.cloud_thickness = 1500
            elif cloud_coverage == "OCT":
                self.clouds = 8
                self.cloud_thickness = 2000
        else:
            self.clouds = 0
            self.cloud_alti = 300
        self.pres_hg = int(self.metar.press.value('MMHG'))
        self.pres_mb = int(self.metar.press.value('MB'))
        self.temp = int(self.metar.temp.value('C'))
        self.dew_point = int(self.metar.dewpt.value('C'))
        self.update_time = self.metar.time
        self._parsed = True

    def __str__(self):
        if not self._parsed:
            print("No METAR parsed yet")
            # TODO: add exception here for ealry access to data
        s = [
            "Update time: {}Z".format(self.update_time),
            "Temp: {}".format(self.temp),
            "Dew point: {}".format(self.dew_point),
            "wind_speed: {}".format(self.wind_speed),
            "wind_dir: {}".format(self.wind_dir),
            "visibility: {}".format(self.visibility),
            "clouds: {}".format(self.clouds),
            "cloud_alti: {}".format(self.cloud_alti),
            "pres_hg: {}".format(self.pres_hg),
            "pres_mb: {}".format(self.pres_mb),
        ]
        return "\n".join(s)


if __name__ == '__main__':
    metar_str = get_metar_of('UGKO')
    metar = Metar(metar_str)
    print(metar.wind_dir)
    print(metar.wind_dir_from)
    print(metar.wind_dir_to)
    print(metar.wind_speed)
    print(metar.wind_gust)
    print(metar.max_vis)
    print(metar.temp)
    print(metar.mod)
    print(metar.press.value('IN'))
    print(metar.press.value('HPA'))
    print(metar.press.value('MMHG'))
    print(metar.runway)
    print(metar.type)
    print(metar.time)
    print(metar.weather)
    print(metar.vis)
    print(metar.visibility('m'))
    print(metar.sky)
    print(metar.sky_conditions())
    w = Weather()
    for k in valid_airport_by_name.keys():
        print(k)
        w.retrieve_online_metar(valid_airport_by_name[k])
        # print(w)

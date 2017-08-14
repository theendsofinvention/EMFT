# coding=utf-8

import random
from datetime import date, datetime

from metar.Metar import Metar

from emft.core.logging import make_logger
from .miz import Miz

LOGGER = make_logger(__name__)

SKY_COVER = {"SKC": (0, 0),
             "CLR": (0, 0),
             "NSC": (0, 0),
             "NCD": (0, 0),
             "FEW": (1, 3),
             "SCT": (4, 6),
             "BKN": (7, 8),
             "OVC": (9, 10),
             "///": (0, 0),
             "VV": (0, 0)
             }

Y = 2000

SEASONS = [
    ('winter', 5, (date(Y, 1, 1), date(Y, 3, 20))),
    ('spring', 10, (date(Y, 3, 21), date(Y, 6, 20))),
    ('summer', 20, (date(Y, 6, 21), date(Y, 9, 22))),
    ('autumn', 10, (date(Y, 9, 23), date(Y, 12, 20))),
    ('winter', 5, (date(Y, 12, 21), date(Y, 12, 31))),
]

def _get_season():
    now = datetime.now().date().replace(year=Y)
    return next((season, temp) for season, temp, (start, end) in SEASONS if start <= now <= end)

def _hpa_to_mmhg(pressure) -> int:
    return int(pressure * 0.75006156130264)


class MissionWeather:
    def __init__(self,
                 metar: Metar,
                 min_wind: int = 0,
                 max_wind: int = 40,
                 ):
        self.metar = metar
        self.wind_dir = None
        self.wind_speed = None
        self._min_wind = min_wind
        self._max_wind = max_wind
        self.fog_vis = None
        self.precip = 0
        self.cloud_density = 0
        self.cloud_base = 300
        self.cloud_thickness = 200
        self.force_cloud_density = 0
        self.force_temperature = 999
        self._parse_precip()
        self._parse_clouds()

    @staticmethod
    def _random_direction() -> int:
        return random.randint(0, 359)

    @staticmethod
    def _reverse_direction(heading) -> int:
        if heading >= 180:
            return int(heading - 180)
        else:
            return int(heading + 180)

    @staticmethod
    def _normalize_direction(heading) -> int:
        while heading > 359:
            heading = int(heading - 359)
        while heading < 0:
            heading = int(heading + 359)
        return heading

    @staticmethod
    def _gauss(mean, sigma) -> int:
        return int(random.gauss(mean, sigma))

    @staticmethod
    def _deviate_wind_speed(base_speed, sigma=None) -> int:
        if sigma is None:
            sigma = base_speed / 4
        val = MissionWeather._gauss(base_speed, sigma)
        if val < 0:
            return 0
        return val

    @staticmethod
    def _deviate_direction(base_heading, sigma) -> int:
        val = MissionWeather._gauss(base_heading, sigma)
        val = MissionWeather._normalize_direction(val)
        return val

    @property
    def wind_at_ground_level_dir(self) -> int:
        if self.metar.wind_dir is None:
            LOGGER.info('wind is variable, making a random value')
            val = self._random_direction()
        else:
            val = self._reverse_direction(self.metar.wind_dir.value())
        self.wind_dir = val
        return val

    @property
    def wind_at_ground_level_speed(self) -> int:
        if self.metar.wind_speed is None:
            LOGGER.info('wind speed is missing, making a random value')
            val = random.randint(self._min_wind, self._max_wind)
        else:
            val = int(self.metar.wind_speed.value('MPS'))
        self.wind_speed = val
        return val

    @property
    def qnh(self) -> int:
        if self.metar.press is None:
            LOGGER.info('QNH is missing, returning standard QNH')
            return 760
        return _hpa_to_mmhg(self.metar.press.value())

    @property
    def visibility(self) -> int:
        if self.metar.vis is None:
            LOGGER.debug('visibility is missing, returning maximum')
            return 800000
        val = int(self.metar.vis.value())
        if val < 10000:
            self.fog_vis = min(6000, val)
        return val

    def _parse_precip(self):
        if 'rain' in self.metar.present_weather():
            self.precip = 1
            self.force_cloud_density = 5
        if 'snow' in self.metar.present_weather():
            self.precip = 3
            self.force_cloud_density = 5
            self.force_temperature = 0
        if 'storm' in self.metar.present_weather():
            if self.precip == 2:
                self.precip = 4
            else:
                self.precip = 3
            self.force_cloud_density = 9

    def _parse_clouds(self):
        base = 0
        ceiling = 999999
        layers = {}
        for skyi in self.metar.sky:
            cover, height, _ = skyi
            height = int(height.value('M'))
            base = min(base, height)
            ceiling = max(ceiling, height)
            cover = random.randint(*SKY_COVER[cover])
            layers[cover] = height
        if layers:
            max_cover = max([key for key in layers])
            self.cloud_density = max_cover
            self.cloud_base = layers[max_cover]
            self.cloud_thickness = max(min(200, ceiling - base), 2000)

    @property
    def temperature(self):
        if self.metar.temp is None:
            season, temp = _get_season()
            LOGGER.debug(f'no temperature given, since it is {season}, defaulting to {temp}')
            return temp
        return int(self.metar.temp.value('C'))

    @property
    def turbulence(self) -> int:
        if self.metar.wind_gust is None:
            return 0
        val = int(self.metar.wind_gust.value('MPS'))
        if self.wind_speed >= val:
            return 0
        return int(min((val - self.wind_speed) * 10, 60))


    def apply_to_miz(self, infile: str, outfile: str = None):

        # TESTING CODE
        # import shutil
        # with Miz('./test/test_files/weather.miz') as miz:
        #     miz._encode()
        #     shutil.copy(miz.mission_file, './test/test_files/weather/mission')

        if outfile is None:
            outfile = infile

        with Miz(infile) as miz:
            miz.mission.weather.wind_at_ground_level_dir = self.wind_at_ground_level_dir
            miz.mission.weather.wind_at_ground_level_speed = self.wind_at_ground_level_speed
            miz.mission.weather.wind_at2000_dir = self._deviate_direction(self.wind_dir, 40)
            miz.mission.weather.wind_at2000_speed = self._deviate_wind_speed(5 + self.wind_speed * 2)
            miz.mission.weather.wind_at8000_dir = self._deviate_direction(self.wind_dir, 80)
            miz.mission.weather.wind_at8000_speed = self._deviate_wind_speed(10 + self.wind_speed * 3)
            miz.mission.weather.turbulence_at_ground_level = self.turbulence

            miz.mission.weather.atmosphere_type = 0
            miz.mission.weather.qnh = self.qnh

            miz.mission.weather.visibility = self.visibility
            miz.mission.weather.fog_thickness = 1000
            if self.fog_vis:
                miz.mission.weather.fog_visibility = self.fog_vis
                miz.mission.weather.fog_enabled = True

            miz.mission.weather.cloud_density = max(self.force_cloud_density, self.cloud_density)
            miz.mission.weather.cloud_thickness = self.cloud_thickness
            miz.mission.weather.cloud_base = self.cloud_base
            miz.mission.weather.precipitations = self.precip

            miz.mission.weather.temperature = self.temperature

            miz.zip(outfile)

            return True

            # TESTING CODE
            # miz._encode()
            # shutil.copy(miz.mission_file, './test/test_files/weather_output/mission')
            # miz.zip('./test/test_files/weather_output.miz')
            # # miz.zip('./test/test_files/weather_output.miz')

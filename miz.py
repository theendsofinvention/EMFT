# coding=utf-8
# Whole imports
# Specific imports
from collections import OrderedDict
from os import walk, remove, rmdir
from os.path import exists, abspath, join
from re import compile as re_compile, sub as re_sub
from time import gmtime, strftime, strptime
from zipfile import ZipFile, BadZipFile, ZipInfo
from itertools import chain
# Own imports
# from ui.globals import
from slpp.slpp import SLPP
from custom_logging.custom_logging import make_logger, Logged
from base_utils.base_utils import BaseUtils
# noinspection PyUnresolvedReferences - keep it ! inverse of gmtime =)
from calendar import timegm
from validator import validator
from validator.validator import Validator
# from validator.validator import Validator, StandardValidators

RE_SPACE_AFTER_EQUAL_SIGN = re_compile("=\n")

LOGGER = make_logger('miz')

EPOCH_DELTA = 1306886400


class MizErrors:
    class BaseMizError(Exception):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class MizFileNotFoundError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class CorruptedMizError(BaseMizError):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class ExtractError(BaseMizError):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class MissingFileInMizError(BaseMizError):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class InvalidParameterError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class PrecipitationsErrors(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class DuplicateGroupIdError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class DuplicateUnitIdError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class CountryNotFoundError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class InvalidGroupStartTimeError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class NoRadioPresetsError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class InvalidChannelError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class InvalidFrequencyError(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg

    class InvalidRadioForThisAircraft(BaseMizError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)
            self.msg = msg


class AbstractMissionObject(Logged):
    def __init__(self, mission_dict, ln10):
        super().__init__()
        assert isinstance(mission_dict, OrderedDict)
        self.d = mission_dict
        self.ln10 = ln10
        self.weather = None
        self.blue_coa = None
        self.red_coa = None
        self.ground_control = None
        self._countries_by_name = {}
        self._countries_by_id = {}

    @property
    def next_group_id(self):
        ids = set()
        for group in chain(self.blue_coa.groups, self.red_coa.groups):
            assert isinstance(group, Group)
            id = group.group_id
            if id in ids:
                raise MizErrors.DuplicateGroupIdError(group.group_name)
            ids.add(id)
        return max(ids) + 1

    @property
    def next_unit_id(self):
        ids = set()
        for unit in chain(self.blue_coa.units, self.red_coa.units):
            assert isinstance(unit, AbstractUnit)
            id = unit.unit_id
            if id in ids:
                raise MizErrors.DuplicateUnitIdError(unit.unit_name)
            ids.add(id)
        return max(ids) + 1

    @property
    def coalitions(self):
        for coalition in [self.blue_coa, self.red_coa]:
            assert isinstance(coalition, Coalition)
            yield coalition

    @property
    def countries(self):
        for coalition in self.coalitions:
            for country in coalition.countries:
                assert isinstance(country, Country)
                yield country

    def get_country_by_name(self, country_name):
        validator.str.validate(country_name, 'get_country_by_name')
        if country_name not in self._countries_by_name.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_name == country_name:
                    self._countries_by_name[country_name] = country
                    return country
            raise MizErrors.CountryNotFoundError(country_name)
        else:
            return self._countries_by_name[country_name]

    def get_country_by_id(self, country_id):
        validator.positive_integer.validate(country_id, 'get_country_by_id')
        if country_id not in self._countries_by_id.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_id == country_id:
                    self._countries_by_id[country_id] = country
                    return country
            raise MizErrors.CountryNotFoundError(country_id)
        else:
            return self._countries_by_id[country_id]

    @property
    def groups(self):
        for country in self.countries:
            for group in country.groups:
                assert isinstance(group, Group)
                yield group

    def get_groups_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_groups_from_category')
        for group in self.groups:
            if group.group_category == category:
                yield group

    @property
    def units(self):
        for group in self.groups:
            for unit in group.units:
                assert isinstance(unit, AbstractUnit)
                yield unit

    def get_units_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_units_from_category')
        for unit in self.units:
            if unit.group_category == category:
                yield unit

    def get_group_by_id(self, group_id):
        validator.positive_integer.validate(group_id, 'get_group_by_id')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_id == group_id:
                return group
        return None

    def get_group_by_name(self, group_name):
        validator.str.validate(group_name, 'get_group_by_name')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_name == group_name:
                return group
        return None

    def get_unit_by_name(self, unit_name):
        validator.str.validate(unit_name, 'get_unit_by_name')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        validator.positive_integer.validate(unit_id, 'get_unit_by_id')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    @property
    def mission_start_time(self):
        return self.d['start_time']

    @mission_start_time.setter
    def mission_start_time(self, value):
        Mission.validator_start_time.validate(value, 'start_time')
        self.d['start_time'] = value

    @property
    def mission_start_time_as_date(self):
        return strftime('%d/%m/%Y %H:%M:%S', gmtime(EPOCH_DELTA + self.mission_start_time))

    @mission_start_time_as_date.setter
    def mission_start_time_as_date(self, value):
        Mission.validator_start_date.validate(value, 'start_time_as_date')
        self.mission_start_time = timegm(strptime(value, '%d/%m/%Y %H:%M:%S')) - EPOCH_DELTA

    @property
    def _sortie_name_key(self):
        return self.d['sortie']

    @property
    def sortie_name(self):
        return self.ln10[self._sortie_name_key]

    @sortie_name.setter
    def sortie_name(self, value):
        validator.str.validate(value, 'sortie name')
        self.ln10[self._sortie_name_key] = value


class Mission(AbstractMissionObject):
    validator_start_time = Validator(_type=int, _min=0, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_start_date = Validator(_type=str,
                                     _regex=r'^(?=\d)(?:(?:31(?!.(?:0?[2469]|11))|(?:30|29)(?!.0?2)|29(?=.0?2.(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00)))(?:\x20|$))|(?:2[0-8]|1\d|0?[1-9]))([-./])(?:1[012]|0?[1-9])\1(?:1[6-9]|[2-9]\d)?\d\d(?:(?=\x20\d)\x20|$))?(((0?[1-9]|1[012])(:[0-5]\d){0,2}(\x20[AP]M))|([01]\d|2[0-3])(:[0-5]\d){1,2})?$', exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_heading = Validator(_type=int, _min=0, _max=359, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_group_category = Validator(_type=str, _in_list=['helicopter', 'ship', 'plane', 'vehicle'], exc=MizErrors.InvalidParameterError, logger=LOGGER)
    valid_group_categories = ('helicopter', 'plane', 'ship', 'vehicle')

    def __init__(self, mission_dict, ln10):
        super().__init__(mission_dict, ln10)
        self.weather = Weather(self.d, ln10)
        self.blue_coa = Coalition(self.d, ln10, 'blue')
        self.red_coa = Coalition(self.d, ln10, 'red')
        self.ground_control = GroundControl(self.d, ln10)

    def __repr__(self):
        return 'Mission({})'.format(self.d)


class Trig(AbstractMissionObject):
    def __init__(self, mission_dict, ln10):
        super().__init__(mission_dict, ln10)

    @property
    def _section_trig(self):
        return self.d['trig']


class Result(AbstractMissionObject):
    def __init__(self, mission_dict, ln10):
        super().__init__(mission_dict, ln10)

    @property
    def _section_result(self):
        return self.d['result']


class GroundControl(AbstractMissionObject):
    validator_commander = Validator(_type=int, _min=0, _max=100, exc=MizErrors.InvalidParameterError, logger=LOGGER)

    def __init__(self, mission_dict, ln10):
        super().__init__(mission_dict, ln10)

    def __repr__(self):
        return 'GroundControl({})'.format(self._section_ground_control)

    @property
    def _section_ground_control(self):
        return self.d['groundControl']

    @property
    def _section_ground_control_roles(self):
        return self.d['groundControl']['roles']

    @property
    def pilots_control_vehicles(self):
        return self._section_ground_control['isPilotControlVehicles']

    @pilots_control_vehicles.setter
    def pilots_control_vehicles(self, value):
        validator.bool.validate(value, 'pilots_control_vehicles')
        self._section_ground_control['isPilotControlVehicles'] = value

    @property
    def _section_artillery_commander(self):
        return self._section_ground_control_roles['artillery_commander']

    @property
    def artillery_commander_red(self):
        return self._section_artillery_commander['red']

    @artillery_commander_red.setter
    def artillery_commander_red(self, value):
        self.validator_commander.validate(value, 'artillery_commander_red')
        self._section_artillery_commander['red'] = value

    @property
    def instructor_blue(self):
        return self._section_instructor['blue']

    @instructor_blue.setter
    def instructor_blue(self, value):
        self.validator_commander.validate(value, 'instructor_blue')
        self._section_instructor['blue'] = value

    @property
    def instructor_red(self):
        return self._section_instructor['red']

    @instructor_red.setter
    def instructor_red(self, value):
        self.validator_commander.validate(value, 'instructor_red')
        self._section_instructor['red'] = value

    @property
    def _section_observer(self):
        return self._section_ground_control_roles['observer']

    @property
    def observer_blue(self):
        return self._section_observer['blue']

    @observer_blue.setter
    def observer_blue(self, value):
        self.validator_commander.validate(value, 'observer_blue')
        self._section_observer['blue'] = value

    @property
    def observer_red(self):
        return self._section_observer['red']

    @observer_red.setter
    def observer_red(self, value):
        self.validator_commander.validate(value, 'observer_red')
        self._section_observer['red'] = value

    @property
    def _section_forward_observer(self):
        return self._section_ground_control_roles['forward_observer']

    @property
    def forward_observer_blue(self):
        return self._section_forward_observer['blue']

    @forward_observer_blue.setter
    def forward_observer_blue(self, value):
        self.validator_commander.validate(value, 'forward_observer_blue')
        self._section_forward_observer['blue'] = value

    @property
    def forward_observer_red(self):
        return self._section_forward_observer['red']

    @forward_observer_red.setter
    def forward_observer_red(self, value):
        self.validator_commander.validate(value, 'forward_observer_red')
        self._section_forward_observer['red'] = value

    @property
    def artillery_commander_blue(self):
        return self._section_artillery_commander['blue']

    @artillery_commander_blue.setter
    def artillery_commander_blue(self, value):
        self.validator_commander.validate(value, 'artillery_commander_blue')
        self._section_artillery_commander['blue'] = value

    @property
    def _section_instructor(self):
        return self._section_ground_control_roles['instructor']


class Weather(AbstractMissionObject):
    validator_precipitations = Validator(_type=int, _min=0, _max=4, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_cloud_density = Validator(_type=int, _min=0, _max=10, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_cloud_thickness = Validator(_type=int, _min=200, _max=2000, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_cloud_base = Validator(_type=int, _min=300, _max=5000, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_fog_visibility = Validator(_type=int, _min=0, _max=6000, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_fog_thickness = Validator(_type=int, _min=0, _max=1000, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_qnh = Validator(_type=int, _min=720, _max=790, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_temp_spring_or_fall = Validator(_type=int, _min=-10, _max=30, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_temp_winter = Validator(_type=int, _min=-50, _max=15, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_temp_summer = Validator(_type=int, _min=5, _max=50, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    seasons_enum = {
        1       : {
            'name'          : 'summer',
            'temp_validator': validator_temp_summer,
        },
        2       : {
            'name'          : 'winter',
            'temp_validator': validator_temp_winter,
        },
        3       : {
            'name'          : 'spring',
            'temp_validator': validator_temp_spring_or_fall,
        },
        4       : {
            'name'          : 'fall',
            'temp_validator': validator_temp_spring_or_fall,
        },
        'summer': 1,
        'winter': 2,
        'spring': 3,
        'fall'  : 4,
    }
    validator_season_name = Validator(_type=str, _in_list=['summer', 'winter', 'fall', 'spring'], exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_season_code = Validator(_type=int, _min=1, _max=4, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_turbulence = Validator(_type=int, _min=0, _max=60, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_atmo_type = Validator(_type=int, _min=0, _max=1, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_wind_speed = Validator(_type=int, _min=0, _max=50, exc=MizErrors.InvalidParameterError, logger=LOGGER)

    def __init__(self, mission_dict, ln10):
        super().__init__(mission_dict, ln10)

    def __repr__(self):
        return 'Weather({})'.format(self._section_weather)

    def __eq__(self, other):
        if not isinstance(other, Weather):
            raise MizErrors.InvalidParameterError('"other" must be an Weather instance; got: {}'.format(type(other)))
        return self._section_weather == other._section_weather

    def get_season_code_from_name(self, season_name):
        self.validator_season_name.validate(season_name, 'get_season_code_from_name')
        return self.seasons_enum[season_name]

    @property
    def _section_fog(self):
        return self._section_weather['fog']

    @property
    def fog_thickness(self):
        return self._section_fog['thickness']

    @fog_thickness.setter
    def fog_thickness(self, value):
        self.validator_fog_thickness.validate(value, 'fog_thickness')
        self._section_fog['thickness'] = value

    @property
    def turbulence_at2000(self):
        return self._section_turbulence['at2000']

    @turbulence_at2000.setter
    def turbulence_at2000(self, value):
        self.validator_turbulence.validate(value, 'turbulence_at2000')
        self._section_turbulence['at2000'] = value

    @property
    def turbulence_at8000(self):
        return self._section_turbulence['at8000']

    @turbulence_at8000.setter
    def turbulence_at8000(self, value):
        self.validator_turbulence.validate(value, 'turbulence_at8000')
        self._section_turbulence['at8000'] = value

    @property
    def _section_wind_at_ground_level(self):
        return self._section_wind['atGround']

    @property
    def turbulence_at_ground_level(self):
        return self._section_turbulence['atGround']

    @turbulence_at_ground_level.setter
    def turbulence_at_ground_level(self, value):
        self.validator_turbulence.validate(value, 'turbulence_at_ground_level')
        self._section_turbulence['atGround'] = value

    @property
    def wind_at_ground_level_speed(self):
        return self._section_wind_at_ground_level['speed']

    @wind_at_ground_level_speed.setter
    def wind_at_ground_level_speed(self, value):
        self.validator_wind_speed.validate(value, 'wind_at_ground_level_speed')
        self._section_wind_at_ground_level['speed'] = value

    @property
    def fog_visibility(self):
        return self._section_fog['visibility']

    @fog_visibility.setter
    def fog_visibility(self, value):
        self.validator_fog_visibility.validate(value, 'fog_visibility')
        self._section_fog['visibility'] = value

    @property
    def precipitations(self):
        return self._section_clouds['iprecptns']

    @precipitations.setter
    def precipitations(self, value):
        self.validator_precipitations.validate(value, 'precipitations')
        if value > 0 and self.cloud_density <= 4:
            raise MizErrors.PrecipitationsErrors('No rain or snow if cloud density is less than 5')
        if value in [2, 4] and self.cloud_density <= 8:
            raise MizErrors.PrecipitationsErrors('No thunderstorm or snowstorm if cloud density is less than 9')
        if value > 2 and self.temperature > 0:
            raise MizErrors.PrecipitationsErrors('No snow with temperature over 0; use rain or thunderstorm instead')
        if value in [1, 2] and self.temperature < 0:
            raise MizErrors.PrecipitationsErrors('No rain or thunderstorm if temperature is below 0; use snow or snowstorm instead')
        self._section_clouds['iprecptns'] = value

    @property
    def wind_at8000_dir(self):
        return self._section_wind_at8000['speed']

    @wind_at8000_dir.setter
    def wind_at8000_dir(self, value):
        Mission.validator_heading.validate(value, 'wind_at8000_dir')
        self._section_wind_at8000['dir'] = value

    @property
    def _section_weather(self):
        return self.d['weather']

    @property
    def temperature(self):
        return self._section_season['temperature']

    @temperature.setter
    def temperature(self, value):
        self.seasons_enum[self.season_code]['temp_validator'].validate(value, 'temperature')
        self._section_season['temperature'] = value
        if value > 0 and self.precipitations > 2:
            self.precipitations -= 2
        if value < 0 < self.precipitations < 3:  # PyKek
            self.precipitations += 2

    @property
    def _section_wind_at8000(self):
        return self._section_wind['at8000']

    @property
    def wind_at_ground_level_dir(self):
        return self._section_wind_at_ground_level['dir']

    @wind_at_ground_level_dir.setter
    def wind_at_ground_level_dir(self, value):
        Mission.validator_heading.validate(value, 'wind_at_ground_level_dir')
        self._section_wind_at_ground_level['dir'] = value

    @property
    def _section_clouds(self):
        return self._section_weather['clouds']

    @property
    def cloud_thickness(self):
        return self._section_clouds['thickness']

    @cloud_thickness.setter
    def cloud_thickness(self, value):
        self.validator_cloud_thickness.validate(value, 'cloud_thickness')
        self._section_clouds['thickness'] = value

    @property
    def fog_enabled(self):
        return self._section_weather['enable_fog']

    @fog_enabled.setter
    def fog_enabled(self, value):
        validator.bool.validate(value, 'enable_fog')
        self._section_weather['enable_fog'] = value

    @property
    def _section_wind(self):
        return self._section_weather['wind']

    @property
    def _section_wind_at2000(self):
        return self._section_wind['at2000']

    @property
    def season_name(self):
        return self.seasons_enum[self.season_code]['name']

    @property
    def _section_turbulence(self):
        return self._section_weather['turbulence']

    @property
    def qnh(self):
        return self._section_weather['qnh']

    @qnh.setter
    def qnh(self, value):
        self.validator_qnh.validate(value, 'qnh')
        self._section_weather['qnh'] = value

    @property
    def wind_at2000_speed(self):
        return self._section_wind_at2000['speed']

    @wind_at2000_speed.setter
    def wind_at2000_speed(self, value):
        self.validator_wind_speed.validate(value, 'wind_at2000_speed')
        self._section_wind_at2000['speed'] = value

    @property
    def wind_at2000_dir(self):
        return self._section_wind_at2000['dir']

    @wind_at2000_dir.setter
    def wind_at2000_dir(self, value):
        Mission.validator_heading.validate(value, 'wind_at2000_dir')
        self._section_wind_at2000['dir'] = value

    @property
    def cloud_density(self):
        return self._section_clouds['density']

    @cloud_density.setter
    def cloud_density(self, value):
        self.validator_cloud_density.validate(value, 'cloud_density')
        self._section_clouds['density'] = value

    @property
    def _section_season(self):
        return self._section_weather['season']

    @property
    def atmosphere_type(self):
        return self._section_weather['atmosphere_type']

    @atmosphere_type.setter
    def atmosphere_type(self, value):
        self.validator_atmo_type.validate(value, 'atmosphere_type')
        self._section_weather['atmosphere_type'] = value

    @property
    def season_code(self):
        return self._section_season['iseason']

    @season_code.setter
    def season_code(self, value):
        self.validator_season_code.validate(value, 'season')
        self._section_season['iseason'] = value
        if self.temperature < self.seasons_enum[value]['temp_validator'].min:
            self.temperature = self.seasons_enum[value]['temp_validator'].min
        if self.temperature > self.seasons_enum[value]['temp_validator'].max:
            self.temperature = self.seasons_enum[value]['temp_validator'].max

    @property
    def cloud_base(self):
        return self._section_clouds['base']

    @cloud_base.setter
    def cloud_base(self, value):
        self.validator_cloud_base.validate(value, 'cloud_base')
        self._section_clouds['base'] = value

    @property
    def wind_at8000_speed(self):
        return self._section_wind_at8000['speed']

    @wind_at8000_speed.setter
    def wind_at8000_speed(self, value):
        self.validator_wind_speed.validate(value, 'wind_at8000_speed')
        self._section_wind_at8000['speed'] = value


class Coalition(AbstractMissionObject):
    def __init__(self, mission_dict, ln10, coa_color):
        super().__init__(mission_dict, ln10)
        self.coa_color = coa_color
        self._countries = {}

    def __repr__(self):
        return 'Coalition({}, {})'.format(self._section_coalition, self.coa_color)

    def __eq__(self, other):
        if not isinstance(other, Coalition):
            raise MizErrors.InvalidParameterError('"other" must be an Coalition instance; got: {}'.format(type(other)))
        return self._section_coalition == other._section_coalition

    @property
    def _section_coalition(self):
        return self.d['coalition'][self.coa_color]

    @property
    def _section_bullseye(self):
        return self._section_coalition['bullseye']

    @property
    def bullseye_x(self):
        return self._section_bullseye['x']

    @property
    def bullseye_y(self):
        return self._section_bullseye['y']

    @property
    def bullseye_position(self):
        return (self.bullseye_x, self.bullseye_y)

    @property
    def _section_nav_points(self):
        return self._section_coalition['nav_points']

    @property
    def coalition_name(self):
        return self._section_coalition['name']

    @property
    def _section_country(self):
        return self._section_coalition['country']

    @property
    def countries(self):
        for k in self._section_country:
            if k not in self._countries.keys():
                country = Country(self.d, self.ln10, self.coa_color, k)
                self._countries[k] = country
                self._countries_by_id[country.country_id] = country
                self._countries_by_name[country.country_name] = country
            yield self._countries[k]

    def get_country_by_name(self, country_name):
        validator.str.validate(country_name, 'get_country_by_name')
        if country_name not in self._countries_by_name.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_name == country_name:
                    return country
            raise MizErrors.CountryNotFoundError(country_name)
        else:
            return self._countries_by_name[country_name]

    def get_country_by_id(self, country_id):
        validator.positive_integer.validate(country_id, 'get_country_by_id', exc=MizErrors.InvalidParameterError)
        if country_id not in self._countries_by_id.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_id == country_id:
                    return country
            raise MizErrors.CountryNotFoundError(country_id)
        else:
            return self._countries_by_id[country_id]

    @property
    def groups(self):
        for country in self.countries:
            assert isinstance(country, Country)
            for group in country.groups:
                assert isinstance(group, Group)
                yield group

    def get_groups_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_groups_from_category')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_category == category:
                yield group

    @property
    def units(self):
        for group in self.groups:
            assert isinstance(group, Group)
            for unit in group.units:
                yield unit

    def get_units_from_category(self, category):
        Mission.validator_group_category.validate(category, 'group category')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.group_category == category:
                yield unit

    def get_group_by_id(self, group_id):
        validator.positive_integer.validate(group_id, 'get_group_by_id')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_id == group_id:
                return group
        return None

    def get_group_by_name(self, group_name):
        validator.str.validate(group_name, 'get_group_by_name')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_name == group_name:
                return group
        return None

    def get_unit_by_name(self, unit_name):
        validator.str.validate(unit_name, 'get_unit_by_name')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        validator.positive_integer.validate(unit_id, 'get_unit_by_id')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_id == unit_id:
                return unit
        return None


class Country(Coalition):
    def __init__(self, mission_dict, ln10, coa_color, country_index):
        super().__init__(mission_dict, ln10, coa_color)
        self.__groups = {
            'helicopter': {},
            'plane'     : {},
            'vehicle'   : {},
            'ship'      : {},
        }
        self.country_index = country_index

    def __repr__(self):
        return 'Country({}, {}, {})'.format(self._section_country, self.coa_color, self.country_index)

    def __eq__(self, other):
        if not isinstance(other, Country):
            raise MizErrors.InvalidParameterError('"other" must be an Country instance; got: {}'.format(type(other)))
        return self._section_country == other._section_country

    @property
    def _section_this_country(self):
        return self._section_coalition['country'][self.country_index]

    @property
    def country_id(self):
        return self._section_this_country['id']

    @property
    def country_name(self):
        return self._section_this_country['name']

    @property
    def groups(self):
        for group_category in Mission.valid_group_categories:
            if group_category in self._section_this_country.keys():
                for group_index in self._section_this_country[group_category]['group']:
                    if group_index not in self.__groups[group_category]:
                        self.__groups[group_category][group_index] = Group(self.d, self.ln10, self.coa_color, self.country_index, group_category, group_index)
                    yield self.__groups[group_category][group_index]

    def get_groups_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_groups_from_category')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_category == category:
                yield group

    def get_group_by_id(self, group_id):
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_id == group_id:
                return group
        return None

    def get_group_by_name(self, group_name):
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_name == group_name:
                return group
        return None

    @property
    def units(self):
        for group in self.groups:
            assert isinstance(group, Group)
            for unit in group.units:
                yield unit

    def get_unit_by_name(self, unit_name):
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    def get_units_from_category(self, category):
        Mission.validator_group_category.validate(category, 'group category')
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.group_category == category:
                yield unit


class Group(Country):
    class Route():

        def __init__(self, parent_group):
            assert isinstance(parent_group, Group)
            self.parent_group = parent_group

        def __repr__(self):
            return 'Route({})'.format(self.parent_group.group_name)

        @property
        def _section_route(self):
            return self.parent_group._section_group['route']['points']

    validator_group_or_unit_name = Validator(_type=str, _regex=r'[a-zA-Z0-9\_\-\#]+', exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_group_route = Validator(_type=Route, exc=MizErrors.InvalidParameterError, logger=LOGGER)
    units_class_enum = None

    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index):
        super().__init__(mission_dict, ln10, coa_color, country_index)
        self.group_category = group_category
        self.group_index = group_index
        self.__group_route = None
        self.__units = {}
        self.units_class_enum = {
            'helicopter': Helicopter,
            'plane'     : Plane,
            'ship'      : Ship,
            'vehicle'   : Vehicle,
        }

    def __repr__(self):
        return 'Group({}, {}, {}, {}, {})'.format(self._section_group, self.coa_color, self.country_index, self.group_category, self.group_index)

    def __eq__(self, other):
        if not isinstance(other, Group):
            raise MizErrors.InvalidParameterError('"other" must be an AbstractUnit instance; got: {}'.format(type(other)))
        return self._section_group == other._section_group

    @property
    def group_route(self):
        if self.__group_route is None:
            self.__group_route = Group.Route(self)
        return self.__group_route

    @group_route.setter
    def group_route(self, value):
        self.validator_group_route.validate(value, 'group_route')
        self.__group_route = value

    @property
    def _section_group(self):
        return self._section_this_country[self.group_category]['group'][self.group_index]

    @property
    def _group_name_key(self):
        return self._section_group['name']

    @property
    def group_name(self):
        return self.ln10[self._group_name_key]

    @group_name.setter
    def group_name(self, value):
        self.validator_group_or_unit_name.validate(value, 'group name')
        self.ln10[self._group_name_key] = value

    @property
    def group_hidden(self):
        return self._section_group['hidden']

    @group_hidden.setter
    def group_hidden(self, value):
        validator.bool.validate(value, 'property "hidden" for group')
        self._section_group['hidden'] = value

    @property
    def group_id(self):
        return self._section_group['groupId']

    @group_id.setter
    def group_id(self, value):
        validator.integer.validate(value, 'groupId')
        self._section_group['goupId'] = value

    @property
    def group_start_delay(self):
        return self._section_group['start_time']

    @group_start_delay.setter
    def group_start_delay(self, value):
        validator.integer.validate(value, 'group_start_delay')
        if value < 0:
            raise MizErrors.InvalidGroupStartTimeError(self.group_name)
        self._section_group['start_time'] = value

    @property
    def group_start_time(self):
        return self.group_start_delay + self.mission_start_time

    @group_start_time.setter
    def group_start_time(self, value):
        validator.integer.validate(value, 'group_start_time')
        self.group_start_delay = value - self.mission_start_time

    @property
    def group_start_time_as_date(self):
        return strftime('%d/%m/%Y %H:%M:%S', gmtime(EPOCH_DELTA + self.group_start_time))

    @group_start_time_as_date.setter
    def group_start_time_as_date(self, value):
        Mission.validator_start_date.validate(value, 'start_time_as_date')
        self.group_start_time = timegm(strptime(value, '%d/%m/%Y %H:%M:%S')) - EPOCH_DELTA

    @property
    def units(self):
        for unit_index in self._section_group['units']:
            if unit_index not in self.__units.keys():
                self.__units[unit_index] = self.units_class_enum[self.group_category](self.d, self.ln10, self.coa_color, self.country_index, self.group_category, self.group_index, unit_index)
            yield self.__units[unit_index]

    def get_unit_by_name(self, unit_name):
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        for unit in self.units:
            assert isinstance(unit, AbstractUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    def get_unit_by_index(self, unit_index):
        if unit_index in self._section_group['units'].keys():
            if unit_index not in self.__units.keys():
                self.__units[unit_index] = self.units_class_enum[self.group_category](self.d, self.ln10, self.coa_color, self.country_index, self.group_category, self.group_index, unit_index)
            return self.__units[unit_index]
        return None

    @property
    def group_is_client_group(self):
        # TODO create test
        first_unit = self.get_unit_by_index(1)
        assert isinstance(first_unit, AbstractUnit)
        return first_unit.skill == 'Client'


class AbstractUnit(Group):
    validator_skill = Validator(_type=str, _in_list=['Average', 'Good', 'High', 'Excellent', 'Random', 'Client', 'Player'], exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_onboard_number = Validator(_type=str, _regex=r'[0-9]{3}', exc=MizErrors.InvalidParameterError, logger=LOGGER)
    validator_unit_types = Validator(_type=str, _in_list=[], exc=MizErrors.InvalidParameterError, logger=LOGGER)

    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index)
        self.unit_index = unit_index

    def __repr__(self):
        return '{}({}, {}, {}, {}, {}, {})'.format(self.__class__.__name__, self._section_unit, self.coa_color, self.country_index, self.group_category, self.group_index, self.unit_index)

    @property
    def _section_unit(self):
        return self._section_group['units'][self.unit_index]

    @property
    def _unit_name_key(self):
        return self._section_unit['name']

    @property
    def unit_name(self):
        return self.ln10[self._unit_name_key]

    @unit_name.setter
    def unit_name(self, value):
        self.validator_group_or_unit_name.validate(value, 'unit name')
        self.ln10[self._unit_name_key] = value

    @property
    def skill(self):
        return self._section_unit['skill']

    @skill.setter
    def skill(self, value):
        self.validator_skill.validate(value, 'unit skill')
        self._section_unit['skill'] = value

    @property
    def speed(self):
        return self._section_unit['speed']

    @speed.setter
    def speed(self, value):
        validator.float.validate(value, 'unit speed')
        self._section_unit['speed'] = value

    @property
    def unit_type(self):
        return self._section_unit['type']

    @unit_type.setter
    def unit_type(self, value):
        self.validator_unit_types.validate(value, 'unit type')
        self._section_unit['type'] = value

    @property
    def unit_id(self):
        return self._section_unit['unitId']

    @unit_id.setter
    def unit_id(self, value):
        validator.integer.validate(value, 'unitId')
        self._section_unit['unitId'] = value

    @property
    def unit_pos_x(self):
        return float(self._section_unit['x'])

    @unit_pos_x.setter
    def unit_pos_x(self, value):
        validator.float.validate(value, 'unit position X coordinate')
        self._section_unit['x'] = value

    @property
    def unit_pos_y(self):
        return float(self._section_unit['y'])

    @unit_pos_y.setter
    def unit_pos_y(self, value):
        validator.float.validate(value, 'unit position Y coordinate')
        self._section_unit['y'] = value

    @property
    def unit_position(self):
        return self.unit_pos_x, self.unit_pos_y

    @unit_position.setter
    def unit_position(self, x, y):
        self.unit_pos_x = x
        self.unit_pos_y = y

    @property
    def heading(self):
        return self._section_unit['heading']

    @heading.setter
    def heading(self, value):
        Mission.validator_heading.validate(value, 'unit heading')
        self._section_unit['heading'] = value

    @property
    def radio_presets(self):
        raise MizErrors.NoRadioPresetsError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    @property
    def has_radio_presets(self):
        return all([self.skill == 'Client', self.unit_type in FlyingUnit.RadioPresets.radio_enum.keys()])

    def __eq__(self, other):
        if not isinstance(other, AbstractUnit):
            raise MizErrors.InvalidParameterError('"other" must be an AbstractUnit instance; got: {}'.format(type(other)))
        return self._section_unit == other._section_unit


class FlyingUnit(AbstractUnit):

    class RadioPresets:

        radio_enum = {
            'Ka-50'      : {
                1: {
                    'radio_name'  : 'R828',
                    'min'         : 20,
                    'max'         : 59.9,
                    'channels_qty': 10,
                },
                2: {
                    'radio_name'  : 'ARK22',
                    'min'         : 0.15,
                    'max'         : 1.75,
                    'channels_qty': 16,
                },
            },
            'Mi-8MT'     : {
                1: {
                    'radio_name'  : 'R863',
                    'min'         : 100,
                    'max'         : 399.9,
                    'channels_qty': 20,
                },
                2: {
                    'radio_name'  : 'R828',
                    'min'         : 20,
                    'max'         : 59.9,
                    'channels_qty': 10,
                },
            },
            'UH-1H'      : {
                1: {
                    'radio_name'  : 'ARC51',
                    'min'         : 225,
                    'max'         : 399.97,
                    'channels_qty': 20,
                },
            },
            'F-86F Sabre': {
                1: {
                    'radio_name'  : 'ARC-27',
                    'min'         : 225,
                    'max'         : 399.9,
                    'channels_qty': 18,
                },
            },
            'M-2000C'    : {
                1: {
                    'radio_name'  : 'UHF',
                    'min'         : 225,
                    'max'         : 400,
                    'channels_qty': 20,
                },
                2: {
                    'radio_name'  : 'V/UHF',
                    'min'         : 118,
                    'max'         : 400,
                    'channels_qty': 20,
                },
            },
            'MiG-21Bis'  : {
                1: {
                    'radio_name'  : 'R-832',
                    'min'         : 80,
                    'max'         : 399.9,
                    'channels_qty': 20,
                },
            },
            'P-51D'      : {
                1: {
                    'radio_name'  : 'SCR552',
                    'min'         : 100,
                    'max'         : 156,
                    'channels_qty': 4,
                },
            },
            'TF-51D'     : {
                1: {
                    'radio_name'  : 'SCR552',
                    'min'         : 100,
                    'max'         : 156,
                    'channels_qty': 4,
                },
            },
        }

        def __init__(self, parent_unit, radio_num):
            assert isinstance(parent_unit, FlyingUnit)
            self.parent_unit = parent_unit
            self.radio_num = radio_num

        def __eq__(self, other):
            if not isinstance(other, FlyingUnit.RadioPresets):
                raise Exception('cannot compare RadioPreset instance with other object of type {}'.format(type(other)))
            assert isinstance(other, FlyingUnit.RadioPresets)
            if not self.radio_name == other.radio_name:
                return False
            for channel, frequency in self.channels:
                if not frequency == other.get_frequency(channel):
                    return False
            return True
            
        @property
        def radio_name(self):
            return self.radio_enum[self.parent_unit.unit_type][self.radio_num]['radio_name']
            
        @property
        def channels_qty(self):
            return self.radio_enum[self.parent_unit.unit_type][self.radio_num]['channels_qty']
            
        @property
        def min(self):
            return float(self.radio_enum[self.parent_unit.unit_type][self.radio_num]['min'])
            
        @property
        def max(self):
            return float(self.radio_enum[self.parent_unit.unit_type][self.radio_num]['max'])

        @property
        def _section_radio(self):
            return self.parent_unit._section_unit['Radio']
        
        @property
        def _section_channels(self):
            return self._section_radio[self.radio_num]['channels']

        @property
        def channels(self):
            for k in self._section_channels:
                yield (k, float(self._section_channels[k]))

        def get_frequency(self, channel):
            validator.positive_integer.validate(channel, 'get_frequency')
            if 1 <= channel <= self.channels_qty:
                return float(self._section_channels[channel])
            else:
                raise MizErrors.InvalidChannelError('channel {} for radio {} in aircraft {}'.format(channel, self.radio_name, self.parent_unit.unit_name))

        def set_frequency(self, channel, frequency):
            validator.positive_integer.validate(channel, 'set_frequency')
            validator.float.validate(frequency, 'set_frequency')
            if 1 <= channel <= self.channels_qty:
                if self.min <= frequency <= self.max:
                    self._section_channels[channel] = float(frequency)
                else:
                    raise MizErrors.InvalidFrequencyError('frequency {} for channel {} for radio {} in aircraft {}'.format(frequency, channel, self.radio_name, self.parent_unit.unit_name))
            else:
                raise MizErrors.InvalidChannelError('channel {} for radio {} in aircraft {}'.format(channel, self.radio_name, self.parent_unit.unit_name))

    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index)

    @property
    def radio_presets(self):
        if self.skill == 'Client' and self.unit_type in FlyingUnit.RadioPresets.radio_enum.keys():
            for k in self._section_unit['Radio']:
                yield FlyingUnit.RadioPresets(self, k)
        else:
            raise MizErrors.NoRadioPresetsError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    def get_radio_by_name(self, radio_name):
        if self.has_radio_presets:
            for k in FlyingUnit.RadioPresets.radio_enum[self.unit_type].keys():
                if radio_name == FlyingUnit.RadioPresets.radio_enum[self.unit_type][k]['radio_name']:
                    return FlyingUnit.RadioPresets(self, k)
            raise MizErrors.InvalidRadioForThisAircraft('{} for aircraft: {}'.format(radio_name, self.unit_type))
        else:
            raise MizErrors.NoRadioPresetsError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    def get_radio_by_number(self, radio_number):
        if self.has_radio_presets:
            if radio_number in FlyingUnit.RadioPresets.radio_enum[self.unit_type].keys():
                return FlyingUnit.RadioPresets(self, radio_number)
            else:
                raise MizErrors.InvalidRadioForThisAircraft('radio number {} for aircraft: {}'.format(radio_number, self.unit_type))
        else:
            raise MizErrors.NoRadioPresetsError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    @property
    def livery(self):
        return self._section_unit['livery_id']

    @livery.setter
    def livery(self, value):
        # TODO validate livery_id
        validator.str.validate(value, 'unit livery')
        self._section_unit['livery_id'] = value

    @property
    def onboard_num(self):
        return self._section_unit['onboard_num']

    @onboard_num.setter
    def onboard_num(self, value):
        AbstractUnit.validator_onboard_number.validate(value, 'unit onboard number')
        self._section_unit['onboard_num'] = value


class Helicopter(FlyingUnit):
    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index)


class Plane(FlyingUnit):
    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index)


class Vehicle(AbstractUnit):
    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index)


class Ship(AbstractUnit):
    def __init__(self, mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, ln10, coa_color, country_index, group_category, group_index, unit_index)


class Miz(Logged):
    def __init__(self, path_to_miz_file, temp_dir=None):
        super().__init__()
        self.miz_path = abspath(path_to_miz_file)
        if not exists(self.miz_path):
            self.logger.error('miz file does not exist: {}'.format(self.miz_path))
            raise MizErrors.MizFileNotFoundError(self.miz_path)
        self.logger.debug('making new Mission object based on miz file: {}'.format(self.miz_path))
        self.temp_dir_path = BaseUtils.tmp_path() if temp_dir is None else BaseUtils.tmp_path(temp_dir)
        self.logger.debug('temporary directory for this mission object: {}'.format(self.temp_dir_path))
        self.files_in_zip = []
        self.__unzipped = False
        self.__ln10 = {}
        self.__mission = Mission(OrderedDict(), self.__ln10)

    def __enter__(self):
        self.logger.debug('instantiating new Mission object as a context')
        self.unzip()
        self.decode()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('closing Mission object context')
        if exc_type:
            self.logger.error('there were error with this mission, keeping temp dir at "{}" and re-raising'.format(self.temp_dir_path))
            print(exc_type, exc_val)
            return False
        else:
            self.remove_temp_dir()


    @property
    def is_unzipped(self):
        return self.__unzipped

    @property
    def ln10(self):
        return self.__ln10

    @property
    def mission(self):
        return self.__mission

    @property
    def mission_file_path(self):
        return abspath(join(self.temp_dir_path, './mission')).replace('\\', '/')

    @property
    def ln10_file_path(self):
        return abspath(join(self.temp_dir_path, './l10n/DEFAULT/dictionary')).replace('\\', '/')

    def decode_mission(self, ln10):
        parser = SLPP()
        try:
            self.logger.debug('parsing mission lua table into dictionary')
            with open(self.mission_file_path, encoding='iso8859_15') as _f:
                self.__mission = Mission(parser.decode("\n".join(_f.readlines()[1:])), ln10)
        except:
            self.logger.exception('error while parsing mission lua table')
            raise

    def decode_ln10(self):
        self.logger.debug('reading ln10 dictionary at: {}'.format(self.ln10_file_path))
        try:
            parser = SLPP()
            with open(self.ln10_file_path) as _f:
                self.__ln10 = parser.decode("\n".join(_f.readlines()[1:]))
        except:
            self.logger.exception('error while reading ln10 dictionary: {}'.format(self.ln10_file_path))
            raise

    def decode(self):
        self.logger.debug('reading Mission files from disk')
        self.decode_ln10()
        self.decode_mission(self.ln10)

    def unzip(self, force=False):
        """Extracts MIZ file into temp dir"""
        self.logger.debug('unzipping miz into temp dir: "{}" -> {}'.format(self.miz_path, self.temp_dir_path))
        with ZipFile(self.miz_path) as zip_file:
            try:
                self.logger.debug('reading infolist')
                zip_content = zip_file.infolist()
                self.files_in_zip = [f.filename for f in zip_content]
                for item in zip_content:  # not using ZipFile.extractall() for security reasons
                    assert isinstance(item, ZipInfo)
                    self.logger.debug('unzipping item: {}'.format(item.filename))
                    try:
                        zip_file.extract(item, self.temp_dir_path)
                    except RuntimeError:
                        raise MizErrors.ExtractError(item)
            except BadZipFile:
                raise MizErrors.CorruptedMizError(self.miz_path)
            except:
                self.logger.exception('error while unzipping miz file: {}'.format(self.miz_path))
                raise
        self.logger.debug('checking miz content')
        for miz_item in map(join, [self.temp_dir_path], ['./mission', './options', './warehouses', './l10n/DEFAULT/dictionary', './l10n/DEFAULT/mapResource']):
            if not exists(miz_item):
                self.logger.error('missing file in miz: {}'.format(miz_item))
                raise MizErrors.MissingFileInMizError(miz_item)
        self.logger.debug('all files have been found, miz successfully unzipped')
        self.__unzipped = True

    def __encode_mission(self):
        self.logger.debug('writing mission dictionary to mission file: {}'.format(self.mission_file_path))
        parser = SLPP()
        try:
            self.logger.debug('encoding dictionary to lua table')
            raw_text = parser.encode(self.__mission.d)
        except:
            self.logger.exception('error while encoding')
            raise
        try:
            self.logger.debug('overwriting mission file')
            with open(self.mission_file_path, mode="w", encoding='iso8859_15') as _f:
                _f.write('mission = ')
                raw_text = re_sub(RE_SPACE_AFTER_EQUAL_SIGN, "= \n", raw_text)
                _f.write(raw_text)
        except:
            self.logger.exception('error while writing mission file: {}'.format(self.mission_file_path))
            raise

    def __encode_ln10(self):
        self.logger.debug('writing ln10 to: {}'.format(self.ln10_file_path))
        parser = SLPP()
        try:
            self.logger.debug('encoding dictionary to lua table')
            raw_text = parser.encode(self.ln10)
        except:
            self.logger.exception('error while encoding')
            raise
        try:
            self.logger.debug('overwriting mission file')
            with open(self.ln10_file_path, mode="w") as _f:
                _f.write('dictionary = ')
                raw_text = re_sub(RE_SPACE_AFTER_EQUAL_SIGN, "= \n", raw_text)
                _f.write(raw_text)
        except:
            self.logger.exception('error while writing ln10 file: {}'.format(self.ln10_file_path))
            raise

    def zip(self):
        self.__encode_mission()
        self.__encode_ln10()
        out_file = abspath('{}_ESME.miz'.format(self.miz_path[:-4])).replace('\\', '/')
        try:
            self.logger.debug('zipping mission into: {}'.format(out_file))
            with ZipFile(out_file, mode='w', compression=8) as _z:
                for f in self.files_in_zip:
                    full_path = abspath(join(self.temp_dir_path, f)).replace('\\', '/')
                    self.logger.debug("injecting in zip file: {}".format(full_path))
                    _z.write(full_path, arcname=f)
        except:
            self.logger.exception('error while zipping miz file')
            raise

    def wipe_temp_dir(self):
        """Removes all files & folders from temp_dir, wiping it clean"""
        files = []
        folders = []
        self.logger.debug('wiping temporary directory')
        for root, _folders, _files in walk(self.temp_dir_path, topdown=False):
            for f in _folders:
                folders.append(join(root, f))
            for f in _files:
                files.append(join(root, f))
        self.logger.debug('removing files')
        for f in files:
            self.logger.debug('removing: {}'.format(f))
            try:
                remove(f)
            except:
                self.logger.exception('could not remove: {}'.format(f))
                raise
        self.logger.debug('removing folders')
        for f in folders:
            self.logger.debug('removing: {}'.format(f))
            try:
                rmdir(f)
            except:
                self.logger.exception('could not remove: {}'.format(f))
                raise

    def remove_temp_dir(self):
        """Deletes the temporary directory"""
        self.logger.debug('removing temporary directory: {}'.format(self.temp_dir_path))
        self.wipe_temp_dir()
        try:
            rmdir(self.temp_dir_path)
        except:
            self.logger.exception('could not remove: {}'.format(self.temp_dir_path))
            raise

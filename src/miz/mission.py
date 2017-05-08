# coding=utf-8
from calendar import timegm
from itertools import chain
from time import strftime, gmtime, strptime

from utils import make_logger
from utils import Logged, valid_str, valid_positive_int, Validator, valid_bool, valid_int, valid_float

EPOCH_DELTA = 1306886400

logger = make_logger(__name__)


class BaseMissionObject(Logged):
    def __init__(self, mission_dict: dict, l10n: dict):
        super().__init__()

        if not isinstance(mission_dict, dict):
            raise TypeError('mission_dict should be an dict, got: {}'.format(type(mission_dict)))

        if not isinstance(l10n, dict):
            print(l10n)
            raise TypeError('l10n should be an dict, got: {}'.format(type(l10n)))

        self.d = mission_dict
        self.l10n = l10n

        self.weather = None
        self.blue_coa = None
        self.red_coa = None
        self.ground_control = None

        self._countries_by_name = {}
        self._countries_by_id = {}

    def get_country_by_name(self, country_name):
        valid_str.validate(country_name, 'get_country_by_name', exc=ValueError)
        if country_name not in self._countries_by_name.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_name == country_name:
                    self._countries_by_name[country_name] = country
                    return country
            raise ValueError(country_name)
        else:
            return self._countries_by_name[country_name]

    def get_country_by_id(self, country_id):
        valid_positive_int.validate(country_id, 'get_country_by_id')
        if country_id not in self._countries_by_id.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_id == country_id:
                    self._countries_by_id[country_id] = country
                    return country
            raise ValueError(country_id)
        else:
            return self._countries_by_id[country_id]

    def get_groups_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_groups_from_category')
        for group in self.groups:
            if group.group_category == category:
                yield group

    def get_units_from_category(self, category):
        Mission.validator_group_category.validate(category, 'get_units_from_category')
        for unit in self.units:
            if unit.group_category == category:
                yield unit

    def get_group_by_id(self, group_id):
        valid_positive_int.validate(group_id, 'get_group_by_id', exc=ValueError)
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_id == group_id:
                return group
        return None

    def get_clients_groups(self):
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_is_client_group:
                yield group

    def get_group_by_name(self, group_name):
        valid_str.validate(group_name, 'get_group_by_name')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_name == group_name:
                return group
        return None

    def get_unit_by_name(self, unit_name):
        valid_str.validate(unit_name, 'get_unit_by_name')
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        valid_positive_int.validate(unit_id, 'get_unit_by_id')
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    @property
    def units(self):
        for group in self.groups:
            for unit in group.units:
                assert isinstance(unit, BaseUnit)
                yield unit

    @property
    def groups(self):
        for country in self.countries:
            for group in country.groups:
                assert isinstance(group, Group)
                yield group

    @property
    def next_group_id(self):
        ids = set()
        for group in chain(self.blue_coa.groups, self.red_coa.groups):
            assert isinstance(group, Group)
            id_ = group.group_id
            if id_ in ids:
                raise IndexError(group.group_name)
            ids.add(id_)
        return max(ids) + 1

    @property
    def next_unit_id(self):
        ids = set()
        for unit in chain(self.blue_coa.units, self.red_coa.units):
            assert isinstance(unit, BaseUnit)
            id_ = unit.unit_id
            if id_ in ids:
                raise IndexError(unit.unit_name)
            ids.add(id_)
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
        return self.l10n[self._sortie_name_key]

    @sortie_name.setter
    def sortie_name(self, value):
        valid_str.validate(value, 'sortie name')
        self.l10n[self._sortie_name_key] = value


class Mission(BaseMissionObject):
    validator_start_time = Validator(
        _type=int,
        _min=0,
        exc=ValueError,
        logger=logger
    )
    validator_start_date = Validator(
        _type=str,
        _regex=r'^(?=\d)(?:(?:31(?!.(?:0?[2469]|11))|(?:30|29)(?!.0?2)|29'
               r'(?=.0?2.(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])'
               r'|(?:(?:16|[2468][048]|[3579][26])00)))(?:\x20|$))|(?:2[0-8]|1\d|0?[1-9]))'
               r'([-./])(?:1[012]|0?[1-9])\1(?:1[6-9]|[2-9]\d)?\d\d(?:(?=\x20\d)\x20|$))?'
               r'(((0?[1-9]|1[012])(:[0-5]\d){0,2}(\x20[AP]M))|([01]\d|2[0-3])'
               r'(:[0-5]\d){1,2})?$',
        exc=ValueError,
        logger=logger
    )
    validator_heading = Validator(
        _type=int,
        _min=0,
        _max=359,
        exc=ValueError,
        logger=logger
    )
    validator_group_category = Validator(
        _type=str,
        _in_list=['helicopter', 'ship', 'plane', 'vehicle'],
        exc=ValueError,
        logger=logger)
    valid_group_categories = ('helicopter', 'plane', 'ship', 'vehicle')

    def __init__(self, mission_dict, l10n):
        super().__init__(mission_dict, l10n)
        self.weather = Weather(self.d, l10n)
        self.blue_coa = Coalition(self.d, l10n, 'blue')
        self.red_coa = Coalition(self.d, l10n, 'red')
        self.ground_control = GroundControl(self.d, l10n)

    def __repr__(self):
        return 'Mission({})'.format(self.d)


# noinspection PyProtectedMember
class Coalition(BaseMissionObject):
    def __init__(self, mission_dict, ln10, coa_color):
        super().__init__(mission_dict, ln10)
        self.coa_color = coa_color
        self._countries = {}

    def __repr__(self):
        return 'Coalition({}, {})'.format(self._section_coalition, self.coa_color)

    def __eq__(self, other):
        if not isinstance(other, Coalition):
            raise ValueError('"other" must be an Coalition instance; got: {}'.format(type(other)))
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
        return self.bullseye_x, self.bullseye_y

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
                country = Country(self.d, self.l10n, self.coa_color, k)
                self._countries[k] = country
                self._countries_by_id[country.country_id] = country
                self._countries_by_name[country.country_name] = country
            yield self._countries[k]

    def get_country_by_name(self, country_name):
        valid_str.validate(country_name, 'get_country_by_name', exc=ValueError)
        if country_name not in self._countries_by_name.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_name == country_name:
                    return country
            raise ValueError(country_name)
        else:
            return self._countries_by_name[country_name]

    def get_country_by_id(self, country_id):
        valid_positive_int.validate(country_id, 'get_country_by_id', exc=ValueError)
        if country_id not in self._countries_by_id.keys():
            for country in self.countries:
                assert isinstance(country, Country)
                if country.country_id == country_id:
                    return country
            raise ValueError(country_id)
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
            assert isinstance(unit, BaseUnit)
            if unit.group_category == category:
                yield unit

    def get_group_by_id(self, group_id):
        valid_positive_int.validate(group_id, 'get_group_by_id')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_id == group_id:
                return group
        return None

    def get_group_by_name(self, group_name):
        valid_str.validate(group_name, 'get_group_by_name')
        for group in self.groups:
            assert isinstance(group, Group)
            if group.group_name == group_name:
                return group
        return None

    def get_unit_by_name(self, unit_name):
        valid_str.validate(unit_name, 'get_unit_by_name')
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        valid_positive_int.validate(unit_id, 'get_unit_by_id')
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_id == unit_id:
                return unit
        return None


class Trig(BaseMissionObject):
    def __init__(self, mission_dict, l10n):
        super().__init__(mission_dict, l10n)

    @property
    def _section_trig(self):
        return self.d['trig']


class Result(BaseMissionObject):
    def __init__(self, mission_dict, l10n):
        super().__init__(mission_dict, l10n)

    @property
    def _section_result(self):
        return self.d['result']


class GroundControl(BaseMissionObject):
    validator_commander = Validator(_type=int, _min=0, _max=100, exc=ValueError, logger=logger)

    def __init__(self, mission_dict, l10n):
        super().__init__(mission_dict, l10n)

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
        valid_bool.validate(value, 'pilots_control_vehicles')
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


# noinspection PyProtectedMember
class Weather(BaseMissionObject):
    validator_precipitations = Validator(_type=int, _min=0, _max=4, exc=ValueError, logger=logger)
    validator_cloud_density = Validator(_type=int, _min=0, _max=10, exc=ValueError, logger=logger)
    validator_cloud_thickness = Validator(_type=int, _min=200, _max=2000, exc=ValueError,
                                          logger=logger)
    validator_cloud_base = Validator(_type=int, _min=300, _max=5000, exc=ValueError, logger=logger)
    validator_fog_visibility = Validator(_type=int, _min=0, _max=6000, exc=ValueError,
                                         logger=logger)
    validator_fog_thickness = Validator(_type=int, _min=0, _max=1000, exc=ValueError,
                                        logger=logger)
    validator_qnh = Validator(_type=int, _min=720, _max=790, exc=ValueError, logger=logger)
    validator_temp_spring_or_fall = Validator(_type=int, _min=-10, _max=30, exc=ValueError,
                                              logger=logger)
    validator_temp_winter = Validator(_type=int, _min=-50, _max=15, exc=ValueError, logger=logger)
    validator_temp_summer = Validator(_type=int, _min=5, _max=50, exc=ValueError, logger=logger)
    seasons_enum = {
        1: {
            'name': 'summer',
            'temp_validator': validator_temp_summer,
        },
        2: {
            'name': 'winter',
            'temp_validator': validator_temp_winter,
        },
        3: {
            'name': 'spring',
            'temp_validator': validator_temp_spring_or_fall,
        },
        4: {
            'name': 'fall',
            'temp_validator': validator_temp_spring_or_fall,
        },
        'summer': 1,
        'winter': 2,
        'spring': 3,
        'fall': 4,
    }
    validator_season_name = Validator(_type=str, _in_list=['summer', 'winter', 'fall', 'spring'],
                                      exc=ValueError, logger=logger)
    validator_season_code = Validator(_type=int, _min=1, _max=4, exc=ValueError, logger=logger)
    validator_turbulence = Validator(_type=int, _min=0, _max=60, exc=ValueError, logger=logger)
    validator_atmo_type = Validator(_type=int, _min=0, _max=1, exc=ValueError, logger=logger)
    validator_wind_speed = Validator(_type=int, _min=0, _max=50, exc=ValueError, logger=logger)

    def __init__(self, mission_dict, l10n):
        super().__init__(mission_dict, l10n)

    def __repr__(self):
        return 'Weather({})'.format(self._section_weather)

    def __eq__(self, other):
        if not isinstance(other, Weather):
            raise ValueError('"other" must be an Weather instance; got: {}'.format(type(other)))
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
    def _section_wind_at_ground_level(self):
        return self._section_wind['atGround']

    @property
    def turbulence_at_ground_level(self):
        return self._section_weather['groundTurbulence']

    @turbulence_at_ground_level.setter
    def turbulence_at_ground_level(self, value):
        self.validator_turbulence.validate(value, 'turbulence_at_ground_level')
        self._section_weather['groundTurbulence'] = value

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
            raise ValueError('No rain or snow if cloud density is less than 5')
        if value in [2, 4] and self.cloud_density <= 8:
            raise ValueError('No thunderstorm or snowstorm if cloud density is less than 9')
        if value > 2 and self.temperature > 0:
            raise ValueError('No snow with temperature over 0; use rain or thunderstorm instead')
        if value in [1, 2] and self.temperature < 0:
            raise ValueError(
                'No rain or thunderstorm if temperature is below 0; use snow or snowstorm instead')
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
        valid_bool.validate(value, 'enable_fog')
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


# noinspection PyProtectedMember
class Country(Coalition):
    def __init__(self, mission_dict, l10n, coa_color, country_index):
        super().__init__(mission_dict, l10n, coa_color)
        self.__groups = {
            'helicopter': {},
            'plane': {},
            'vehicle': {},
            'ship': {},
        }
        self.country_index = country_index

    def __repr__(self):
        return 'Country({}, {}, {})'.format(self._section_country, self.coa_color, self.country_index)

    def __eq__(self, other):
        if not isinstance(other, Country):
            raise ValueError('"other" must be an Country instance; got: {}'.format(type(other)))
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
                        self.__groups[group_category][group_index] = Group(self.d, self.l10n, self.coa_color,
                                                                           self.country_index, group_category,
                                                                           group_index)
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
            assert isinstance(unit, BaseUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    def get_units_from_category(self, category):
        Mission.validator_group_category.validate(category, 'group category')
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.group_category == category:
                yield unit


# noinspection PyProtectedMember
class Group(Country):

    attribs = ('group_category', 'group_index', 'group_hidden', 'group_start_time', '_group_name_key')

    class Route:

        def __init__(self, parent_group):
            assert isinstance(parent_group, Group)
            self.parent_group = parent_group

        def __repr__(self):
            return 'Route({})'.format(self.parent_group.group_name)

        @property
        def _section_route(self):
            return self.parent_group._section_group['route']['points']

    validator_group_or_unit_name = Validator(_type=str, _regex=r'[a-zA-Z0-9\_\-\#]+',
                                             exc=ValueError, logger=logger)
    validator_group_route = Validator(_type=Route, exc=ValueError, logger=logger)
    units_class_enum = None

    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index):
        super().__init__(mission_dict, l10n, coa_color, country_index)
        self.group_category = group_category
        self.group_index = group_index
        self.__group_route = None
        self.__units = {}
        self.units_class_enum = {
            'helicopter': Helicopter,
            'plane': Plane,
            'ship': Ship,
            'vehicle': Vehicle,
        }

    def __repr__(self):
        return 'Group({}, {}, {}, {}, {})'.format(self._section_group, self.coa_color, self.country_index,
                                                  self.group_category, self.group_index)

    def __eq__(self, other):
        if not isinstance(other, Group):
            raise ValueError(
                '"other" must be an AbstractUnit instance; got: {}'.format(type(other)))
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
        return self.l10n[self._group_name_key]

    @group_name.setter
    def group_name(self, value):
        self.validator_group_or_unit_name.validate(value, 'group name')
        self.l10n[self._group_name_key] = value

    @property
    def group_hidden(self):
        return self._section_group['hidden']

    @group_hidden.setter
    def group_hidden(self, value):
        valid_bool.validate(value, 'property "hidden" for group')
        self._section_group['hidden'] = value

    @property
    def group_id(self):
        return self._section_group['groupId']

    @group_id.setter
    def group_id(self, value):
        valid_int.validate(value, 'groupId')
        self._section_group['goupId'] = value

    @property
    def group_start_delay(self):
        return self._section_group['start_time']

    @group_start_delay.setter
    def group_start_delay(self, value):
        valid_int.validate(value, 'group_start_delay')
        if value < 0:
            raise ValueError(self.group_name)
        self._section_group['start_time'] = value

    @property
    def group_start_time(self):
        return self.group_start_delay + self.mission_start_time

    @group_start_time.setter
    def group_start_time(self, value):
        valid_int.validate(value, 'group_start_time')
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
                self.__units[unit_index] = self.units_class_enum[self.group_category](self.d, self.l10n, self.coa_color,
                                                                                      self.country_index,
                                                                                      self.group_category,
                                                                                      self.group_index, unit_index)
            yield self.__units[unit_index]

    def first_unit(self) -> 'BaseUnit':
        return list(self.units)[0]

    def group_size(self) -> int:
        return len(list(self.units))

    def get_unit_by_name(self, unit_name):
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_unit_by_id(self, unit_id):
        for unit in self.units:
            assert isinstance(unit, BaseUnit)
            if unit.unit_id == unit_id:
                return unit
        return None

    def get_unit_by_index(self, unit_index):
        if unit_index in self._section_group['units'].keys():
            if unit_index not in self.__units.keys():
                self.__units[unit_index] = self.units_class_enum[self.group_category](self.d, self.l10n, self.coa_color,
                                                                                      self.country_index,
                                                                                      self.group_category,
                                                                                      self.group_index, unit_index)
            return self.__units[unit_index]
        return None

    @property
    def group_is_client_group(self):
        # TODO create test
        first_unit = self.get_unit_by_index(1)
        assert isinstance(first_unit, BaseUnit)
        return first_unit.skill == 'Client'


# noinspection PyProtectedMember
class BaseUnit(Group):
    validator_skill = Validator(_type=str,
                                _in_list=['Average', 'Good', 'High', 'Excellent', 'Random', 'Client', 'Player'],
                                exc=ValueError, logger=logger)
    validator_unit_types = Validator(_type=str, _in_list=[], exc=ValueError, logger=logger)

    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index)
        self.unit_index = unit_index

    def __repr__(self):
        return '{}({}, {}, {}, {}, {}, {})'.format(self.__class__.__name__, self._section_unit, self.coa_color,
                                                   self.country_index, self.group_category, self.group_index,
                                                   self.unit_index)

    @property
    def _section_unit(self):
        return self._section_group['units'][self.unit_index]

    @property
    def _unit_name_key(self):
        return self._section_unit['name']

    @property
    def unit_name(self):
        return self.l10n[self._unit_name_key]

    @unit_name.setter
    def unit_name(self, value):
        self.validator_group_or_unit_name.validate(value, 'unit name')
        self.l10n[self._unit_name_key] = value

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
        valid_float.validate(value, 'unit speed')
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
        valid_int.validate(value, 'unitId')
        self._section_unit['unitId'] = value

    @property
    def unit_pos_x(self):
        return float(self._section_unit['x'])

    @unit_pos_x.setter
    def unit_pos_x(self, value):
        valid_float.validate(value, 'unit position X coordinate')
        self._section_unit['x'] = value

    @property
    def unit_pos_y(self):
        return float(self._section_unit['y'])

    @unit_pos_y.setter
    def unit_pos_y(self, value):
        valid_float.validate(value, 'unit position Y coordinate')
        self._section_unit['y'] = value

    @property
    def unit_position(self):
        return self.unit_pos_x, self.unit_pos_y

    @unit_position.setter
    def unit_position(self, value):
        self.unit_pos_x, self.unit_pos_y = value

    @property
    def heading(self):
        return self._section_unit['heading']

    @heading.setter
    def heading(self, value):
        Mission.validator_heading.validate(value, 'unit heading')
        self._section_unit['heading'] = value

    @property
    def radio_presets(self):
        raise TypeError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    @property
    def has_radio_presets(self):
        return all([self.skill == 'Client', self.unit_type in FlyingUnit.RadioPresets.radio_enum.keys()])

    def __eq__(self, other):
        if not isinstance(other, BaseUnit):
            raise ValueError(
                '"other" must be an AbstractUnit instance; got: {}'.format(type(other)))
        return self._section_unit == other._section_unit


class FlyingUnit(BaseUnit):
    validator_board_number = Validator(_type=str, _regex=r'[0-9]{3}', exc=ValueError,
                                       logger=logger)

    class RadioPresets:

        radio_enum = {
            'Ka-50': {
                1: {
                    'radio_name': 'R828',
                    'min': 20,
                    'max': 59.9,
                    'channels_qty': 10,
                },
                2: {
                    'radio_name': 'ARK22',
                    'min': 0.15,
                    'max': 1.75,
                    'channels_qty': 16,
                },
            },
            'Mi-8MT': {
                1: {
                    'radio_name': 'R863',
                    'min': 100,
                    'max': 399.9,
                    'channels_qty': 20,
                },
                2: {
                    'radio_name': 'R828',
                    'min': 20,
                    'max': 59.9,
                    'channels_qty': 10,
                },
            },
            'UH-1H': {
                1: {
                    'radio_name': 'ARC51',
                    'min': 225,
                    'max': 399.97,
                    'channels_qty': 20,
                },
            },
            'F-86F Sabre': {
                1: {
                    'radio_name': 'ARC-27',
                    'min': 225,
                    'max': 399.9,
                    'channels_qty': 18,
                },
            },
            'M-2000C': {
                1: {
                    'radio_name': 'UHF',
                    'min': 225,
                    'max': 400,
                    'channels_qty': 20,
                },
                2: {
                    'radio_name': 'V/UHF',
                    'min': 118,
                    'max': 400,
                    'channels_qty': 20,
                },
            },
            'MiG-21Bis': {
                1: {
                    'radio_name': 'R-832',
                    'min': 80,
                    'max': 399.9,
                    'channels_qty': 20,
                },
            },
            'P-51D': {
                1: {
                    'radio_name': 'SCR552',
                    'min': 100,
                    'max': 156,
                    'channels_qty': 4,
                },
            },
            'TF-51D': {
                1: {
                    'radio_name': 'SCR552',
                    'min': 100,
                    'max': 156,
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
            valid_positive_int.validate(channel, 'get_frequency')
            if 1 <= channel <= self.channels_qty:
                return float(self._section_channels[channel])
            else:
                raise ValueError(
                    'channel {} for radio {} in aircraft {}'.format(channel, self.radio_name,
                                                                    self.parent_unit.unit_name))

        def set_frequency(self, channel, frequency):
            valid_positive_int.validate(channel, 'set_frequency')
            valid_float.validate(frequency, 'set_frequency')
            if 1 <= channel <= self.channels_qty:
                # noinspection PyTypeChecker
                if self.min <= frequency <= self.max:
                    self._section_channels[channel] = float(frequency)
                else:
                    raise ValueError(
                        'frequency {} for channel {} for radio {} in aircraft {}'.format(frequency, channel,
                                                                                         self.radio_name,
                                                                                         self.parent_unit.unit_name))
            else:
                raise ValueError(
                    'channel {} for radio {} in aircraft {}'.format(channel, self.radio_name,
                                                                    self.parent_unit.unit_name))

    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index)

    @property
    def radio_presets(self):
        if self.skill == 'Client' and self.unit_type in FlyingUnit.RadioPresets.radio_enum.keys():
            for k in self._section_unit['Radio']:
                yield FlyingUnit.RadioPresets(self, k)
        else:
            raise TypeError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    def get_radio_by_name(self, radio_name):
        if self.has_radio_presets:
            for k in FlyingUnit.RadioPresets.radio_enum[self.unit_type].keys():
                if radio_name == FlyingUnit.RadioPresets.radio_enum[self.unit_type][k]['radio_name']:
                    return FlyingUnit.RadioPresets(self, k)
            raise TypeError('{} for aircraft: {}'.format(radio_name, self.unit_type))
        else:
            raise TypeError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    def get_radio_by_number(self, radio_number):
        if self.has_radio_presets:
            if radio_number in FlyingUnit.RadioPresets.radio_enum[self.unit_type].keys():
                return FlyingUnit.RadioPresets(self, radio_number)
            else:
                raise TypeError(
                    'radio number {} for aircraft: {}'.format(radio_number, self.unit_type))
        else:
            raise TypeError('unit #{}: {}'.format(self.unit_id, self.unit_name))

    @property
    def livery(self):
        return self._section_unit['livery_id']

    @livery.setter
    def livery(self, value):
        # TODO validate livery_id
        valid_str.validate(value, 'unit livery')
        self._section_unit['livery_id'] = value

    @property
    def onboard_num(self):
        return self._section_unit['onboard_num']

    @onboard_num.setter
    def onboard_num(self, value):
        FlyingUnit.validator_board_number.validate(value, 'unit onboard number')
        self._section_unit['onboard_num'] = value


class Helicopter(FlyingUnit):
    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index)


class Plane(FlyingUnit):
    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index)


class Vehicle(BaseUnit):
    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index)


class Ship(BaseUnit):
    def __init__(self, mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index):
        super().__init__(mission_dict, l10n, coa_color, country_index, group_category, group_index, unit_index)

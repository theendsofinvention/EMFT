# coding=utf-8
"""
Nope
"""

from os.path import exists
from time import sleep

from base_utils.base_utils import decrypt_bytes, encrypt, get_cipher
from custom_logging.custom_logging import make_logger, Logged
from yaml import dump as ydump, load as yload

LOGGER = make_logger('roster')
ROSTER_KEY = get_cipher('p3z9n8M49xriTSnRTTjTvNr9u28qve1r')


class RosterError:
    class BaseRosterError(Exception):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)

    class ObjectExistsError(BaseRosterError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)

    class ObjectDoesNotExistsError(BaseRosterError):
        def __init__(self, msg, *args, **kwargs):
            super().__init__(msg, *args, **kwargs)


class Container:
    def __init__(self, name, parent=None):
        self.state = {}
        self.__dict__ = self.state
        self.name = name
        self.parent = parent
        self.default_ac = 'None'
        self.default_skin = 'None'
        self.__children = dict()

    @property
    def children(self):
        for k in sorted(self.__children.keys()):
            yield self.__children[k]

    def add_child(self, child):
        if child.name in self.__children.keys():
            raise RosterError.ObjectExistsError('{} already exists: {}'.format(self.__class__.__name__, child.name))
        self.__children[child.name] = child

    def remove(self, child):
        if child.name not in self.__children.keys():
            raise RosterError.ObjectDoesNotExistsError(
                '{} does not exists: {}'.format(self.__class__.__name__, child.name))
        del self.__children[child.name]

    def __str__(self):
        return '{}: [{}]'.format(self.name, ', '.join([str(child) for child in self.__children]))

        # def __repr__(self):


class Wing(Container):
    def __init__(self, name):
        super().__init__(name)
        self.parent = None


class Squad(Container):
    def __init__(self, name, parent_wing, default_ac=None, default_skin=None):
        super().__init__(name)
        self.parent = parent_wing
        self.default_ac = default_ac or AC('None')
        self.default_skin = default_skin or Skin('None')


class Pilot(Container):
    def __init__(self, name, parent_squad, default_ac=None, default_skin=None):
        super().__init__(name)
        self.parent = parent_squad
        self.default_ac = default_ac or AC('None')
        self.default_skin = default_skin or Skin('None')


class AC(Container):
    def __init__(self, name, default_skin=None):
        super().__init__(name)
        self.default_skin = default_skin or 'None'


class Skin(Container):
    def __init__(self, name):
        super().__init__(name)
        # self.parent = parent_ac


class Roster(Container, Logged):
    lock = True

    file_path = None

    encode = True

    def __init__(self):
        super().__init__('roster')
        if Roster.file_path is None:
            raise NotImplementedError('You dawg, thou might wanna define a path for that rooster, hey ?')

    def add_wing(self, wing_obj):
        if not isinstance(wing_obj, Wing):
            raise Exception()  # TODO implement
        self.add_child(wing_obj)

    def remove_wing(self, wing_obj):
        if not isinstance(wing_obj, Wing):
            raise Exception()  # TODO implement
        self.remove(wing_obj)

    @property
    def wings(self):
        for wing in self.children:
            yield wing

    def get_wing_by_name(self, wing_name):
        for wing in self.wings:
            if wing.name == wing_name:
                return wing
        return None

    def get_squad_by_name(self, squad_name):
        for wing in self.wings:
            for squad in wing.children:
                if squad.name == squad_name:
                    return squad
        return None

    def read(self):
        """
        Reads the local Config file
        """
        while not Roster.lock:
            sleep(0.1)
        Roster.lock = False
        try:
            if exists(Roster.file_path):
                if Roster.encode:
                    with open(Roster.file_path, 'rb') as f:
                        self.__dict__ = yload(decrypt_bytes(f.read(), ROSTER_KEY))
                else:
                    with open(Roster.file_path) as f:
                        try:
                            self.__dict__ = yload(f.read())
                        except ValueError:
                            pass
        except:
            LOGGER.exception('error while reading Roster from {}'.format(Roster.file_path))
        finally:
            Roster.lock = True

    def write(self):
        """
        Writes the current config to the local Config file
        """
        LOGGER.debug('writing roster file to {}'.format(Roster.file_path))
        while not Roster.lock:
            sleep(0.1)
        Roster.lock = False
        LOGGER.debug('lock is free, writing now')
        try:
            if Roster.encode:
                LOGGER.debug('encoding roster')
                with open(Roster.file_path, mode='wb') as f:
                    f.write(encrypt(ydump(self.__dict__), ROSTER_KEY))
            else:
                LOGGER.debug('writing plain')
                with open(Roster.file_path, mode='w') as f:
                    f.write(ydump(self.__dict__))
        except:
            LOGGER.exception('error while writing Roster to {}'.format(Roster.file_path))
        finally:
            LOGGER.debug('write successfull, freeing lock')
            Roster.lock = True


if __name__ == '__main__':
    make_logger()
    Roster.file_path = 'test.roster'
    Roster.encode = False
    roster = Roster()
    roster.read()
    print(roster)
    exit(0)
    _3rd = Wing('3rd')
    roster.add_wing(_3rd)
    _132nd = Wing('132nd')
    roster.add_wing(_132nd)
    _319th = Squad('319th', _3rd)
    _3rd.add_child(_319th)
    etcher = Pilot('etcher', _319th)
    _319th.add_child(etcher)
    print(roster)
    roster.write()

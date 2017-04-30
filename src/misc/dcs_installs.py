# coding=utf-8

try:
    import winreg
except ImportError:
    from unittest.mock import MagicMock

    winreg = MagicMock()

import os
import re

from utils import make_logger, Path

from src import global_
from src.cfg.cfg import Config

logger = make_logger(__name__)

A_REG = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


class InvalidSavedGamesPath(ValueError):
    pass


class InvalidInstallPath(ValueError):
    pass


class AutoexecCFG:
    RE_VFS = re.compile(r'table\.insert\(options\.graphics\.VFSTexturePaths, "(?P<path>.*)"\)')

    def __init__(self, path):
        self._path = Path(path)
        self._vfs = set()
        self.parse_vfs()

    @property
    def mounted_vfs_paths(self) -> set:
        return self._vfs

    def parse_vfs(self):
        logger.debug('reading "{}"'.format(self._path.abspath()))
        with open(self._path.abspath()) as f:
            lines = f.readlines()
        if lines:
            for line in lines:
                m = self.RE_VFS.match(line)
                if m:
                    self._vfs.add(m.group('path'))
        logger.debug('found {} VFS path(s)'.format(len(self._vfs)))


class DCSSkin:
    def __init__(self, name, ac, root_folder, skin_nice_name):
        self.name = name
        self.ac = ac
        self.root_folder = root_folder
        self.skin_nice_name = skin_nice_name or name

    def __repr__(self):
        return 'DCSSkin("{}", "{}", "{}", "{}")'.format(
            self.name, self.ac, self.root_folder, self.skin_nice_name
        )


class DCSInstall:
    RE_SKIN_NICE_NAME = re.compile(r'name = "(?P<skin_nice_name>.*)"')

    def __init__(self, install_path, saved_games_path, version, label):
        self.__install = install_path if install_path else None
        self.__sg = saved_games_path if saved_games_path else None
        self.__version = str(version) if version else None
        self.__label = label
        self.__skins = {}
        self.__autoexec = None

    @staticmethod
    def __check_path(path: Path or None, exc):
        if path is not None:
            path = Path(path)
            if not all([path.exists(), path.isdir()]):
                raise exc(path)

    @property
    def label(self):
        return self.__label

    @property
    def install_path(self):
        self.__check_path(self.__install, InvalidInstallPath)
        return str(Path(self.__install).abspath()) if self.__install is not None else None

    @property
    def saved_games(self):
        self.__check_path(self.__sg, InvalidSavedGamesPath)
        return str(Path(self.__sg).abspath()) if self.__sg is not None else None

    @property
    def version(self):
        return self.__version

    @property
    def skins(self):
        return self.__skins

    def discover_skins(self):

        self.__skins = {}

        def scan_dir(p: Path):
            if not p.exists():
                logger.debug('skipping absent folder: {}'.format(p.abspath()))
                return
            logger.debug('scanning for skins in: {}'.format(p.abspath()))
            for ac_folder in os.scandir(p.abspath()):
                # logger.debug('scanning for skins in: {}'.format(ac_folder.path))
                ac_name = ac_folder.name
                if ac_folder.is_dir():
                    for skin_folder in os.scandir(ac_folder.path):
                        # logger.debug('scanning for skins in: {}'.format(skin_folder.path))
                        skin_name = skin_folder.name
                        skin_nice_name = None

                        try:
                            with open(Path(skin_folder.path).join('description.lua')) as f:
                                lines = f.readlines()
                                for line in lines:
                                    m = self.RE_SKIN_NICE_NAME.match(line)
                                    if m:
                                        skin_nice_name = m.group('skin_nice_name')
                        except FileNotFoundError:
                            pass

                        self.__skins['{}_{}'.format(ac_name, skin_name)] = DCSSkin(
                            skin_name, ac_name, str(skin_folder.path), skin_nice_name
                        )

        scan_dir(Path(self.install_path).joinpath('bazar', 'liveries'))
        scan_dir(Path(self.saved_games).joinpath('liveries'))

        logger.debug('found {} skins'.format(len(self.__skins)))

    @property
    def autoexec_cfg(self) -> AutoexecCFG:
        return self.__autoexec

    def discover_autoexec(self):
        autoexec_cfg_path = Path(self.__sg).joinpath('config', 'autoexec.cfg')
        if autoexec_cfg_path.exists():
            logger.debug('reading {}'.format(autoexec_cfg_path.abspath()))
            self.__autoexec = AutoexecCFG(autoexec_cfg_path)
        else:
            logger.warning('file does not exist: {}'.format(autoexec_cfg_path.abspath()))


class DCSInstalls:
    def __init__(self):
        self._database = {}
        self._installs = {}
        self.installs_props = {
            'stable': {
                'reg_key': global_.DCS['reg_key']['stable'],
                'sg_default': 'DCS',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_stable',
                'autoexec_cfg': None,
            },
            'beta': {
                'reg_key': global_.DCS['reg_key']['beta'],
                'sg_default': 'DCS.openbeta',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_beta',
                'autoexec_cfg': None,
            },
            'alpha': {
                'reg_key': global_.DCS['reg_key']['alpha'],
                'sg_default': 'DCS.openalpha',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_alpha',
                'autoexec_cfg': None,
            },
        }

    @staticmethod
    def discover_saved_games_path() -> Path:
        logger.debug('searching for base "Saved Games" folder')
        try:
            logger.debug('trying "User Shell Folders"')
            with winreg.OpenKey(A_REG,
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as aKey:
                # noinspection SpellCheckingInspection
                base_sg = Path(winreg.QueryValueEx(aKey, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")[0])
        except FileNotFoundError:
            logger.debug('failed, trying "Shell Folders"')
            try:
                with winreg.OpenKey(A_REG,
                                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as aKey:
                    # noinspection SpellCheckingInspection
                    base_sg = Path(winreg.QueryValueEx(aKey, "{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}")[0])
            except FileNotFoundError:
                logger.debug('darn it, another fail, falling back to "~"')
                base_sg = Path('~').expanduser().abspath()
        return base_sg

    def _get_base_saved_games_path(self):
        if Config().saved_games_path is None:
            logger.debug('no Saved Games path in Config, looking it up')
            base_sg = self.discover_saved_games_path()
        else:
            logger.debug('Saved Games path found in Config')
            base_sg = Path(Config().saved_games_path)
        base_sg.must_be_a_dir(InvalidSavedGamesPath)
        logger.debug('using Saved Games path: {}'.format(base_sg.abspath()))
        return base_sg

    def __discover_install_path(self, k) -> Path or None:
        try:
            logger.debug('{}: looking up in registry'.format(k))
            with winreg.OpenKey(A_REG,
                                r'Software\Eagle Dynamics\{}'.format(
                                    self.installs_props[k]['reg_key'])) as aKey:
                p = Path(winreg.QueryValueEx(aKey, 'Path')[0])
                logger.debug('{}: found path: {}'.format(k, p.abspath()))
                return p
        except FileNotFoundError:
            logger.debug('{}: no install path found'.format(k))
            return None

    def get_install_path(self, k) -> Path or None:
        logger.debug('{}: reading config'.format(k))
        install_path = self.__discover_install_path(k)
        if install_path is None:
            logger.debug('{}: no install path found'.format(k))
            return None
        install_path = Path(install_path)
        install_path.must_be_a_dir(InvalidInstallPath)
        return install_path

    def get_variant(self, k):
        install_path = Path(self.installs_props[k]['install'])
        sg_path = Path(Config().saved_games_path)
        variant_path = Path(install_path.joinpath('dcs_variant.txt'))
        logger.debug('{}: looking for variant: {}'.format(k, variant_path.abspath()))
        if variant_path.exists():
            logger.debug('{}: found variant: "{}"; reading'.format(k, variant_path.abspath()))
            return sg_path.abspath().joinpath('DCS.{}'.format(variant_path.text()))
        else:
            logger.debug('{}: no variant, falling back to default: {}'.format(k, self.installs_props[k]['sg_default']))
            return sg_path.abspath().joinpath(self.installs_props[k]['sg_default'])

    def discover_dcs_installations(self):
        logger.debug('looking for local DCS installations')

        if Config().saved_games_path is None:
            Config().saved_games_path = self._get_base_saved_games_path()

        for k in self.installs_props:
            logger.debug('{}: searching for paths'.format(k))

            install_path = self.get_install_path(k)
            if install_path is None:
                logger.info('{}: no installation found, skipping'.format(k))
                continue

            exe = Path(install_path.joinpath('bin').joinpath('dcs.exe'))
            if not exe.exists():
                logger.info('{}: no executable found, skipping'.format(k))
                continue

            logger.debug('{}: install found: {}'.format(k, install_path.abspath()))

            self.installs_props[k]['install'] = str(install_path.abspath())
            self.installs_props[k]['sg'] = self.get_variant(k)
            self.installs_props[k]['version'] = exe.get_win32_file_info().file_version

            logger.debug('{}: set "Saved Games" path to: {}'.format(k, self.installs_props[k]['sg']))

            install = DCSInstall(*self.__get_props(k))

            self._installs[k] = install

            install.discover_skins()
            install.discover_autoexec()

    def __get_props(self, channel):
        return self.installs_props[channel]['install'], \
               self.installs_props[channel]['sg'], self.installs_props[channel]['version'], channel

    @property
    def stable(self) -> DCSInstall:
        return self._installs.get('stable', None)

    @property
    def beta(self) -> DCSInstall:
        return self._installs.get('beta', None)

    @property
    def alpha(self) -> DCSInstall:
        return self._installs.get('alpha', None)

    @property
    def present_dcs_installations(self):
        for x in self.__iter__():
            if x.install_path:
                yield x

    def __iter__(self) -> DCSInstall:
        yield self.stable
        yield self.beta
        yield self.alpha

    def __getitem__(self, item) -> DCSInstall:
        return getattr(self, item)


dcs_installs = DCSInstalls()

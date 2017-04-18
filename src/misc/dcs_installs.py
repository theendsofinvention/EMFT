# coding=utf-8

try:
    import winreg
except ImportError:
    from unittest.mock import MagicMock

    winreg = MagicMock()

from utils import make_logger, Path, Singleton

from src import global_
from src.cfg.cfg import Config

logger = make_logger(__name__)

A_REG = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)


class InvalidSavedGamesPath(ValueError):
    pass


class InvalidInstallPath(ValueError):
    pass


class InvalidVariantPath(ValueError):
    pass


class DCSInstall:
    def __init__(self, install_path, saved_games_path, version, label):
        self.__install = install_path if install_path else None
        self.__sg = saved_games_path if saved_games_path else None
        self.__version = str(version) if version else None
        self.__label = label

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


class DCSInstalls(metaclass=Singleton):
    def __init__(self):
        self.installs = {
            'stable': {
                'reg_key': global_.DCS['reg_key']['stable'],
                'sg_default': 'DCS',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_stable',
            },
            'beta': {
                'reg_key': global_.DCS['reg_key']['beta'],
                'sg_default': 'DCS.openbeta',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_beta',
            },
            'alpha': {
                'reg_key': global_.DCS['reg_key']['alpha'],
                'sg_default': 'DCS.openalpha',
                'install': None,
                'sg': None,
                'version': None,
                'config_attrib': 'dcs_install_path_alpha',
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
                                    self.installs[k]['reg_key'])) as aKey:
                p = Path(winreg.QueryValueEx(aKey, 'Path')[0])
                logger.debug('{}: found path: {}'.format(k, p.abspath()))
                return p
        except FileNotFoundError:
            logger.debug('{}: no install path found'.format(k))
            return None

    def get_install_path(self, k) -> Path or None:
        logger.debug('{}: reading config'.format(k))
        install_path = getattr(Config(), self.installs[k]['config_attrib'])
        logger.debug('{}: config value: {}'.format(k, install_path))
        if install_path is None:
            install_path = self.__discover_install_path(k)
        if install_path is None:
            logger.debug('{}: no install path found'.format(k))
            return None
        install_path = Path(install_path)
        install_path.must_be_a_dir(InvalidInstallPath)
        return install_path

    def get_variant(self, k):
        install_path = Path(self.installs[k]['install'])
        sg_path = Path(Config().saved_games_path)
        variant_path = Path(install_path.joinpath('dcs_variant.txt'))
        logger.debug('{}: looking for variant: {}'.format(k, variant_path.abspath()))
        if variant_path.exists():
            logger.debug('{}: found variant: "{}"; reading'.format(k, variant_path.abspath()))
            return sg_path.abspath().joinpath('DCS.{}'.format(variant_path.text()))
        else:
            logger.debug('{}: no variant, falling back to default: {}'.format(k, self.installs[k]['sg_default']))
            return sg_path.abspath().joinpath(self.installs[k]['sg_default'])

    def discover_dcs_installations(self):
        logger.debug('looking for local DCS installations')

        if Config().saved_games_path is None:
            Config().saved_games_path = self._get_base_saved_games_path()

        for k in self.installs:
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

            self.installs[k]['install'] = str(install_path.abspath())
            self.installs[k]['sg'] = self.get_variant(k)
            self.installs[k]['version'] = exe.get_win32_file_info().file_version

            logger.debug('{}: set "Saved Games" path to: {}'.format(k, self.installs[k]['sg']))

    def __get_props(self, channel):
        return self.installs[channel]['install'], \
               self.installs[channel]['sg'], \
               self.installs[channel]['version'], \
               channel

    @property
    def stable(self) -> DCSInstall:
        return DCSInstall(*self.__get_props('stable'))

    @property
    def beta(self) -> DCSInstall:
        return DCSInstall(*self.__get_props('beta'))

    @property
    def alpha(self) -> DCSInstall:
        return DCSInstall(*self.__get_props('alpha'))

    def __iter__(self) -> DCSInstall:
        yield self.stable
        yield self.beta
        yield self.alpha

    def __getitem__(self, item) -> DCSInstall:
        return getattr(self, item)

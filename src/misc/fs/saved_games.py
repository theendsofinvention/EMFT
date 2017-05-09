# coding=utf-8
from utils import Path, make_logger
from ._winreg import winreg, A_REG
from src.cfg import Config


logger = make_logger(__name__)


def _get_saved_games_from_registry() -> Path:
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


def discover_saved_games_path():
    if Config().saved_games_path is None:
        logger.debug('no Saved Games path in Config, looking it up')
        base_sg = _get_saved_games_from_registry()

    else:
        logger.debug('Saved Games path found in Config')
        base_sg = Path(Config().saved_games_path)
        try:
            base_sg.must_be_a_dir(NotADirectoryError)
        except NotADirectoryError:
            base_sg = _get_saved_games_from_registry()

    logger.debug('using Saved Games path: {}'.format(base_sg.abspath()))
    return base_sg


saved_games_path = discover_saved_games_path()

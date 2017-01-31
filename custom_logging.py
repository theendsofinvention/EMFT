# coding=utf-8
"""
Custom loggers
"""
import logging
import os

DEBUG = logging.DEBUG
WARNING = logging.WARNING
INFO = logging.INFO
ERROR = logging.ERROR
WARN = WARNING
ERR = ERROR


def make_logger(module_name='__main__', log_file_path=None, logging_level=logging.DEBUG, custom_handler=None) -> logging.Logger:
    """Creates a module-specific logger
    :param log_file_path: path to the logfile for this logger; if None (default), no file will be created
    :param custom_handler: optional logging handler to add to the logger
    :param logging_level: minimal level of logging (anything below will be ignored)
    :param module_name: name of the module this logger pertains to
    :return: logger object
    """
    if logging_level not in {logging.DEBUG, logging.INFO, logging.WARNING, logging.WARN, logging.ERROR}:
        raise ValueError('unknown logging level: {}'.format(logging_level))
    if module_name == '__main__':
        return __setup_logger(log_file_path=log_file_path, logging_level=logging_level, custom_handler=custom_handler)
    else:
        sub_logger = logging.getLogger(".".join(['main', module_name]))
        if custom_handler is not None:
            sub_logger.addHandler(custom_handler)
        return sub_logger


class ParasiteLogger:

    def __init__(self, prefix: str, logger: logging.Logger):
        self.__parasite_logger_prefix = prefix
        self.__logger = logger

    def debug(self, txt: str):
        self.__logger.debug('{}: {}'.format(self.__parasite_logger_prefix, txt))

    def info(self, txt: str):
        self.__logger.info('{}: {}'.format(self.__parasite_logger_prefix, txt))

    def warning(self, txt: str):
        self.__logger.warning('{}: {}'.format(self.__parasite_logger_prefix, txt))

    def error(self, txt: str):
        self.__logger.error('{}: {}'.format(self.__parasite_logger_prefix, txt))

    def critical(self, txt: str):
        self.__logger.critical('{}: {}'.format(self.__parasite_logger_prefix, txt))


class Logged:
    """
    Adds a logger object to child class
    """

    logger = None

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(".".join(["main", self.__class__.__name__]))


def __setup_logger(logger_name="main", log_file_path=None, logging_level=logging.DEBUG, custom_handler=None):
    """
    Creates a logger object
    :param logger_name: name of the logger, defaults to "main"
    :param logging_level: minimal level of logging (anything below will be ignored)
    :param custom_handler: optional logging handler to add to the logger
    :param log_file_path: path to the logfile for this logger; if None (default), no file will be created
    :return: logger object
    """
    if logging_level not in [logging.DEBUG, logging.INFO, logging.WARNING, logging.WARN, logging.ERROR]:
        raise ValueError('unknown logging level: {}'.format(logging_level))

    if log_file_path is not None and os.path.exists(log_file_path):
        os.remove(log_file_path)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)

    if log_file_path is not None:
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging_level)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s: [%(levelname)8s]: (%(threadName)-9s) - %(name)s - %(funcName)s - %(message)s'))
        logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    ch.setFormatter(
        logging.Formatter('%(asctime)s: [%(levelname)8s]: (%(threadName)-9s) - %(name)s - %(funcName)s - %(message)s'))
    logger.addHandler(ch)

    if custom_handler:
        logger.addHandler(custom_handler)

    if log_file_path is None:
        logger.debug('logger output will *not* be written to a file')

    return logger

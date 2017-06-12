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

CH = None
FH = None


def make_logger(
        logger_name='__main__',
        log_file_path=None,
        fh_level=logging.DEBUG,
        ch_level=logging.DEBUG,
        custom_handler=None) -> logging.Logger:
    """Creates a module-specific logger
    :param log_file_path: path to the logfile for this logger; if None (default), no file will be created
    :param custom_handler: optional logging handler to add to the logger
    :param fh_level: minimal level of logging for the logfile handler (anything below will be ignored)
    :param ch_level: minimal level of logging for the console handler (anything below will be ignored)
    :param logger_name: name of the module this logger pertains to
    :return: logger object
    """

    if ch_level not in {logging.DEBUG, logging.INFO, logging.WARNING, logging.WARN, logging.ERROR}:
        raise ValueError('unknown logging level: {}'.format(ch_level))

    if fh_level not in {logging.DEBUG, logging.INFO, logging.WARNING, logging.WARN, logging.ERROR}:
        raise ValueError('unknown logging level: {}'.format(fh_level))

    if logger_name == '__main__':
        return __setup_logger(log_file_path=log_file_path, fh_level=fh_level, ch_level=ch_level,
                              custom_handler=custom_handler)

    else:
        sub_logger = logging.getLogger('__main__.{}'.format(logger_name))

        if custom_handler is not None:
            sub_logger.addHandler(custom_handler)

        return sub_logger


class Logged:
    """
    Adds a logger object to child class
    """

    logger = None

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        self.logger = make_logger(self.__class__.__name__)


def __setup_logger(
        logger_name='__main__',
        log_file_path=None,
        fh_level=logging.DEBUG,
        ch_level=logging.DEBUG,
        custom_handler=None):
    """
    Creates a logger object
    :param logger_name: name of the logger, defaults to "__main__"
    :param fh_level: minimal level of logging (anything below will be ignored)
    :param custom_handler: optional logging handler to add to the logger
    :param log_file_path: path to the logfile for this logger; if None (default), no file will be created
    :return: logger object
    """
    global CH, FH

    if log_file_path is not None and os.path.exists(log_file_path):
        os.remove(log_file_path)

    logger = logging.getLogger(logger_name)
    logger.setLevel(fh_level)

    if log_file_path is not None:
        FH = logging.FileHandler(log_file_path)
        FH.setLevel(fh_level)
        FH.setFormatter(
            logging.Formatter(
                '%(asctime)s: [%(levelname)8s]: (%(threadName)-9s) - %(name)s - %(funcName)s - %(message)s'
            )
        )
        logger.addHandler(FH)

    CH = logging.StreamHandler()
    CH.setLevel(ch_level)
    CH.setFormatter(
        logging.Formatter(
            '%(asctime)s: [%(levelname)8s]: (%(threadName)-9s) - %(name)s - %(funcName)s - %(message)s'
        )
    )
    logger.addHandler(CH)

    if custom_handler:
        logger.addHandler(custom_handler)

    if log_file_path is None:
        logger.warning('logger output will *not* be written to a file')

    return logger

# coding=utf-8
"""
Custom loggers
"""
import abc
import logging
import os
import typing

DEBUG = logging.DEBUG
WARNING = logging.WARNING
INFO = logging.INFO
ERROR = logging.ERROR
WARN = WARNING
ERR = ERROR
CRITICAL = logging.CRITICAL

CH = None
FH = None


def make_logger(
    logger_name='__main__',
    log_file_path=None,
    fh_level=logging.DEBUG,
    ch_level=logging.DEBUG,
    custom_handler=None
) -> logging.Logger:
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


def __setup_logger(  # noqa: N802
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


LOGGING_LEVELS = {
    'NOTSET': 0,
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50,
}
LOGGING_NAMES = {LOGGING_LEVELS[k]: k for k in LOGGING_LEVELS}


def _sanitize_level(level):
    if isinstance(level, int):
        return level
    elif level in LOGGING_LEVELS:
        return LOGGING_LEVELS[level]
    else:
        raise KeyError(level)


class Records:
    def __init__(self, records: typing.List[logging.LogRecord]):
        self._records = records

    @staticmethod
    def _sanitize_level(level):
        return _sanitize_level(level)

    def __filter(self, filter_func):
        self._records = [rec for rec in filter(filter_func, self._records)]
        return self

    def filter_by_level(self, minimum_level=logging.NOTSET):

        minimum_level = self._sanitize_level(minimum_level)

        def filter_func(rec: logging.LogRecord):
            return rec.levelno >= minimum_level

        return self.__filter(filter_func)

    def _filter_by_str(self, text: str or None, rec_attrib):

        if text is None:
            return self

        def filter_func(rec: logging.LogRecord):
            return text.lower() in getattr(rec, rec_attrib)

        return self.__filter(filter_func)

    def filter_by_message(self, text: str or None):
        return self._filter_by_str(text, 'msg')

    def filter_by_module(self, text: str or None):
        return self._filter_by_str(text, 'module')

    def filter_by_thread(self, text: str or None):
        return self._filter_by_str(text, 'threadName')

    def __iter__(self) -> typing.Generator[logging.LogRecord, None, None]:
        for x in self._records:
            yield x

    def __len__(self):
        return len(self._records)


class PersistentLoggingFollower(logging.Formatter):
    @property
    @abc.abstractmethod
    def fmt_(self):
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def datefmt_(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def handle_record(self, record: logging.LogRecord):
        raise NotImplementedError()

    def __init__(self):
        logging.Formatter.__init__(self, self.fmt_, self.datefmt_)

    @staticmethod
    def _sanitize_level(level):
        return _sanitize_level(level)

    @staticmethod
    def filter_record(
        record,
        minimum_level=logging.NOTSET,
        msg_filter: str or None = None,
        module_filter: str or None = None,
        thread_filter: str or None = None,
    ):
        records = Records([record])
        records \
            .filter_by_level(minimum_level) \
            .filter_by_message(msg_filter) \
            .filter_by_module(module_filter) \
            .filter_by_thread(thread_filter)
        return len(records) > 0

    @staticmethod
    def filter_records(
        minimum_level=logging.NOTSET,
        msg_filter: str or None = None,
        module_filter: str or None = None,
        thread_filter: str or None = None,
    ) -> typing.Iterator[logging.LogRecord]:
        records = Records(persistent_logging_handler.records)
        records \
            .filter_by_level(minimum_level) \
            .filter_by_message(msg_filter) \
            .filter_by_module(module_filter) \
            .filter_by_thread(thread_filter)
        for rec in records:
            yield rec


class PersistentLoggingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        self._records.append(record)
        for follower in self._followers:
            follower.handle_record(record)

    def __init__(self):
        logging.Handler.__init__(self)
        self._records = []
        self._followers = []

    def add_follower(self, follower: PersistentLoggingFollower):
        self._followers.append(follower)

    def del_follower(self, follower: PersistentLoggingFollower):
        self._followers.remove(follower)

    @property
    def records(self):
        return self._records


def get_console_handler() -> logging.Handler:
    # noinspection PyTypeChecker
    return CH


persistent_logging_handler = PersistentLoggingHandler()

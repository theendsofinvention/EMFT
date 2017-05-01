# coding=utf-8


import abc
import logging
import typing

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

    def filter_records(
            self,
            minimum_level=logging.NOTSET,
            msg_filter: str or None = None,
            module_filter: str or None = None,
            thread_filter: str or None = None,
    ):
        records = Records(persistent_logging_handler.records)
        records\
            .filter_by_level(minimum_level)\
            .filter_by_message(msg_filter)\
            .filter_by_module(module_filter)\
            .filter_by_thread(thread_filter)
        for rec in records:
            self.handle_record(rec)


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


persistent_logging_handler = PersistentLoggingHandler()

# coding=utf-8
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from emft.core.logging import make_logger
from emft.core.threadpool import ThreadPool
from emft.gui.main_ui_threading_adapter import MainUiThreadingAdapter

LOGGER = make_logger(__name__)


class MainGuiWorker(QObject):
    """
    Sits in the main EventLoop, and reads a blocking queue of things to run.

    When somethings pops up, sends a nice Qt Signal to the main EventLoop.
    """

    def __init__(self, signal, queue):
        QObject.__init__(self)
        self.signal = signal
        self.queue = queue

    def run(self):
        while True:
            obj_name, func, args, kwargs = self.queue.get()
            self.signal.emit(obj_name, func, args, kwargs)


class MainUiThreading(MainUiThreadingAdapter):
    """
    Encapsulates calls to the MainUi inside a Qt thread.

    Qt is very bitchy about changing anything in the main event loop directly; calls are deferred to the
    @classmethod "do", which puts them in a Queue so Qt can relax a tad and do the real work inside its
    own fucking safe space. Wuss.
    """
    threading_signal = pyqtSignal(object, object, object, object, name='threading_signal')

    def __init__(self):
        if not hasattr(self, 'threading_queue'):
            raise AttributeError('main_gui object is missing a threading_queue')
        if not hasattr(self, 'threading_signal'):
            raise AttributeError('main_gui object is missing a threading_signal')
        t = QThread()
        # noinspection PyUnresolvedReferences
        w = MainGuiWorker(self.threading_signal, self.threading_queue)
        w.moveToThread(t)
        # noinspection PyUnresolvedReferences
        t.started.connect(w.run)
        # noinspection PyUnresolvedReferences
        self.threading_signal.connect(self._do)
        t.start()
        self.__threading = {
            'thread': t,
            'worker': w,
        }
        self.__pool = ThreadPool(1, 'main_ui', False)

    @property
    def pool(self) -> ThreadPool:
        return self.__pool

    def _do(self, obj_name, func, args, kwargs):
        """
        Actually do the work
        :param obj_name: str or None; name of the attribute object holding func; MainUi if None
        :param func: method to call
        :param args: args to the methods
        :param kwargs: kwargs to the methods
        :return: False
        """
        if obj_name in [None, 'main_ui', 'main']:
            method = getattr(self, func, None)
        else:
            obj = getattr(self, obj_name, None)
            if obj is None:
                raise ValueError('unknown member of MainUI: {}'.format(obj_name))
            method = getattr(obj, func, None)
        _args = kwargs.pop('args', None)
        try:
            if _args:
                args = _args
            if method is None:
                raise ValueError('unknown method: {}'.format(func))
            if args and kwargs:
                method(*args, **kwargs)
            elif args:
                method(*args)
            elif kwargs:
                method(**kwargs)
            else:
                method()
        except TypeError:
            LOGGER.exception(
                f'method "{method}" of object "{func}" failed ([{args}], {{{kwargs}}})')

    @classmethod
    def do(cls, obj_name, func, *args, **kwargs):
        """
        Executes a Gui method inside the Qt main loop

        :param obj_name: attribute of MainUi instance that has the "func" method
        :param func: name of the method to run
        :param args: argument of the method
        :param kwargs: keyword arguments of the method
        """
        # noinspection PyProtectedMember,PyUnresolvedReferences
        cls.threading_queue.put((obj_name, func, args, kwargs))

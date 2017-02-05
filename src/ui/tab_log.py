# coding=utf-8

import logging

from PyQt5.QtWidgets import QPlainTextEdit

from src.cfg import Config
from src.sentry import SENTRY
from src.ui.base import VLayout, Combo, PushButton, HLayout
from src.ui.itab import iTab


class TabLog(iTab, logging.Handler):
    @property
    def tab_title(self) -> str:
        return 'Log'

    def __init__(self, parent=None):
        iTab.__init__(self, parent=parent)
        logging.Handler.__init__(self)

        self.levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
        }

        self.records = []

        self.setLevel(logging.DEBUG)
        self.setFormatter(
            logging.Formatter(
                '%(asctime)s: [%(levelname)8s]: %(message)s',
                '%H:%M:%S'
            )
        )

        self.combo = Combo(
            on_change=self.combo_changed,
            choices=[
                'DEBUG',
                'INFO',
                'WARNING',
                'ERROR'
            ]
        )

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)

        self._min_lvl = self.levels[Config().log_level]
        self.combo.set_index_from_text(Config().log_level)

        self.clear_btn = PushButton('Clear', self._clean)
        self.send_btn = PushButton('Send', self._send)

        self.setLayout(
            VLayout(
                [
                    HLayout(
                        [
                            (self.combo, dict(stretch=1)),
                            (self.clear_btn, dict(stretch=0)),
                            (self.send_btn, dict(stretch=0)),
                        ]
                    ),
                    self.log_text,
                ]
            )
        )

        logger = logging.getLogger('__main__')
        logger.addHandler(self)
        self._clean()

    def emit(self, record: logging.LogRecord):
        self.records.append(record)
        if record.levelno >= self._min_lvl:
            self.write(self.format(record))

    def write(self, msg):
        self.log_text.appendPlainText(msg)

    def combo_changed(self, new_value):
        Config().log_level = new_value
        self._set_log_level(new_value)

    def _send(self):
        for rec in self.records:
            assert isinstance(rec, logging.LogRecord)
            SENTRY.add_crumb(rec.msg, 'LOG:{}'.format(rec.module), rec.levelname)
        SENTRY.captureMessage('Logfile')
        self.write('Log file sent; thank you !')

    def _clean(self):
        self.log_text.clear()
        self.write('Application is ready')

    def _set_log_level(self, log_level):
        self._clean()
        self._min_lvl = self.levels[log_level]
        for rec in self.records:
            assert isinstance(rec, logging.LogRecord)
            if rec.levelno >= self._min_lvl:
                self.write(self.format(rec))

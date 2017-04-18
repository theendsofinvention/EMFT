# coding=utf-8
import abc

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QGroupBox, QBoxLayout, QSpacerItem, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, \
    QRadioButton, QComboBox, QShortcut, QCheckBox, QLineEdit, QLabel, QPlainTextEdit


class Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent, flags=Qt.Widget)


class GroupBox(QGroupBox):
    def __init__(self):
        QGroupBox.__init__(self)
        self.setContentsMargins(40, 0, 0, 0)


class _WithChildren:
    def add_children(self, children: list):
        for child in children:
            params = {}
            if isinstance(child, tuple):
                params = child[1]
                child = child[0]
            if isinstance(child, QBoxLayout):
                self.addLayout(child, **params)
            elif isinstance(child, QSpacerItem):
                self.addSpacerItem(child, **params)
            elif isinstance(child, QWidget):
                self.addWidget(child, **params)
            elif isinstance(child, int):
                self.addSpacing(child, **params)
            else:
                raise TypeError(type(child))

    # noinspection PyPep8Naming
    @abc.abstractmethod
    def addLayout(self, layout: QBoxLayout):
        """"""

    # noinspection PyPep8Naming
    @abc.abstractmethod
    def addWidget(self, widget: QWidget):
        """"""

    # noinspection PyPep8Naming
    @abc.abstractmethod
    def addSpacerItem(self, spacer: QSpacerItem):
        """"""

    # noinspection PyPep8Naming
    @abc.abstractmethod
    def addSpacing(self, spacer: int):
        """"""


class HLayout(QHBoxLayout, _WithChildren):
    def __init__(self, children: list):
        super(HLayout, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.add_children(children)


class VLayout(QVBoxLayout, _WithChildren):
    def __init__(self, children: list):
        super(VLayout, self).__init__()
        self.add_children(children)


class PushButton(QPushButton):
    def __init__(self, text, func: callable):
        QPushButton.__init__(self, text)
        # noinspection PyUnresolvedReferences
        self.clicked.connect(func)


class Checkbox(QCheckBox):
    def __init__(self, text, func: callable = None):
        QCheckBox.__init__(self, text)
        if func:
            # noinspection PyUnresolvedReferences
            self.toggled.connect(func)


class Radio(QRadioButton):
    def __init__(self, text, func: callable):
        QRadioButton.__init__(self, text)
        # noinspection PyUnresolvedReferences
        self.toggled.connect(func)


class Combo(QComboBox):
    def __init__(self, on_change: callable, choices: list = None, parent=None):
        QComboBox.__init__(self, parent=parent)
        if choices:
            self.addItems(choices)
        # noinspection PyUnresolvedReferences
        self.currentTextChanged.connect(on_change)

    def set_index_from_text(self, text):
        idx = self.findText(text, Qt.MatchExactly)
        if idx < 0:
            raise ValueError(text)
        self.setCurrentIndex(idx)


class Shortcut(QShortcut):
    def __init__(self, key_sequence: QKeySequence, parent: QWidget, func: callable):
        QShortcut.__init__(self, key_sequence, parent)
        # noinspection PyUnresolvedReferences
        self.activated.connect(func)


class LineEdit(QLineEdit):
    def __init__(self, text, func: callable = None):
        QLineEdit.__init__(self, text)
        if func:
            # noinspection PyUnresolvedReferences
            self.textChanged.connect(func)


class Label(QLabel):
    def __init__(self, text, text_color='black', bg_color='rgba(255, 255, 255, 10)'):
        QLabel.__init__(self, text)
        self.text_color = text_color
        self.bg_color = bg_color

    def __update_style_sheet(self):
        self.setStyleSheet('QLabel {{ background-color : {}; color : {}; }}'.format(self.bg_color, self.text_color))

    def set_text_color(self, color):
        self.text_color = color
        self.__update_style_sheet()

    def set_bg_color(self, color):
        self.bg_color = color
        self.__update_style_sheet()


class PlainTextEdit(QPlainTextEdit):

    def __init__(self, *, default_text='', read_only=False):
        QPlainTextEdit.__init__(self, default_text)
        self.setReadOnly(read_only)

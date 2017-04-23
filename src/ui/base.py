# coding=utf-8
import abc

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import QGroupBox, QBoxLayout, QSpacerItem, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, \
    QRadioButton, QComboBox, QShortcut, QCheckBox, QLineEdit, QLabel, QPlainTextEdit, QSizePolicy, QGridLayout, \
    QMessageBox


class Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent, flags=Qt.Widget)


class Expandable:
    # noinspection PyPep8Naming
    @abc.abstractmethod
    def setSizePolicy(self, w, h):
        pass

    def h_expand(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def v_expand(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

    def expand(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class GroupBox(QGroupBox):
    def __init__(self, title=None, layout=None):
        QGroupBox.__init__(self)
        self.setContentsMargins(40, 0, 0, 0)
        if title:
            self.setTitle(title)
        if layout:
            self.setLayout(layout)


class _WithChildren:
    def add_children(self, children: list):
        for child in children:
            params = {}
            if isinstance(child, tuple):
                params = child[1]
                child = child[0]
            if isinstance(child, QBoxLayout):
                self.addLayout(child, **params)
            elif isinstance(child, QGridLayout):
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


class GridLayout(QGridLayout):
    align = {
        'l': Qt.AlignLeft,
        'c': Qt.AlignCenter,
        'r': Qt.AlignRight,
    }

    def __init__(self, children: list, stretch: list = None, auto_right=True):
        QGridLayout.__init__(self)
        self.auto_right = auto_right
        self.add_children(children)
        if stretch:
            for x in range(len(stretch)):
                self.setColumnStretch(x, stretch[x])

    # noinspection PyArgumentList
    def add_children(self, children: list):
        for r in range(len(children)):
            child = children[r]
            for c in range(len(child)):
                if child[c] is None:
                    continue
                elif isinstance(child[c], QWidget):
                    if c == 0 and self.auto_right:
                        self.addWidget(child[c], r, c, Qt.AlignRight)
                    else:
                        self.addWidget(child[c], r, c)
                elif isinstance(child[c], tuple):
                    align = child[c][1].get('align', 'l')
                    span = child[c][1].get('span', [1, 1])
                    self.addWidget(child[c][0], r, c, *span, self.align[align])
                elif isinstance(child[c], QBoxLayout):
                    self.addLayout(child[c], r, c)
                elif isinstance(child[c], int):
                    self.addItem(VSpacer(child[c]))
                else:
                    raise ValueError('unmanaged child type: {}'.format(type(child[c])))


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


class LineEdit(QLineEdit, Expandable):
    def __init__(self, text, func: callable = None, read_only=False, clear_btn_enabled=False):
        QLineEdit.__init__(self, text)
        if func:
            # noinspection PyUnresolvedReferences
            self.textChanged.connect(func)
        self.setReadOnly(read_only)
        self.setClearButtonEnabled(clear_btn_enabled)


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


class Spacer(QSpacerItem):
    def __init__(self, w=1, h=1):
        QSpacerItem.__init__(self, w, h, QSizePolicy.Expanding, QSizePolicy.Expanding)


class HSpacer(QSpacerItem):
    def __init__(self, size: int = None):
        if size is None:
            QSpacerItem.__init__(self, 1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        else:
            QSpacerItem.__init__(self, size, 1)


class VSpacer(QSpacerItem):
    def __init__(self, size: int = None):
        if size is None:
            QSpacerItem.__init__(self, 1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            QSpacerItem.__init__(self, 1, size)


class WithMsgBoxAdapter():
    @abc.abstractmethod
    def msg(self, text: str, follow_up: callable = None, title: str = None):
        pass

    @abc.abstractmethod
    def error(self, text: str, follow_up: callable = None, title: str = None):
        pass

    @abc.abstractmethod
    def confirm(self, text: str, follow_up: callable, title: str = None, follow_up_on_no: callable = None):
        pass


class WithMsgBox(WithMsgBoxAdapter):
    def __init__(self, title: str, ico: str):
        self.title = title
        self.ico = ico

    def _run_box(
            self,
            text: str,
            follow_up: callable = None,
            title: str = None,
            is_question=False,
            follow_up_on_no: callable = None,
    ):

        msgbox = QMessageBox()

        msgbox.setWindowIcon(QIcon(self.ico))
        msgbox.setText(text)

        if title:
            msgbox.setWindowTitle(title)

        else:
            msgbox.setWindowTitle(self.title)

        if is_question:
            msgbox.addButton(QMessageBox.Yes)
            msgbox.addButton(QMessageBox.No)

        else:
            msgbox.addButton(QPushButton('Ok'), QMessageBox.YesRole)

        if is_question:

            if msgbox.exec() == QMessageBox.Yes:
                if follow_up:
                    follow_up()

            else:
                if follow_up_on_no:
                    follow_up_on_no()

        else:

            msgbox.exec()
            if follow_up:
                follow_up()

    def msg(self, text: str, follow_up: callable = None, title: str = None):
        self._run_box(text=text, follow_up=follow_up, title=title)

    def error(self, text: str, follow_up: callable = None, title: str = None):
        self._run_box(text=text, follow_up=follow_up, title=title)

    def confirm(self, text: str, follow_up: callable, title: str = None, follow_up_on_no: callable = None):

        if title is None:
            title = 'Please confirm'

        self._run_box(text=text, follow_up=follow_up, title=title, follow_up_on_no=follow_up_on_no, is_question=True)

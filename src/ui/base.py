# coding=utf-8
import abc
import typing
from abc import abstractmethod

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QSortFilterProxyModel, QAbstractItemModel, \
    QRegExp
from PyQt5.QtGui import QKeySequence, QIcon, QContextMenuEvent, QColor, QRegExpValidator
from PyQt5.QtWidgets import QGroupBox, QBoxLayout, QSpacerItem, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, \
    QRadioButton, QComboBox, QShortcut, QCheckBox, QLineEdit, QLabel, QPlainTextEdit, QSizePolicy, QGridLayout, \
    QMessageBox, QTableView, QAbstractItemView, QMenu, QMenuBar, QFileDialog, QTabWidget, QDoubleSpinBox, \
    QStyledItemDelegate, QStyleOptionViewItem
from utils import make_logger, Path


class Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent, flags=Qt.Widget)


LEFT_MARGIN = 10
RIGHT_MARGIN = 10
TOP_MARGIN = 15
BOTTOM_MARGIN = 10

DEFAULT_MARGINS = (LEFT_MARGIN, TOP_MARGIN, RIGHT_MARGIN, BOTTOM_MARGIN)

logger = make_logger(__name__)


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
        if title:
            self.setTitle(title)
        if layout:
            self.setLayout(layout)
        self.setContentsMargins(*DEFAULT_MARGINS)


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
        for r in range(len(children)):  # "r" is the row
            child = children[r]
            for c in range(len(child)):  # "c" is the column
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
                elif isinstance(child[c], QSpacerItem):
                    self.addItem(child[c])
                else:
                    raise ValueError('unmanaged child type: {}'.format(type(child[c])))


class HLayout(QHBoxLayout, _WithChildren):
    def __init__(self, children: list):
        """
        Creates a horizontal layout.
        Children can be either a single item, or a tuple including a configuration dictionary.
        Parameters that can be included in the configuration dictionary are:
            Stretch: "weight" of the item in the layout
        :param children: list of children
        """
        super(HLayout, self).__init__()
        self.setContentsMargins(*DEFAULT_MARGINS)
        self.add_children(children)


class VLayout(QVBoxLayout, _WithChildren):
    def __init__(self, children: list):
        """
        Creates a vertical layout.
        Children can be either a single item, or a tuple including a configuration dictionary.
        Parameters that can be included in the configuration dictionary are:
            Stretch: "weight" of the item in the layout

        :param children: list of children
        """
        super(VLayout, self).__init__()
        self.setContentsMargins(*DEFAULT_MARGINS)
        self.add_children(children)


class PushButton(QPushButton):
    def __init__(self, text, func: callable):
        QPushButton.__init__(self, text)
        # noinspection PyUnresolvedReferences
        self.clicked.connect(func)
        self.setStyleSheet('padding-left: 15px; padding-right: 15px;'
                           'padding-top: 3px; padding-bottom: 3px;')


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
        self.on_change = on_change
        if choices:
            self.addItems(choices)
        # noinspection PyUnresolvedReferences
        self.currentTextChanged.connect(on_change)

    def __enter__(self):
        try:
            # noinspection PyUnresolvedReferences
            self.currentTextChanged.disconnect()
        except TypeError:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # noinspection PyUnresolvedReferences
        self.currentTextChanged.connect(self.on_change)

    def set_index_from_text(self, text):
        try:
            # noinspection PyUnresolvedReferences
            self.currentTextChanged.disconnect()
        except TypeError:
            pass
        idx = self.findText(text, Qt.MatchExactly)
        if idx < 0:
            raise ValueError(text)
        self.setCurrentIndex(idx)
        # noinspection PyUnresolvedReferences
        self.currentTextChanged.connect(self.on_change)


class Shortcut(QShortcut):
    def __init__(self, key_sequence: QKeySequence, parent: QWidget, func: callable):
        QShortcut.__init__(self, key_sequence, parent)
        # noinspection PyUnresolvedReferences
        self.activated.connect(func)


class LineEdit(QLineEdit, Expandable):
    def __init__(self, text, on_text_changed: callable = None, read_only=False, clear_btn_enabled=False):
        QLineEdit.__init__(self, text)
        if on_text_changed:
            # noinspection PyUnresolvedReferences
            self.textChanged.connect(on_text_changed)
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


class Menu(QMenu):
    def __init__(self, title: str = '', parent=None):
        super(Menu, self).__init__(title, parent)
        self.actions = {}

    def add_action(self, text: str, func: callable):
        action = self.addAction(text)
        self.actions[action] = func


class MenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)
        raise NotImplementedError('plop')


class _TableViewWithRowContextMenu:
    # noinspection PyPep8Naming
    @abc.abstractmethod
    def selectionModel(self):
        """"""

    def __init__(self, menu=None):
        self._menu = menu

    # noinspection PyPep8Naming
    def contextMenuEvent(self, event):
        logger.debug('in')
        if self._menu:
            logger.debug('menu')
            if self.selectionModel().selection().indexes():
                selected_rows = set()
                logger.debug('indexes')
                for i in self.selectionModel().selection().indexes():
                    selected_rows.add(i.row())

                if selected_rows:

                    assert isinstance(self._menu, Menu)
                    assert isinstance(event, QContextMenuEvent)

                    action = self._menu.exec(event.globalPos())
                    if action:
                        func = self._menu.actions[action]
                        for row in selected_rows:
                            func(row)


class TableView(QTableView):
    def __init__(self, parent=None):
        super(TableView, self).__init__(parent=parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setSortingEnabled(True)
        self.verticalHeader().hide()

    def setModel(self, model: QAbstractItemModel):
        if isinstance(model, TableEditableModel):
            for i, delegate in enumerate(model.delegates):
                if delegate:
                    self.setItemDelegateForColumn(i, delegate)
        return super(TableView, self).setModel(model)


class TableViewWithSingleRowMenu(TableView, _TableViewWithRowContextMenu):
    def __init__(self, menu, parent=None):
        TableView.__init__(self, parent)
        _TableViewWithRowContextMenu.__init__(self, menu)


class TableProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(TableProxy, self).__init__(parent)
        self.setDynamicSortFilter(False)
        self._filter = None

    def default_sort(self):
        self.sort(0, Qt.AscendingOrder)

    def sort(self, p_int, order=None):
        super(TableProxy, self).sort(p_int, order)

    def filterAcceptsRow(self, row: int, index: QModelIndex):
        if self._filter:
            model = self.sourceModel()
            for column, filter_ in enumerate(self._filter):
                if filter_:
                    item_text = model.data(model.index(row, column), role=Qt.DisplayRole)
                    if filter_.lower() not in item_text.lower():
                        return False
        return True

    def filter(self, *args):
        self._filter = args
        self.invalidateFilter()


class TableModel(QAbstractTableModel):
    align = {
        'c': Qt.AlignCenter,
        'l': Qt.AlignLeft,
        'r': Qt.AlignRight,
        'vc': Qt.AlignVCenter,
    }

    def __init__(
            self,
            data: list,
            header_data: list,
            parent=None,
            bg: list = None,
            fg: list = None,
            align: list = None,
            default_align='vc'
    ):
        super(TableModel, self).__init__(parent=parent)
        self._data = data[:]
        self._header_data = header_data[:]
        self._bg = bg
        self._fg = fg
        self._align = align
        self._default_align = TableModel.align[default_align]

    def reset_data(self, new_data: list, bg: list = None, fg: list = None, align: list = None):
        self.beginResetModel()
        self._data = new_data[:]
        if bg:
            self._bg = bg
        if fg:
            self._fg = fg
        if align:
            self._align = align
        self.endResetModel()
        self.sort(0, Qt.AscendingOrder)

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._data)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self._header_data)

    @staticmethod
    def _get_color(color):
        if isinstance(color, str):
            return QColor(color)
        elif isinstance(color, tuple):
            return QColor(*color)
        else:
            raise TypeError(type(color))

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                item = self._data[index.row()]
                if hasattr(item, '__len__'):
                    return item[index.column()]
                return item
            elif self._bg and role == Qt.BackgroundColorRole and self._bg[index.row()]:
                c = self._bg[index.row()]
                if isinstance(c, list):
                    return QVariant(self._get_color(c[index.column()]))
                else:
                    return QVariant(self._get_color(c))
            elif self._fg and role == Qt.ForegroundRole and self._fg[index.row()]:
                c = self._fg[index.row()]
                if isinstance(c, list):
                    return QVariant(self._get_color(c[index.column()]))
                else:
                    return QVariant(self._get_color(c))
            elif role == Qt.TextAlignmentRole:
                if self._align:
                    return self._default_align | TableModel.align[self._align[index.column()]]
                else:
                    return self._default_align
        return QVariant()

    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header_data[col]
        return QVariant()


class TableEditableModel(TableModel):
    class StringDelegate(QStyledItemDelegate):

        def __init__(self, validation_regex: str = None, parent=None):
            QStyledItemDelegate.__init__(self, parent)
            self._regex = validation_regex

        def displayText(self, value, locale):
            return str(value)

        def createEditor(self, parent: QWidget, style: QStyleOptionViewItem, index: QModelIndex):
            editor = QLineEdit(parent)
            if self._regex:
                validator = QRegExpValidator(editor)
                validator.setRegExp(QRegExp(self._regex))
                editor.setValidator(validator)
            editor.setText(str(index.data(Qt.DisplayRole)))
            return editor

        def setEditorData(self, editor: QLineEdit, index: QModelIndex):
            editor.setText(index.data(Qt.DisplayRole))

        def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
            model.setData(index, editor.text())

    class FloatDelegate(QStyledItemDelegate):

        def __init__(self, min_value: float, max_value: float, parent=None):
            QStyledItemDelegate.__init__(self, parent)
            self._min = min_value
            self._max = max_value

        def displayText(self, value, locale):
            return '{:07.3f}'.format(float(value))

        def createEditor(self, parent: QWidget, style: QStyleOptionViewItem, index: QModelIndex):
            editor = QDoubleSpinBox(parent)
            editor.setMinimum(self._min)
            editor.setMaximum(self._max)
            editor.setDecimals(3)
            editor.setValue(float(index.data(Qt.DisplayRole)))
            return editor

        def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
            editor.setValue(index.data(Qt.DisplayRole))

        def setModelData(self, editor: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex):
            editor.interpretText()
            model.setData(index, editor.value())

    def __init__(
            self,
            data: list,
            header_data: list,
            delegates: list,
            parent=None,
            bg: list = None,
            fg: list = None,
            align: list = None
    ):

        TableModel.__init__(self, data, header_data, parent, bg, fg, align)
        self.delegates = delegates

    def flags(self, index: QModelIndex):
        if index.isValid():
            if self.delegates[index.column()] is not None:
                return super(TableEditableModel, self).flags(index) | Qt.ItemIsEditable
        return super(TableEditableModel, self).flags(index)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            return super(TableEditableModel, self).data(index, Qt.DisplayRole)
        return super(TableEditableModel, self).data(index, role)

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if index.isValid():
            self._data[index.row()][index.column()] = value
            # noinspection PyUnresolvedReferences
            self.dataChanged.emit(index, index)
            return True
        return super(TableEditableModel, self).setData(index, value, role)


def box_info(parent, title: str, text: str):
    # noinspection PyArgumentList
    QMessageBox.information(parent, title, text)


def box_question(parent, text: str, title: str = 'Please confirm'):
    # noinspection PyArgumentList
    reply = QMessageBox.question(parent, title, text)

    return reply == QMessageBox.Yes


class BrowseDialog(QFileDialog):
    def __init__(self, parent, title: str):
        QFileDialog.__init__(self, parent)
        self.setWindowIcon(QIcon(':/ico/app.ico'))
        self.setViewMode(QFileDialog.Detail)
        self.setWindowTitle(title)

    def parse_single_result(self) -> Path or None:
        if self.exec():
            result = self.selectedFiles()[0]
            return Path(result)
        else:
            return None

    def parse_multiple_results(self) -> typing.List[Path] or None:
        if self.exec():
            results = [Path(x) for x in self.selectedFiles()[0]]
            return results
        else:
            return None

    @staticmethod
    def make(parent, title: str, filter_: typing.List[str] = None, init_dir: str = '.'):
        if filter_ is None:
            filter_ = ['*.*']
        dialog = BrowseDialog(parent, title)
        dialog.setOption(QFileDialog.DontResolveSymlinks)
        dialog.setOption(QFileDialog.DontUseCustomDirectoryIcons)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilters(filter_)
        dialog.setDirectory(init_dir)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        if filter_:
            dialog.setDefaultSuffix(filter_[0])
        # dialog.setOption(QFileDialog.ReadOnly)
        return dialog

    @staticmethod
    def get_file(parent, title: str, filter_: typing.List[str] = None, init_dir: str = '.') -> Path or None:
        dialog = BrowseDialog.make(parent, title, filter_, init_dir)
        dialog.setFileMode(QFileDialog.AnyFile)
        return dialog.parse_single_result()

    @staticmethod
    def get_existing_file(parent, title: str, filter_: typing.List[str] = None, init_dir: str = '.') -> Path or None:
        dialog = BrowseDialog.make(parent, title, filter_, init_dir)
        dialog.setFileMode(QFileDialog.ExistingFile)
        return dialog.parse_single_result()

    @staticmethod
    def get_existing_files(parent, title: str, filter_: typing.List[str] = None,
                           init_dir: str = '.') -> typing.List[Path] or None:
        dialog = BrowseDialog.make(parent, title, filter_, init_dir)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        return dialog.parse_multiple_results()

    @staticmethod
    def save_file(parent, title: str, filter_: typing.List[str] = None, init_dir: str = '.') -> Path or None:
        dialog = BrowseDialog.make(parent, title, filter_, init_dir)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        return dialog.parse_single_result()

    @staticmethod
    def get_directory(parent, title: str, init_dir: str = '.') -> Path or None:
        dialog = BrowseDialog.make(parent, title, init_dir=init_dir)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        return dialog.parse_single_result()


class TabChild(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent, flags=Qt.Widget)
        self.setContentsMargins(20, 20, 20, 20)
        self._main_ui = parent

    @abstractmethod
    def tab_clicked(self):
        pass

    @property
    @abc.abstractmethod
    def tab_title(self) -> str:
        """"""


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self._tabs = []
        # noinspection PyUnresolvedReferences
        self.currentChanged.connect(self._current_index_changed)

    @property
    def tabs(self) -> typing.Generator['TabChild', None, None]:
        for tab in self._tabs:
            yield tab

    def get_tab_from_title(self, tab_title: str) -> 'TabChild':
        for tab in self.tabs:
            if tab.tab_title == tab_title:
                return tab
        raise KeyError('tab "{}" not found'.format(tab_title))

    # noinspection PyMethodOverriding
    def addTab(self, tab: 'TabChild'):
        self._tabs.append(tab)
        super(TabWidget, self).addTab(tab, tab.tab_title)

    def _current_index_changed(self, tab_index):
        self._tabs[tab_index].tab_clicked()

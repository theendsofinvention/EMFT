# coding=utf-8
# Whole imports
import builtins
import ctypes
import sys
import traceback
from json import dumps as jdumps, loads as jloads
from operator import itemgetter
from os import stat, _exit, startfile
from os.path import exists, abspath, join, normpath, dirname
from pickle import dumps as pdumps, loads as ploads
from re import compile as re_compile
from shutil import move
from time import sleep
from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_CURRENT_USER

from PyQt5.QtCore import QThread, pyqtSlot as Slot, pyqtSignal as Signal, QObject, Qt, QRegExp, QAbstractTableModel, \
    QModelIndex, QVariant, QSortFilterProxyModel, QAbstractListModel, \
    QAbstractItemModel
from PyQt5.QtGui import QImage, QIcon, QPixmap, QBrush, QRegExpValidator, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton, QWidget, QStyledItemDelegate, \
    QLineEdit, QStyleOption, QComboBox, QStyleOptionViewItem, QDoubleSpinBox
from abstract_gui.abstract_gui import AbstractGui, StandardAbstractTableWithHeaders
from base_utils.base_utils import BaseUtils
from custom_config.custom_config import Config
from custom_logging.custom_logging import make_logger, Logged
from custom_version.custom_version import Version
from esme import flights as flights_module
from esme import skins
from esme.__version__ import __version__, __app_name__, __author__, __guid__
from esme.miz import Miz, Country, Coalition, Group, AbstractUnit, MizErrors, FlyingUnit, Mission as MizMission
from esme.roster import Roster, RosterError, Wing, Squad, Pilot, Skin, AC
from secure.secure import Secure
from tendo import singleton
from thread_pool.thread_pool import ThreadPool
from ui import main as qt_main_ui, widget_units as qt_widget_units, widget_config as qt_widget_config, \
    widget_radios as qt_widget_radios, widget_roster as qt_widget_roster, \
    widget_flights as qt_widget_flights

VALID_CLIENT_AC = {'A-10A', 'A-10C', 'F-15C', 'FW-190D9', 'ka-50', 'L-39ZA', 'mi-8mt', 'mig-29a', 'mig-29s', 'P-51D',
                   'su-25', 'su-25t', 'su-27', 'su-33', 'TF-51D', }
VALID_CLIENT_AC = sorted(VALID_CLIENT_AC)
VALID_CLIENT_AC_LOWER = [x.lower() for x in VALID_CLIENT_AC]

FROZEN = hasattr(sys, "frozen")

LOG_FILE = 'esme.debug'
LOGGER = make_logger(log_file_path=LOG_FILE)

CONFIG_FILE = 'esme.config'
if exists(CONFIG_FILE) and stat(CONFIG_FILE).st_size == 0:
    remove(CONFIG_FILE)

LOGGER.debug('Reading config')
Config.defaults = {
    'roster_path': 'esme.roster',
}
Config.encode = FROZEN
Config.path = CONFIG_FILE
Config().read()

QT_APP = QApplication(sys.argv)
APP_ICON = QIcon(':/ico/resources/esme.ico')

CURRENT_VERSION = Version(__version__)

UI = None

SECURE = Secure()
SECURE.decode('TFRxuIYih7pF6jGoJum8jQUuNGuJuSrm')

DATABASE = {
    'parking': {},
    'countries': {},
}

ROSTER_FILE = 'esme.roster'

Roster.file_path = ROSTER_FILE
Roster.encode = FROZEN
ROSTER = Roster()

FLIGHTS = flights_module.Flights()


class ESMEE:
    """Container for ESME specific Exceptions"""

    class ESMEError(Exception):
        """Base ESME Exception"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


# noinspection PyMissingOrEmptyDocstring,PyShadowingBuiltins
def exit(code=0):
    if code is False:
        code = 0
    LOGGER.debug('exiting {} with error code {}'.format(__app_name__, code))
    _exit(code)


class Params:
    """
    Contains the parameters that are parsed at the start of ESME
    """
    __state = {
        'admin': False,
        'config': False,
        'subscription': False,
    }

    def __init__(self):
        super().__init__()
        self.__dict__ = self.__state

    def __str__(self):
        return '\n'.join(['\t\tParam: {} is {}'.format(k, self.__state[k]) for k in self.__state.keys()])

    def __repr__(self):
        return self.__str__()


class BuiltinsWrapper(Logged):
    """
    Wraps around builtins functions to log their execution
    Re-declaration of builtins happens at instantiation
    """
    old_move = move
    old_open = builtins.open
    old_remove = remove
    old_removedirs = removedirs
    old_print = print
    old_print_exception = traceback.print_exception

    # noinspection PyShadowingBuiltins, PyRedeclaration
    def __init__(self):
        super().__init__()
        global remove, move, removedirs, print
        # noinspection PyGlobalUndefined
        global exit
        move = self.new_move
        remove = self.new_remove
        removedirs = self.new_remove_dirs
        print = self.new_print
        if FROZEN:
            sys.excepthook = self.excepthook

    @staticmethod
    def excepthook(_type, value, tback):
        """
        Monkeypatching to intercept exceptions and report them
        :param _type: exception type
        :param value: exception msg
        :param tback: traceback
        """
        LOGGER.error('excepthook intercept error:\n{}: {}\n{}'.format(_type, value,
                                                                      ''.join([x for x in traceback.format_tb(tback)])))
        Utils.send_crash_report(crash_program=True)

    # noinspection PyMissingOrEmptyDocstring
    def new_print(self, *args, **kwargs):
        if FROZEN:
            return
        self.old_print(*args, **kwargs)

    # noinspection PyMissingOrEmptyDocstring
    def new_move(self, *args, **kwargs):
        try:
            self.logger.debug("moving: {} -> {}".format(args[0], args[1]))
            BuiltinsWrapper.old_move(*args, **kwargs)
        except:
            self.logger.exception("error while trying to move file")
            raise
        return True

    # noinspection PyMissingOrEmptyDocstring
    def new_remove(self, *args, **kwargs):
        try:
            self.logger.debug("removing: {}".format(args[0]))
            BuiltinsWrapper.old_remove(*args, **kwargs)
        except:
            self.logger.exception("error while trying to remove file")
            raise
        return True

    # noinspection PyMissingOrEmptyDocstring
    def new_remove_dirs(self, *args, **kwargs):
        try:
            # removed output, was way too much FFS; leaving error output only, should about do it
            # self.logger.debug("removing directories: {}".format(args[0]))
            BuiltinsWrapper.old_removedirs(*args, **kwargs)
        except OSError:
            pass
        except:
            self.logger.exception("error while trying to remove directories")
            raise
        return True


BuiltinsWrapper()


class Utils(BaseUtils):
    """Utility class; holds all static methods"""

    def __init__(self):
        super().__init__()

    @staticmethod
    def send_crash_report(crash_program=True):
        """Sends a crash report, including debug log and current config as attachments
        :param crash_program: whether or not EASI should exit after sending the crash report
        """
        with open(LOG_FILE) as _f:
            debug_text = _f.read()
        _from = Utils.raw_uuid() or 'CrashReporter'
        Utils.send_mail(subject='{} crash report'.format(__app_name__), body='', secure=SECURE,
                        text_attachment_as_text=[(debug_text, 'debug'),
                                                 (jdumps(Config().state.data, indent=True, sort_keys=True), 'config')],
                        _from=_from)
        if crash_program:
            exit(1)

    @staticmethod
    def get_dcs_path():
        LOGGER.debug('looking for main DCS installation in the registry')
        a_reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        try:
            with OpenKey(a_reg, r"Software\Eagle Dynamics\DCS World") as aKey:
                return QueryValueEx(aKey, "Path")[0]
        except:
            LOGGER.error('could not find main DCS installation')


class MizData(Logged):
    """Represents a loaded Miz file"""

    mission = None

    loading = False

    miz_path = None

    __is_loaded = False

    def __init__(self):
        super().__init__()

    @property
    def is_loaded(self):
        return self.__is_loaded

    # @staticmethod
    # def threaded_loader(path_to_miz):
    #     MizData.loading = True
    #     with Miz(path_to_miz) as opened_miz:
    #         miz.mission = opened_miz.mission
    #     miz.loading = False

    def load(self):
        self.loading = True
        with Miz(self.miz_path) as opened_miz:
            self.mission = opened_miz.mission
        # print(self.mission)
        self.loading = False
        self.__is_loaded = True
        # print('endloading')
        # print('Miz: {}'.format(miz.is_loaded))

    # def load_from_miz(self, path_to_miz):
    #     """
    #     Delegates loading a miz file to a threaded worker
    #     :param path_to_miz: path to the miz file to load
    #     """
    #     path_to_miz = abspath(path_to_miz)
    #     MizData.miz_path = path_to_miz
    #     Gui.do('mizfile_loading')
    #     main_process.queue_task(self.threaded_loader, args=[path_to_miz], _task_callback=miz.on_miz_loaded)
    #     main_process.queue_task(FLIGHTS.populate_from_miz, args=[miz])

    @staticmethod
    def on_miz_loaded(*args):
        Gui.do('mizfile_loaded')
        MIZ.__is_loaded = True

    @staticmethod
    def wait_for_miz():
        """
        Loops until a miz file has been loaded
        """
        while MIZ.loading:
            sleep(0.1)


MIZ = MizData()


class MainProcess(Logged):
    threadpool = None

    def __init__(self):
        super().__init__()
        if self.threadpool is None:
            self.threadpool = ThreadPool(num_threads=1, crash_call_back=Utils.send_crash_report)

    def queue(self, task, args=None, kwargs=None, _task_callback=None):
        self.logger.debug(
            'queueing task: {} with params {}\n{}\ncallback is:{}'.format(task, args, kwargs, _task_callback))
        self.threadpool.queue_task(task, args=args, kwargs=kwargs, _task_callback=_task_callback)

    def gather_skins(self):
        skin_folders = Config().skin_folders
        self.threadpool.queue_task(skins.gather_in_folders, kwargs={'list_of_folders': skin_folders})

    def load_miz(self, miz_file_path):
        MIZ.miz_path = abspath(miz_file_path)
        Gui.do('mizfile_loading')
        self.threadpool.queue_task(MIZ.load, _task_callback=MIZ.on_miz_loaded)
        self.threadpool.queue_task(FLIGHTS.populate_from_miz, kwargs={'miz': MIZ})


MAIN_PROC = MainProcess()


class Parking(Logged):
    def __init__(self, x, y):
        super().__init__()
        self.__pos_x = x
        self.__pos_y = y
        self.__suitable_for = set()

    @property
    def pos_x(self):
        return self.__pos_x

    @property
    def pos_y(self):
        return self.__pos_y

    def is_suitable_for(self, aircraft):
        return aircraft in self.__suitable_for

    def set_suitable_for(self, aircraft):
        self.__suitable_for.add(aircraft)


class Airport(Logged):
    names = {
        12: 'Anapa Vityazevo',
        13: 'Krasnodar-Central',
        14: 'Novorossiysk',
        15: 'Krymsk',
        16: 'Maikop',
        17: 'Gelendzhik',
        18: 'Sochi-Adler',
        19: 'Krasnodar-Pashkovsky',
        20: 'Sukhumi',
        21: 'Gudauta',
        22: 'Batumi',
        23: 'Senaki-Kolkhi',
        24: 'Kobuleti',
        25: 'Kutaisi',
        26: 'Mineralnye Vody',
        27: 'Nalchik',
        28: 'Mozdok',
        29: 'Tbilissi-Lochini',
        30: 'Soganlug',
        31: 'Vaziani',
        32: 'Beslan',
    }

    def __init__(self):
        super().__init__()
        self.parking = set()


class AbstractTreeItem(QStandardItem):
    def __init__(self):
        super().__init__()
        self.__children_items = []
        self.__ids = {}

    def add_child_item(self, item, id):
        self.__children_items.append(item)
        self.__ids[id] = item

    def remove_child_item(self, id):
        item = self.__ids[id]
        self.__children_items.remove(item)
        del self.__ids[id]

    def get_item(self, id):
        return self.__ids[id]

    @property
    def children(self):
        for child_item in self.__children_items:
            yield child_item


class AbstractWidget(QWidget, Logged):
    def __init__(self, parent, linked_btn):
        super().__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.connect_elements()
        self.linked_btn = linked_btn

    def update_model(self):
        raise NotImplementedError()

    def connect_elements(self):
        raise NotImplementedError()

    def show(self):
        self.parent.hide_all_widgets()
        self.linked_btn.setChecked(True)
        self.update_model()
        super().show()


class StandardAbstractListModel(QAbstractListModel):
    def __init__(self, data_array, parent=None):
        """ datain: a list where each item is a row
        """
        super().__init__(parent)
        self.data_array = data_array

    def reset_data_to(self, data_array):
        # noinspection PyUnresolvedReferences
        self.layoutAboutToBeChanged.emit()
        self.data_array = data_array
        # noinspection PyUnresolvedReferences
        self.layoutChanged.emit()
        # noinspection PyUnresolvedReferences
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(), 0))

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.data_array)

    def data(self, index, role=None):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.data_array[index.row()])
        else:
            return QVariant()

    def flags(self, index):
        flags = super().flags(index)

        if index.isValid():
            flags |= Qt.ItemIsEditable
            flags |= Qt.ItemIsDragEnabled
        else:
            flags = Qt.ItemIsDropEnabled

        return flags

    def insertRows(self, new_data, row=0, count=1, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self.data_array[row:row] = [new_data] * count
        self.endInsertRows()
        return True

    def insertRow(self, new_data, row=0, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), row, row)
        self.data_array[row:row] = [new_data]
        self.endInsertRows()
        return True

    def removeRows(self, row, count=1, parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self.data_array[row:row + count]
        self.endRemoveRows()
        return True

    def removeRow(self, row, parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.data_array[row]
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        self.data_array[index.row()] = value
        # noinspection PyUnresolvedReferences
        self.dataChanged.emit(index, index)
        return True


class ConfigWidget(AbstractWidget, qt_widget_config.Ui_Form):
    class SkinListModel(StandardAbstractListModel):
        def __init__(self, datain, parent):
            super().__init__(datain, parent)

    def __init__(self, parent, linked_btn):
        super().__init__(parent, linked_btn)
        self.model = ConfigWidget.SkinListModel([], self.list_skin_folders_view)
        self.list_skin_folders_view.setModel(self.model)

    def update_model(self):
        config = Config()
        self.line_dcs_install_path.setText(config.dcs_path)
        if config.skin_folders is None:
            if config.dcs_path and exists(config.dcs_path):
                config.skin_folders = [normpath(join(config.dcs_path, 'Bazar/Liveries'))]
            else:
                config.skin_folders = []
        self.model.reset_data_to(config.skin_folders)

    @property
    def selected_index(self):
        try:
            return self.list_skin_folders_view.selectedIndexes()[0]
        except IndexError:
            return None

    def open_selected_skin_folder(self):
        index = self.selected_index
        if index:
            startfile(self.model.data_array[index.row()])

    def connect_elements(self):
        self.btn_dcs_set.clicked.connect(self.set_dcs_install_path)
        self.btn_dcs_open.clicked.connect(lambda: startfile(self.line_dcs_install_path.text()))
        self.btn_skin_open.clicked.connect(self.open_selected_skin_folder)
        self.btn_skin_add.clicked.connect(self.add_skin_folder)
        self.btn_skin_remove.clicked.connect(self.remove_skin_folder)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.cancel)

    def add_skin_folder(self):
        new_folder = Utils.user_select('Select the folder to add', 'existing_folder')
        if new_folder is None:
            self.logger.debug('user cancelled')
            return
        new_folder = normpath(new_folder)
        if new_folder in self.model.data_array:
            self.parent._msgbox_say('This folder is already a known skin folder =)')
            return
        self.model.insertRow(new_folder)

    def remove_skin_folder(self):
        index = self.selected_index
        if index:
            print(index.row())
            self.model.removeRow(index.row())

    def set_dcs_install_path(self):
        folder = Utils.user_select('Point to your DCS installation', 'existing_folder')
        folder = abspath(folder)
        if not folder:
            self.logger.debug('user cancelled')
            return
        if not exists(join(folder, 'run.exe')):
            self.parent._msgbox_say('This does not seem to be a DCS installation')
            return
        self.line_dcs_install_path.setText(folder)

    def save(self):
        Config().dcs_path = self.line_dcs_install_path.text()
        Config().skin_folders = self.model.data_array

    def cancel(self):
        self.update_model()


class UnitsWidget(AbstractWidget, qt_widget_units.Ui_Form):
    class SortingProxy(QSortFilterProxyModel):

        def __init__(self, parent=None):
            super().__init__(parent)
            self.filterString = ''
            self.filterFunctions = {}
            self.coa = 'any'
            self.category = 'any'
            self.str = ''
            self.client = False

        def col_index_of_header(self, header_text):
            for i in range(0, self.sourceModel().columnCount()):
                if self.headerData(i, Qt.Horizontal) == header_text:
                    return i
            return None

        def value_of_col_in_row(self, header_text, row_num):
            col_num = self.col_index_of_header(header_text)
            if col_num:
                index = self.index(row_num, col_num)
                return self.data(index)
            else:
                return None

        def setFilterString(self, text):
            self.str = text
            # self.setFilterRegExp(text)

        def filterAcceptsRow(self, row_num, index):
            basemodel = self.sourceModel()
            assert isinstance(basemodel, UnitsWidget.UnitModel)
            assert isinstance(index, QModelIndex)
            if not self.str == '':
                found = False
                for data in basemodel.data_array[row_num]:
                    if self.str.lower() in str(data).lower():
                        found = True
                if not found:
                    return False
            if not self.category == 'any':
                if not self.category == basemodel.data(basemodel.index(row_num, basemodel.headers.index('Category'))):
                    return False
            if not self.coa == 'any':
                if not self.coa == basemodel.data(basemodel.index(row_num, basemodel.headers.index('Coalition'))):
                    return False
            if self.client and not basemodel.data(
                    basemodel.index(row_num, basemodel.headers.index('Skill'))) == 'Client':
                return False
            return True

    class UnitModel(StandardAbstractTableWithHeaders):

        def __init__(self, data_in, headers, parent):
            super().__init__(data_in, headers, parent)

        def flags(self, index):
            if self.headers[index.column()] in ['Group name', 'Unit name', 'Skill']:
                return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    class DelegateUnitSkill(QStyledItemDelegate):

        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent

        def createEditor(self, parent, option, index):
            if not index.isValid():
                return False
            model = self.parent.model()
            assert isinstance(model, UnitsWidget.SortingProxy)
            self.currentIndex = index
            self.editor = QComboBox(parent)
            if model.value_of_col_in_row('Unit type', index.row()).lower() in VALID_CLIENT_AC_LOWER:
                self.editor.addItems(['Client', 'Player', 'Average', 'Good', 'High', 'Excellent', 'Random'])
            else:
                self.editor.addItems(['Average', 'Good', 'High', 'Excellent', 'Random'])
            self.editor.setCurrentText(index.data(Qt.DisplayRole))
            return self.editor

        def setEditorData(self, editor, index):
            value = index.data(Qt.DisplayRole)
            assert isinstance(editor, QComboBox)
            editor.setCurrentText(value)

        def setModelData(self, editor, model, index):
            if not index.isValid():
                return
            assert isinstance(editor, QComboBox)
            value = editor.currentText()
            model.setData(index, value)
            # model.invalidateFilter()

    class DelegateUnitOrGroupName(QStyledItemDelegate):
        re_numbered_name = re_compile(r'(?P<base_name>.*) #(?P<counter>[0-9]{3})')

        def __init__(self, parent):
            super().__init__(parent)

        def createEditor(self, parent, option, index):
            if not index.isValid():
                return False
            self.currentIndex = index
            self.editor = QLineEdit(parent)
            self.editor.setText(index.data(Qt.DisplayRole))
            #  TODO set validator
            return self.editor

        def setEditorData(self, editor, index):
            value = index.data(Qt.DisplayRole)
            editor.setText(value)

        def validate_new_name(self, model, col, new_name, existing=None):
            assert isinstance(model, UnitsWidget.SortingProxy)
            if existing is None:
                existing = [model.sourceModel().data(model.index(r, col)) for r in range(0, model.rowCount())]
            new_unit_name_lower = new_name.lower()
            if new_unit_name_lower in existing:
                m = self.re_numbered_name.match(new_name)
                if m:
                    return self.validate_new_name(model, col, '{} #{}'.format(m.group('base_name'),
                                                                              str(int(m.group('counter')) + 1).zfill(
                                                                                  3)), existing)
                else:
                    return self.validate_new_name(model, col, '{} #001'.format(new_name), existing)
            else:
                return new_name

        def setModelData(self, editor, model, index):
            if not index.isValid():
                return
            value = editor.text()
            assert isinstance(model, UnitsWidget.SortingProxy)
            old_value = model.data(index)
            if value == old_value:
                return
            header = model.headerData(index.column(), Qt.Horizontal)
            print('header: {}'.format(header))
            if header in ['Unit name', 'Group name']:
                print('header is group or unit name')
                value = self.validate_new_name(model, index.column(), value)
                if header in ['Group name']:
                    print('header is group name')
                    for r in range(0, model.rowCount()):
                        other_index = model.index(r, index.column())
                        if model.data(other_index) == old_value:
                            model.setData(other_index, value)
            model.setData(index, value)

    def __init__(self, parent, linked_btn):
        super().__init__(parent, linked_btn)
        self.proxy = UnitsWidget.SortingProxy(self)
        self.model = None

    def show(self):
        self.update_model()
        super().show()

    def update_model(self):
        if not MIZ.is_loaded:
            return
        if MIZ.mission:
            unit_list = [
                [unit.group_id, unit.group_name, unit.unit_id, unit.unit_name, unit.group_category, unit.unit_type,
                 unit.skill, unit.coa_color] for unit in MIZ.mission.units]
            headers = ['Group Id', 'Group name', 'UnitId', 'Unit name', 'Category', 'Unit type', 'Skill', 'Coalition']
            self.model = UnitsWidget.UnitModel(data_in=unit_list, headers=headers, parent=self.table_units)
            self.proxy.setSourceModel(self.model)
            self.table_units.setItemDelegateForColumn(self.model.headers.index('Group name'),
                                                      UnitsWidget.DelegateUnitOrGroupName(self.table_units))
            self.table_units.setItemDelegateForColumn(self.model.headers.index('Unit name'),
                                                      UnitsWidget.DelegateUnitOrGroupName(self.table_units))
            self.table_units.setItemDelegateForColumn(self.model.headers.index('Skill'),
                                                      UnitsWidget.DelegateUnitSkill(self.table_units))
            self.table_units.setModel(self.proxy)
            self.table_units.resizeColumnsToContents()
            self.table_units.setColumnWidth(6, 100)

    def connect_elements(self):
        self.btn_selected.clicked.connect(self.selected_rows)
        self.check_clients_only.clicked.connect(self.filter_clients)
        self.line_generic_search.textChanged.connect(self.filter_generic)
        self.combo_unit_coalition.currentIndexChanged.connect(self.filter_coalition)
        self.combo_unit_category.currentIndexChanged.connect(self.filter_unit_category)

    @property
    def selected_units_ids(self):
        for index in self.table_units.selectedIndexes():
            model = self.table_units.model()
            assert isinstance(model, UnitsWidget.SortingProxy)
            unit_id_col_num = model.col_index_of_header('UnitId')
            unit_id_index = model.index(index.row(), unit_id_col_num)
            yield model.data(unit_id_index)

    def selected_rows(self):
        for index in self.table_units.selectedIndexes():
            print(index.row())

    def filter_generic(self):
        self.proxy.setFilterString(self.line_generic_search.text())
        self.proxy.invalidateFilter()

    def filter_clients(self):
        self.proxy.client = self.check_clients_only.isChecked()
        self.proxy.invalidateFilter()

    def filter_unit_category(self):
        self.proxy.category = self.combo_unit_category.currentText()
        self.proxy.invalidateFilter()

    def filter_coalition(self):
        self.proxy.coa = self.combo_unit_coalition.currentText()
        self.proxy.invalidateFilter()


class RadiosWidget(AbstractWidget, qt_widget_radios.Ui_Form):
    class UnitListSortingProxy(QSortFilterProxyModel):

        def __init__(self, parent=None):
            super().__init__(parent)

        def filterAcceptsRow(self, row_num, index):
            basemodel = self.sourceModel()
            assert isinstance(basemodel, RadiosWidget.UnitTableModel)
            assert isinstance(index, QModelIndex)
            return True

    class UnitTableModel(QAbstractTableModel):

        def __init__(self, data_in, parent):
            super().__init__(parent)
            self.parent = parent
            self.data_array = data_in

        def rowCount(self, parent=None, *args, **kwargs):
            return len(self.data_array)

        def columnCount(self, parent=None, *args, **kwargs):
            if len(self.data_array) > 0:
                return len(self.data_array[0])
            return 0

        def flags(self, index):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid():
                return QVariant()
            if not role == Qt.DisplayRole:
                return QVariant()
            return QVariant(self.data_array[index.row()][index.column()])

        def setData(self, index, value, role=Qt.DisplayRole):
            if not index.isValid():
                return False
            self.data_array[index.row()][index.column()] = value
            return True

    class RadioTableModel(StandardAbstractTableWithHeaders):

        def __init__(self, data_in, headers, parent):
            super().__init__(data_in, headers, parent)

        def sort(self, col=0, order=None):
            """Sort table by given column number.
            """
            # noinspection PyUnresolvedReferences
            self.layoutAboutToBeChanged.emit()
            self.data_array = sorted(self.data_array, key=itemgetter(col))
            if order == Qt.DescendingOrder:
                self.data_array.reverse()
            # noinspection PyUnresolvedReferences
            self.layoutChanged.emit()

        def flags(self, index):
            if self.headers[index.column()] in ['Frequency']:
                return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    class FrequencyEditor(QStyledItemDelegate):

        def __init__(self, _min, _max, parent, step_double):
            super().__init__(parent)
            self.parent = parent
            self.min = float(_min)
            self.max = float(_max)
            self.editor = None
            self.step_double = step_double

        def createEditor(self, parent, option, index):
            if not index.isValid():
                return False
            model = self.parent.model()
            assert isinstance(model, RadiosWidget.RadioTableModel)
            self.currentIndex = index
            self.editor = QDoubleSpinBox(parent)
            if self.max < 5:
                self.editor.setDecimals(3)
                # self.editor.setSingleStep(0.001)
            else:
                self.editor.setDecimals(2)
            self.editor.setSingleStep(self.step_double.value())
            self.editor.setMinimum(self.min)
            self.editor.setMaximum(self.max)
            self.editor.setValue(float(index.data(Qt.DisplayRole)))
            #  TODO set validator
            return self.editor

        def setEditorData(self, editor, index):
            editor.setValue(float(index.data(Qt.DisplayRole)))

        def setModelData(self, editor, model, index):
            if not index.isValid():
                return
            assert isinstance(editor, QDoubleSpinBox)
            value = editor.value()
            model.setData(index, value)
            # model.invalidateFilter()

    def __init__(self, parent, linked_btn):
        super().__init__(parent)
        self.btns = [self.btn_huey, self.btn_ka, self.btn_mi, self.btn_sabre, self.btn_mirage, self.btn_mig21,
                     self.btn_p51, self.btn_tf51, self.btn_all]
        self.base_model = None
        self.proxy = RadiosWidget.UnitListSortingProxy(self)
        self.radio1_delegate = None
        self.radio2_delegate = None

    def update_model(self):
        if not MIZ.is_loaded:
            return
        unit_list = [[unit.unit_name, unit.unit_type] for unit in MIZ.mission.units if unit.has_radio_presets]
        self.base_model = RadiosWidget.UnitTableModel(unit_list, self.table_aircrafts)
        self.proxy.setSourceModel(self.base_model)
        self.table_aircrafts.setModel(self.proxy)

    def uncheck_all_btns(self):
        for btn in self.btns:
            btn.setChecked(False)

    def connect_elements(self):
        self.btn_ka.clicked.connect(self.show_ka)
        self.btn_tf51.clicked.connect(self.show_tf51)
        self.btn_huey.clicked.connect(self.show_huey)
        self.btn_p51.clicked.connect(self.show_p51)
        self.btn_mig21.clicked.connect(self.show_mig21)
        self.btn_mi.clicked.connect(self.show_mi)
        self.btn_mirage.clicked.connect(self.show_mirage)
        self.btn_sabre.clicked.connect(self.show_sabre)
        self.btn_all.clicked.connect(self.show_all)
        self.table_aircrafts.clicked.connect(self.aircraft_list_clicked)
        # self.double_r1_step.valueChanged.connect(self.radio1_step_changed)
        # self.double_r2_step.valueChanged.connect(self.radio2_step_changed)

    def aircraft_list_clicked(self):
        if not MIZ.is_loaded:
            return
        index = self.table_aircrafts.selectedIndexes()[0]
        unit_name = self.proxy.data(self.proxy.index(index.row(), 0))
        assert isinstance(MIZ.mission, MizMission)
        unit = MIZ.mission.get_unit_by_name(unit_name)
        assert isinstance(unit, FlyingUnit)
        headers = ['Channel', 'Frequency']
        radio1 = unit.get_radio_by_number(1)
        if radio1.max < 5:
            self.double_r1_step.setValue(0.01)
        else:
            self.double_r1_step.setValue(0.1)
        radio1_model = RadiosWidget.RadioTableModel([[channel, freq] for channel, freq in radio1.channels], headers,
                                                    self.table_radio1)
        radio1_model.sort()
        self.label_radio1.setText(radio1.radio_name)
        self.table_radio1.setModel(radio1_model)
        self.radio1_delegate = RadiosWidget.FrequencyEditor(radio1.min, radio1.max, self.table_radio1,
                                                            self.double_r1_step)
        self.table_radio1.setItemDelegateForColumn(1, self.radio1_delegate)
        try:
            radio2 = unit.get_radio_by_number(2)
        except TypeError:
            radio2_model = RadiosWidget.RadioTableModel([], headers, self.table_radio2)
            self.table_radio2.setModel(radio2_model)
            self.label_radio2.setText('')
            self.set_radio2_enabled(False)
        else:
            self.set_radio2_enabled(True)
            radio2_model = RadiosWidget.RadioTableModel([[channel, freq] for channel, freq in radio2.channels], headers,
                                                        self.table_radio2)
            radio2_model.sort()
            self.label_radio2.setText(radio2.radio_name)
            self.table_radio2.setModel(radio2_model)
            if radio2.max < 5:
                self.double_r2_step.setValue(0.01)
            else:
                self.double_r2_step.setValue(0.1)
            self.radio2_delegate = RadiosWidget.FrequencyEditor(radio2.min, radio2.max, self.table_radio2,
                                                                self.double_r2_step)
            self.table_radio2.setItemDelegateForColumn(1, self.radio2_delegate)

    def set_radio2_enabled(self, enabled=True):
        for e in [self.label_radio2, self.table_radio2, self.btn_r2_apply, self.btn_r2_apply_to_all, self.btn_r2_copy,
                  self.btn_r2_discard, self.btn_r2_load, self.btn_r2_paste, self.btn_r2_save,
                  self.double_r2_step, self.label_r2_step]:
            e.setEnabled(enabled)

    def show_all(self):
        self.uncheck_all_btns()
        self.btn_all.setChecked(True)

    def show_sabre(self):
        self.uncheck_all_btns()
        self.btn_sabre.setChecked(True)

    def show_ka(self):
        self.uncheck_all_btns()
        self.btn_ka.setChecked(True)

    def show_tf51(self):
        self.uncheck_all_btns()
        self.btn_tf51.setChecked(True)

    def show_huey(self):
        self.uncheck_all_btns()
        self.btn_huey.setChecked(True)

    def show_p51(self):
        self.uncheck_all_btns()
        self.btn_p51.setChecked(True)

    def show_mig21(self):
        self.uncheck_all_btns()
        self.btn_mig21.setChecked(True)

    def show_mi(self):
        self.uncheck_all_btns()
        self.btn_mi.setChecked(True)

    def show_mirage(self):
        self.uncheck_all_btns()
        self.btn_mirage.setChecked(True)


class RosterWidget(AbstractWidget, qt_widget_roster.Ui_Form):
    class DelegateAC(QStyledItemDelegate):

        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent

        def createEditor(self, parent, option, index):
            if not index.isValid():
                return False
            model = self.parent.model()
            assert isinstance(model, RosterWidget.RosterTreeModel)
            self.currentIndex = index
            self.editor = QComboBox(parent)
            self.editor.addItem('None')
            self.editor.addItems(VALID_CLIENT_AC)
            return self.editor

        def setEditorData(self, editor, index):
            value = index.data(Qt.DisplayRole)
            assert isinstance(editor, QComboBox)
            editor.setCurrentText(value)

        def setModelData(self, editor, model, index):
            assert isinstance(editor, QComboBox)
            assert isinstance(index, QModelIndex)
            assert isinstance(model, RosterWidget.RosterTreeModel)
            if not index.isValid():
                print('index invalid')
                return
            value = editor.currentText()
            model.setData(index, value)
            model.setData(index.sibling(index.row(), index.column() + 1), 'None')

    class DelegateSkin(QStyledItemDelegate):

        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.editor = None
            self.currentIndex = None

        def createEditor(self, parent, option, index):
            if not index.isValid():
                return False
            model = self.parent.model()
            assert isinstance(model, RosterWidget.RosterTreeModel)
            assert isinstance(index, QModelIndex)
            self.currentIndex = index
            self.editor = QComboBox(parent)
            self.editor.addItem('None')
            ac_index = index.sibling(index.row(), index.column() - 1)
            ac_item = model.itemFromIndex(ac_index)
            ac_name = ac_item.name
            if ac_name is not None and not ac_name == 'None':
                if ac_name is not None:
                    self.editor.addItems(skins.available_skins_for(ac_name))
            return self.editor

        def setEditorData(self, editor, index):
            value = index.data(Qt.DisplayRole)
            assert isinstance(editor, QComboBox)
            editor.setCurrentText(value)

        def setModelData(self, editor, model, index):
            if not index.isValid():
                return
            assert isinstance(editor, QComboBox)
            value = editor.currentText()
            model.setData(index, value)

    class RosterTreeItem(QStandardItem):

        def __init__(self, obj, parent=None):
            super().__init__()
            self.obj = obj
            self.setText(self.name)
            self.parent = parent
            self.__child_items = []
            self.skin_item = None
            self.ac_item = None

        def add_child_item(self, child_item):
            child_item.ac_item = RosterWidget.ACItem(child_item.obj.default_ac, child_item)
            child_item.skin_item = RosterWidget.SkinItem(child_item.obj.default_skin, child_item)
            self.appendRow([child_item, child_item.ac_item, child_item.skin_item])
            self.__child_items.append(child_item)

        @property
        def child_items(self):
            for child in sorted(self.__child_items, key=lambda child: child.name):
                yield child

        @property
        def name(self):
            return self.obj.name

    class WingItem(RosterTreeItem):

        def __init__(self, obj, parent=None):
            super().__init__(obj, parent)

    class SquadItem(RosterTreeItem):

        def __init__(self, obj, parent):
            super().__init__(obj, parent)

    class PilotItem(RosterTreeItem):

        def __init__(self, obj, parent):
            super().__init__(obj, parent)

    class SkinItem(RosterTreeItem):

        def __init__(self, obj, parent):
            super().__init__(obj, parent)

    class ACItem(RosterTreeItem):

        def __init__(self, obj, parent):
            super().__init__(obj, parent)
            self.obj = obj

    class RosterTreeModel(QStandardItemModel):

        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.headers = ['Name', 'Default A/C', 'Default skin']

        def make_from_roster(self):
            self.clear()
            for wing in ROSTER.wings:
                wing_item = RosterWidget.WingItem(wing)
                self.appendRow([wing_item, None, None])
                for squad in wing.children:
                    squad_item = RosterWidget.SquadItem(squad, wing_item)
                    wing_item.add_child_item(squad_item)
                    for pilot in squad.children:
                        pilot_item = RosterWidget.PilotItem(pilot, squad_item)
                        squad_item.add_child_item(pilot_item)

        def setData(self, index, value, int_role=Qt.DisplayRole):
            super().setData(index, value, int_role)
            item = self.itemFromIndex(index)
            assert isinstance(item, RosterWidget.RosterTreeItem)
            item.obj.name = value
            if isinstance(item, RosterWidget.SkinItem):
                # assert isinstance(item.parent.obj, Pilot)
                item.parent.obj.default_skin = Skin(value)
            if isinstance(item, RosterWidget.ACItem):
                # assert isinstance(item.parent.obj, Pilot)
                item.parent.obj.default_ac = AC(value)
            return True

        def headerData(self, col, orientation, role=Qt.DisplayRole):
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return QVariant(self.headers[col])
            return QVariant()

    class FlightItem(QStandardItem):

        def __init__(self, parent_item, flight):
            super().__init__()
            self.setText(flight.name)
            self.children = []
            self.parent_item = parent_item
            self.flight = flight

        def add_child_item(self, child_item):
            self.children.append(child_item)

    class FlightsModel(QStandardItemModel):

        def __init__(self, parent):
            super().__init__(parent)
            self.headers = ['Name', 'zzz', 'zzz']
            self.__flights = {}
            self.__items = {}
            self.__unassigned_pilots_item = FlightsWidget.UnassignedPilotsItem()

        def flags(self, index):
            return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled

        def flight_from_item(self, item):
            pass

        def item_from_flight(self, flight):
            pass

        def make(self):
            self.clear()
            self.__unassigned_pilots_item = FlightsWidget.UnassignedPilotsItem()
            # print(self.__unassigned_pilots_item.flags().__int__())
            self.appendRow([self.__unassigned_pilots_item, None, None])
            print(FLIGHTS)
            for flight in FLIGHTS.flights:
                # print(flight)
                flight_item = FlightsWidget.FlightItem(self, flight)
                self.__flights[flight_item.index()] = flight
                self.__items[flight.id] = flight_item
                self.appendRow([flight_item, None, None])

    def __init__(self, parent, linked_btn):
        super().__init__(parent, linked_btn)
        self.roster_model = RosterWidget.RosterTreeModel(self.tree_roster_view)
        self.tree_roster_view.setModel(self.roster_model)
        self.tree_roster_view.setItemDelegateForColumn(1, RosterWidget.DelegateAC(self.tree_roster_view))
        self.tree_roster_view.setItemDelegateForColumn(2, RosterWidget.DelegateSkin(self.tree_roster_view))
        self.load_from_file(alert=False)
        self.model_state = None
        self.combo_ac.addItem('None')
        self.combo_ac.addItems(VALID_CLIENT_AC)
        self.flights_model = RosterWidget.FlightsModel(self.tree_flights_view)
        self.tree_flights_view.setModel(self.flights_model)

    def show(self):
        self.line_roster_file_path.setText(abspath(Config().roster_path))
        super().show()

    def update_model(self):
        # self.model.make_from_roster()
        self.tree_roster_view.expandAll()

    def connect_elements(self):
        self.btn_add_wing.clicked.connect(self.add_wing)
        self.btn_add_squad.clicked.connect(self.add_squad)
        self.btn_add_pilot.clicked.connect(self.add_pilot)
        self.btn_save.clicked.connect(self.save_to_file)
        self.btn_load.clicked.connect(self.load_from_file)
        self.btn_roster_file_path.clicked.connect(self.set_roster_file_path)
        self.btn_jump_to_roster_file.clicked.connect(lambda: startfile(dirname(Roster.file_path)))
        self.combo_ac.currentTextChanged.connect(self.combo_ac_changed)
        self.btn_set_batch.clicked.connect(self.batch_set_skin_and_ac)
        self.btn_remove.clicked.connect(self.remove_selected)

    def combo_ac_changed(self):
        self.combo_skin.clear()
        self.combo_skin.addItem('None')
        if self.combo_ac.currentText() != 'None':
            self.combo_skin.addItems(skins.available_skins_for(self.combo_ac.currentText()))

    def batch_set_skin_and_ac(self):
        item = self.selected_item
        if item is None:
            return
        assert isinstance(item, RosterWidget.RosterTreeItem)
        ac = self.combo_ac.currentText()
        skin = self.combo_skin.currentText()
        self.__batch_set_skin_and_ac(item, ac, skin)
        self.update_model()

    def __batch_set_skin_and_ac(self, item, ac, skin):
        assert isinstance(item, RosterWidget.RosterTreeItem)
        if isinstance(item.skin_item, RosterWidget.RosterTreeItem):
            item.skin_item.obj.name = skin
        if isinstance(item.ac_item, RosterWidget.RosterTreeItem):
            item.ac_item.obj.name = ac
        for child in item.child_items:
            self.__batch_set_skin_and_ac(child, ac, skin)

    def set_roster_file_path(self):
        new_path = Utils.user_select('Choose the roster file (must be a valid roster file if it already exists)',
                                     'save_file', str_filter='*.roster')
        if not new_path.endswith('.roster'):
            new_path = '{}.roster'.format(new_path)
        if new_path:
            new_path = abspath(new_path)
            Config().roster_path = new_path
            self.line_roster_file_path.setText(new_path)

    @property
    def selected_item(self):
        try:
            sel_idx = self.tree_roster_view.selectedIndexes()[0]
        except IndexError:
            return None
        item = self.roster_model.itemFromIndex(sel_idx)
        assert isinstance(item, QStandardItem)
        return item

    @property
    def selected_item_text(self):
        if self.selected_item is None:
            return None
        return self.selected_item.text()

    def add_wing(self):
        Gui.msgbox_input_str('New Wing name: ', self.__add_wing)

    def __add_wing(self, wing_name):
        try:
            new_wing = Wing(wing_name)
            ROSTER.add_wing(new_wing)
        except RosterError.ObjectExistsError:
            Gui.msgbox_say('This Wing already exist =)')
        self.update_model()

    def add_squad(self):
        parent_name = self.selected_item_text
        if parent_name is None or not isinstance(self.selected_item, RosterWidget.WingItem):
            Gui.msgbox_say('Please select a Wing to add this squadron to')
            return
        Gui.msgbox_input_str('New squadron name: ', self.__add_squad, parent_name)

    def __add_squad(self, squad_name, parent_name):
        parent = ROSTER.get_wing_by_name(parent_name)
        try:
            new_squad = Squad(squad_name, parent)
            parent.add_child(new_squad)
        except RosterError.ObjectExistsError:
            Gui.msgbox_say('This squadron already exist =)')
        self.update_model()

    def add_pilot(self):
        parent_name = self.selected_item_text
        if not parent_name or not isinstance(self.selected_item, RosterWidget.SquadItem):
            Gui.msgbox_say('Please select a squadron to attach this pilot to')
            return
        Gui.msgbox_input_str('New pilot name: ', self.__add_pilot, parent_name)

    def __add_pilot(self, pilot_name, parent_name):
        parent = ROSTER.get_squad_by_name(parent_name)
        assert isinstance(parent, Squad)
        try:
            pilot = Pilot(pilot_name, parent, default_ac=AC(parent.default_ac.name),
                          default_skin=Skin(parent.default_skin.name))
            parent.add_child(pilot)
        except RosterError.ObjectExistsError:
            Gui.msgbox_say('This pilot already exist =)')
        self.update_model()

    def remove_selected(self):
        item = self.selected_item
        if item:
            if isinstance(item, RosterWidget.WingItem):
                ROSTER.remove_wing(item.obj)
            else:
                assert isinstance(item, RosterWidget.RosterTreeItem)
                item.obj.parent.remove(item.obj)
            self.update_model()

    @Slot()
    def load_from_file(self, alert=True):
        Roster.file_path = Config().roster_path
        if not exists(Roster.file_path):
            if alert:
                Gui.msgbox_say('{} does not exists'.format(Roster.file_path))
            return False
        ROSTER.read()
        self.update_model()

    @Slot()
    def save_to_file(self):
        Roster.file_path = Config().roster_path
        ROSTER.write()
        Gui.msgbox_say('Roster saved to {}'.format(Roster.file_path))


class FlightsWidget(AbstractWidget, qt_widget_flights.Ui_Form):
    sig_drop = Signal(object)

    class UnassignedPilotsItem(QStandardItem):
        def __init__(self):
            super().__init__()
            self.setText('Unassigned pilots')

    class FlightItem(QStandardItem):
        def __init__(self, parent_item, flight):
            super().__init__()
            self.setText(flight.name)
            self.children = []
            self.parent_item = parent_item
            self.flight = flight

        def add_child_item(self, child_item):
            self.children.append(child_item)

    class FlightsModel(QStandardItemModel):
        def __init__(self, parent):
            super().__init__(parent)
            self.headers = ['Name', 'zzz', 'zzz']
            self.__flights = {}
            self.__items = {}
            self.__unassigned_pilots_item = FlightsWidget.UnassignedPilotsItem()

        def flags(self, index):
            return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled

        def flight_from_item(self, item):
            pass

        def item_from_flight(self, flight):
            pass

        def make(self):
            self.clear()
            self.__unassigned_pilots_item = FlightsWidget.UnassignedPilotsItem()
            # print(self.__unassigned_pilots_item.flags().__int__())
            self.appendRow([self.__unassigned_pilots_item, None, None])
            print(FLIGHTS)
            for flight in FLIGHTS.flights:
                # print(flight)
                flight_item = FlightsWidget.FlightItem(self, flight)
                self.__flights[flight_item.index()] = flight
                self.__items[flight.id] = flight_item
                self.appendRow([flight_item, None, None])

    def __init__(self, parent, linked_btn):
        super().__init__(parent, linked_btn)
        self.model = FlightsWidget.FlightsModel(self)
        self.flights_view.setModel(self.model)

    def connect_elements(self):
        pass
        # self.flights_view.dragLeaveEvent.connect(self.test)

    def test(self):
        print('test')

    def update_model(self):
        self.model.make()


class Gui(AbstractGui, qt_main_ui.Ui_MainWindow):
    def __init__(self):
        super().__init__(__app_name__, APP_ICON, __version__)
        self.setupUi(self)

        self.widgets = []
        self.btns = []

        self.widget_units = UnitsWidget(self, self.btn_show_units)
        self.__add_widget(self.widget_units)

        self.widget_config = ConfigWidget(self, self.btn_show_config)
        self.__add_widget(self.widget_config)

        self.widget_roster = RosterWidget(self, self.btn_show_roster)
        self.__add_widget(self.widget_roster)

        self.widget_flights = FlightsWidget(self, self.btn_show_flights)
        self.__add_widget(self.widget_flights)

        # self.widget_radios = RadiosWidget(self)
        # self.__add_widget(self.widget_radios, self.btn_show_radios, self.widget_radios.show)

        # for widget in self.widgets:
        # self.hide_all_widgets()
        self.frame_welcome.show()
        self.connect_elements()
        self.miz = None

    def __add_widget(self, widget_obj):
        self.main_layout.addWidget(widget_obj)
        self.widgets.append(widget_obj)
        self.btns.append(widget_obj.linked_btn)
        widget_obj.linked_btn.clicked.connect(widget_obj.show)
        widget_obj.hide()

    def start(self):
        self.gather_skins()
        self.show()

    def load_miz_dialog(self):
        selected_miz = Utils.user_select('Open MIZ file', 'existing_file', str_filter='*.miz')
        if selected_miz:
            self.load_miz(selected_miz)

    def load_miz(self, path_to_miz):
        MAIN_PROC.load_miz(path_to_miz)
        # miz.load_from_miz(path_to_miz)

    def save_miz(self):
        raise NotImplementedError()

    def save_miz_as(self):
        raise NotImplementedError()

    def uncheck_all_buttons(self):
        for btn in self.btns:
            btn.setChecked(False)

    def hide_all_widgets(self):
        self.frame_welcome.hide()
        for widget in self.widgets:
            widget.hide()
        self.uncheck_all_buttons()

    def connect_elements(self):
        # self.action_show_units.triggered.connect(self.widget_units.show)
        self.action_load_miz.triggered.connect(self.load_miz_dialog)
        self.action_save_miz.triggered.connect(self.save_miz)
        self.action_save_miz_as.triggered.connect(self.save_miz_as)
        self.widget_units.btn_radios.clicked.connect(self.test_radios)
        self.widget_config.btn_rescan.clicked.connect(self.gather_skins)

    def test_radios(self):
        if not MIZ.is_loaded:
            return
        for unit_id in self.widget_units.selected_units_ids:
            unit = MIZ.mission.get_unit_by_id(unit_id)
            assert isinstance(unit, AbstractUnit)
            print(unit.unit_type)
            try:
                for radio_preset in unit.radio_presets:
                    assert isinstance(radio_preset, FlyingUnit.RadioPresets)
                    print(radio_preset.radio_name)
                    print(radio_preset._section_channels)
                    for channel, freq in radio_preset.channels:
                        print('{}: {}'.format(channel, freq))
            except TypeError as e:
                self._msgbox_say('This unit does not have any radio preset: {}'.format(e.msg))

    def mizfile_loading(self):
        self.statusbar.showMessage('Loading {}...'.format(MIZ.miz_path))

    def mizfile_loaded(self):
        self.statusbar.showMessage('Loaded {}'.format(MIZ.miz_path))
        for widget in self.widgets:
            widget.update_model()

    def gather_skins(self):
        MAIN_PROC.gather_skins()
        self.widget_config.label_skin_scan_result.setText(
            'Found {} skins'.format(sum(len(x) for _, x in skins.available_skins.items())))


def start():
    """
    Main ESME function.
    """
    try:

        LOGGER.debug('Starting {} {}'.format(__app_name__, CURRENT_VERSION))

        if FROZEN:
            LOGGER.debug('Running frozen {}, setting singleton and GUID'.format(__app_name__))
            singleton.SingleInstance(__guid__)
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(__guid__)
            except:
                pass
        else:
            LOGGER.debug('Running scripted {}'.format(__app_name__))

        if not Config().dcs_path:
            dcs_path = Utils.get_dcs_path()
            if dcs_path:
                Config().dcs_path = dcs_path
            else:
                Config().dcs_path = ''

        global UI
        UI = Gui()

        params = Params()

        while len(sys.argv) > 1:
            arg = sys.argv.pop()
            if arg == '/admin':
                params.admin = True
            elif arg == '/config':
                params.config = True
            elif arg == '/subscription':
                params.subscription = True
        LOGGER.debug('Options:\n{}'.format(params))

        LOGGER.debug('Starting main UI')
        UI.start()
        if not FROZEN:  # TESTING GROUND
            UI.load_miz(r'E:\Bibliothèques\Saved Games\DCS\Missions\LE FRONT_V2.miz')
        exit(QT_APP.exec())
    except:
        LOGGER.exception('uncaught error, sending crash report')
        Utils.send_crash_report()
        exit(1)


def extract_parking_spots():
    global DATABASE
    for file, aircraft_name in [('./Parking_MIZ/A10C.miz', 'A-10C'), ('./Parking_MIZ/Ka50.miz', 'Ka50'),
                                ('./Parking_MIZ/Mi8.miz', 'Mi8')]:
        # for file, aircraft_name in [('./Parking_MIZ/Mi8.miz', 'Mi8')]:
        with Miz(file) as miz:
            for country_id in miz.mission.d['coalition']['blue']['country'].keys():
                country = miz.mission.d['coalition']['blue']['country'][country_id]
                if 'plane' in country.keys():
                    for _, group in country['plane']['group'].items():
                        # group = mis.mission.d['coalition']['blue']['country'][10]['plane']['group'][k]
                        p = group['route']['points'][1]
                        airport_id = p['airdromeId']
                        parking_x = p['x']
                        parking_y = p['y']
                        if airport_id not in DATABASE['parking'].keys():
                            DATABASE['parking'][airport_id] = {}
                        if aircraft_name not in DATABASE['parking'][airport_id].keys():
                            DATABASE['parking'][airport_id][aircraft_name] = set()
                        DATABASE['parking'][airport_id][aircraft_name].add_child((float(parking_x), float(parking_y)))
                if 'helicopter' in country.keys():
                    for _, group in country['helicopter']['group'].items():
                        # group = mis.mission.d['coalition']['blue']['country'][10]['plane']['group'][k]
                        p = group['route']['points'][1]
                        airport_id = p['airdromeId']
                        parking_x = p['x']
                        parking_y = p['y']
                        if airport_id not in DATABASE['parking'].keys():
                            DATABASE['parking'][airport_id] = {}
                        if aircraft_name not in DATABASE['parking'][airport_id].keys():
                            DATABASE['parking'][airport_id][aircraft_name] = set()
                        DATABASE['parking'][airport_id][aircraft_name].add_child((float(parking_x), float(parking_y)))
    for airport_id in DATABASE['parking']:
        print(Airport.names[airport_id])
        for aircraft_name in DATABASE['parking'][airport_id].keys():
            print('\t{}'.format(aircraft_name))
            for parking in DATABASE['parking'][airport_id][aircraft_name]:
                print('\t\t{}'.format(parking))
    with open('esme.db', 'wb') as _f:
        _f.write(pdumps(DATABASE))


def test():
    pass
    # with Miz('./test/test_files/TRG_KA50.miz') as miz:
    #     print(miz.mission.ln10)
    #     for unit in miz.mission.blue_coa.units:
    #         assert isinstance(unit, AbstractUnit)
    #         print(unit.group_name)
    #         print(unit.unit_name)
    #         print(miz.mission.blue_coa.bullseye_position)
    #         print(miz.mission.red_coa.bullseye_position)
    #     print(miz.mission.next_group_id)
    #     print(miz.mission.next_unit_id)
    #     print(miz.mission.mission_start_time_as_date)
    #     return
    #     print(miz.mission.blue.units)
    #
    #     for country in miz.mission.blue.countries:
    #         assert isinstance(country, Country)
    #         print(country.country_name)
    #         for group in country.plane_groups:
    #             assert isinstance(group, Group)
    #             print('\t{}'.format(group.get_group_name(miz.ln10)))
    #             for unit in group.units:
    #                 assert isinstance(unit, AbstractUnit)
    #                 print('\t\t{}'.format(unit.get_unit_name(miz.ln10)))
    #                 print('\t\t{}'.format(unit.skill))
    #                 print('\t\t{}'.format(unit.unit_type))
    #                 print('\t\t{}'.format(unit.unit_position))
    #                 print('\t\t{}'.format(unit.group_id))
    #                 print('\t\t{}'.format(unit.unit_id))
    # print(miz.ln10)
    # print(miz.mission)
    # print(miz.ln10.get('DictKey_UnitName_72'))
    # print(miz.mission.artillery_commander_blue)
    # miz.mission.artillery_commander_red = 10
    # print(miz.mission.artillery_commander_red)
    # print(miz.mission.d['groundControl'])
    # print(miz.mission.start_time)
    # print(miz.mission.start_time_as_date)
    # miz.mission.start_time_as_date = '01/02/2016 01:38:00'
    # print(miz.mission.start_time_as_date)
    # # mis.zip()
    # print(miz.mission.cloud_thickness)
    # print(miz.mission.cloud_base)
    # print(miz.mission.fog_visibility)
    # print(miz.mission.fog_thickness)
    # print(miz.ln10)


if __name__ == '__main__':
    start()
    # extract_parking_spots()
    # with open('esme.db', 'rb') as _f:
    #     test = ploads(_f.read())
    # print(test)
    # test()

    # TODO avertir d'une update de briefing par mail: système de souscription ('subscribe to CLID', où CLID est une string aléatoire identifiant la mission, même chose pour unsubscribe) Chque fois qu'une nouvelle version du birefing est poussée en HTML sur le serveur, la mailing liste est avertie. LEs ubscribe/unsubscribe sont lus via une adresse email, les email sont parsés via sujet ('ESME - subscribe', avec la CLID en body).

# coding=utf-8
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from utils import make_logger

# noinspection PyProtectedMember
from src import global_
from src.cfg import Config
from .base import Shortcut, VLayout, Widget, WithMsgBox
from .itab import iTab
from .main_ui_interface import I
from .main_ui_progress import MainUiProgress
from .main_ui_threading import MainUiThreading

logger = make_logger(__name__)


class MainUi(QMainWindow, MainUiThreading, MainUiProgress, WithMsgBox):
    threading_queue = Queue()

    def __init__(self):
        # Fucking QMainWindow calls a general super().__init__ on every parent class, don't call them here !
        flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
        flags = flags | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint

        self.helpers = {}

        QMainWindow.__init__(
            self,
            flags=flags
        )

        WithMsgBox.__init__(self, global_.APP_SHORT_NAME, ':/ico/app.ico')

        self.resize(1024, 768)

        self.tabs = QTabWidget()

        layout = VLayout(
            [
                self.tabs
            ]
        )

        layout.setContentsMargins(10, 10, 10, 10)

        window = Widget()
        window.setLayout(layout)

        self.setCentralWidget(window)

        self.setWindowIcon(QIcon(':/ico/app.ico'))

        self.exit_shortcut = Shortcut(QKeySequence(Qt.Key_Escape), self, self.exit)

    def show_log_tab(self):
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def write_log(self, value: str, color: str):
        self.helpers['write_log'](value, color)

    def tab_reorder_update_view_after_remote_scan(self):
        self.helpers['tab_reorder_update_view_after_remote_scan']()

    def update_config_tab(self, version_check_result=None):
        self.helpers['update_config_tab'](version_check_result)

    def add_tab(self, tab: iTab, helpers: dict = None):
        self.tabs.addTab(tab, tab.tab_title)
        if helpers:
            for k in helpers.keys():
                self.helpers[k] = getattr(tab, helpers[k])

    def show(self):
        self.setWindowTitle(
            '{} v{} - {}'.format(global_.APP_SHORT_NAME,
                                 global_.APP_VERSION,
                                 global_.APP_RELEASE_NAME))
        self.setWindowState(self.windowState() & Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        super(QMainWindow, self).show()

        self.raise_()

    @staticmethod
    def exit(code=0):
        if global_.QT_APP:
            global_.QT_APP.exit(code)

    def closeEvent(self, event):
        self.exit()


def start_ui():
    from PyQt5.QtWidgets import QApplication
    import sys
    from src.ui.tab_reorder import TabReorder
    from src.ui.tab_log import TabLog
    from src.ui.tab_config import TabConfig
    logger.debug('starting QtApp object')
    global_.QT_APP = QApplication([])
    global_.MAIN_UI = MainUi()
    global_.MAIN_UI.add_tab(
        TabReorder(),
        helpers={
            'tab_reorder_update_view_after_remote_scan': 'tab_reorder_update_view_after_remote_scan'
        }
    )
    global_.MAIN_UI.add_tab(TabConfig(), helpers={'update_config_tab': 'update_config_tab'})
    global_.MAIN_UI.add_tab(TabLog(), helpers={'write_log': 'write'})
    global_.MAIN_UI.show()

    def pre_update_hook():
        if not hasattr(sys, 'frozen'):
            logger.warning('skipping update on script run')
            return False
        else:
            I.hide()
            return True

    def cancel_update_hook():
        I.show()

    from utils import Progress
    Progress.register_adapter(I)

    from src.updater import updater

    updater.find_and_install_latest_release(
        current_version=global_.APP_VERSION,
        cancel_update_hook=cancel_update_hook,
        pre_update_hook=pre_update_hook,
    )

    from src.misc.dcs_installs import DCSInstalls
    DCSInstalls().discover_dcs_installations()

    global_.MAIN_UI.update_config_tab()

    sys.exit(global_.QT_APP.exec())

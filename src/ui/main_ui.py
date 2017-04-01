# coding=utf-8
from queue import Queue
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QShortcut

# noinspection PyProtectedMember
from src import global_
from .base import Shortcut, VLayout, Widget
from .itab import iTab
from .main_ui_progress import MainUiProgress
from .main_ui_threading import MainUiThreading
from .main_ui_interface import I
from utils import make_logger

logger = make_logger(__name__)


class MainUi(QMainWindow, MainUiThreading, MainUiProgress):

    threading_queue = Queue()

    def __init__(self):
        # Fucking QMainWindow calls a general super().__init__ on every parent class, don't call them here !
        flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
        flags = flags | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint

        self.helpers = {}

        QMainWindow.__init__(
            self,
            parent=None,
            flags=flags
        )

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
    logger.debug('starting QtApp object')
    global_.QT_APP = QApplication([])
    global_.MAIN_UI = MainUi()
    global_.MAIN_UI.add_tab(TabReorder())
    global_.MAIN_UI.add_tab(TabLog(), helpers={'write_log': 'write'})
    global_.MAIN_UI.show()

    def pre_update_hook():
        if not hasattr(sys, 'frozen'):
            logger.warning('skipping update on script run')
            return False
        else:
            I.hide()
            return True

    from utils import Updater
    updater = Updater(
        executable_name='EMFT',
        current_version=global_.APP_VERSION,
        gh_user='132nd-etcher',
        gh_repo='EMFT',
        asset_filename='EMFT.exe',
        pre_update_func=pre_update_hook,
        cancel_update_func=I.show)
    updater.version_check('alpha')

    from utils import Progress
    Progress.register_adapter(I)

    sys.exit(global_.QT_APP.exec())

# coding=utf-8
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow
from emft.utils import make_logger

# noinspection PyProtectedMember
from emft import global_
from emft.ui.base import TabWidget
from emft.ui.main_ui_tab_widget import MainUiTabChild
from .base import Shortcut, VLayout, Widget
from .main_ui_interface import I
from .main_ui_mixins import MainUiMixins

LOGGER = make_logger(__name__)


class MainUi(QMainWindow, MainUiMixins):
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

        self.resize(1024, 768)

        self.tabs = TabWidget()

        layout = VLayout(
            [
                self.tabs
            ]
        )

        layout.setContentsMargins(10, 10, 10, 10)

        window = Widget()
        window.setLayout(layout)

        self.setCentralWidget(window)

        self.setWindowIcon(QIcon(global_.DEFAULT_ICON))

        self.exit_shortcut = Shortcut(QKeySequence(Qt.Key_Escape), self, self.exit)

        self.setWindowTitle(
            '{} v{} - {}'.format(global_.APP_SHORT_NAME,
                                 global_.APP_VERSION,
                                 global_.APP_RELEASE_NAME))

    def add_tab(self, tab: MainUiTabChild):
        setattr(self, 'tab_{}'.format(tab.tab_title), tab)
        self.tabs.addTab(tab)

    def show(self):
        self.setWindowState(self.windowState() & Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        super(QMainWindow, self).show()

        self.raise_()

    @staticmethod
    def exit(code=0):
        if global_.QT_APP:
            global_.QT_APP.exit(code)

    def closeEvent(self, event):  # noqa: N802
        self.exit()


def start_ui(show: bool = True):

    from PyQt5.QtWidgets import QApplication
    import sys
    LOGGER.info('starting application')
    global_.QT_APP = QApplication([])
    main_ui = MainUi()
    global_.MAIN_UI = main_ui

    LOGGER.info('loading module: re-order')
    from emft.reorder.ui.tab_reorder import TabChildReorder
    global_.MAIN_UI.add_tab(TabChildReorder(main_ui))

    # logger.info('loading module: dcs_installs')
    # from src.misc.fs import dcs_installs
    # dcs_installs.discover_dcs_installations()

    LOGGER.info('loading tab: skins')
    from emft.ui.tab_skins import TabChildSkins
    global_.MAIN_UI.add_tab(TabChildSkins(main_ui))

    LOGGER.info('loading tab: roster')
    from emft.ui.tab_roster import TabChildRoster
    global_.MAIN_UI.add_tab(TabChildRoster(main_ui))

    LOGGER.info('loading tab: radios')
    from emft.ui.tab_radios import TabChildRadios
    global_.MAIN_UI.add_tab(TabChildRadios(main_ui))

    LOGGER.info('loading tab: config')
    from emft.ui.tab_config import TabChildConfig
    global_.MAIN_UI.add_tab(TabChildConfig(main_ui))

    LOGGER.info('loading tab: log')
    from emft.ui.tab_log import TabChildLog
    global_.MAIN_UI.add_tab(TabChildLog(main_ui))

    LOGGER.info('loading tab: about')
    from emft.ui.tab_about import TabChildAbout
    global_.MAIN_UI.add_tab(TabChildAbout(main_ui))

    if show:
        global_.MAIN_UI.show()

    LOGGER.info('loading adapter: Progress')
    from emft.utils import Progress
    # noinspection PyTypeChecker
    Progress.register_adapter(I)

    LOGGER.info('loading module: updater')
    from emft.updater import updater

    updater.look_for_new_version(auto_update=True)

    LOGGER.info('starting GUI')

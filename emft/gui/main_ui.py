# coding=utf-8
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow

from emft.__version__ import __version__
# noinspection PyProtectedMember
from emft.core import constant
from emft.core.logging import make_logger
from emft.gui.base import Shortcut, TabWidget, VLayout, Widget
from emft.gui.main_ui_interface import I
from emft.gui.main_ui_mixins import MainUiMixins
from emft.gui.main_ui_tab_widget import MainUiTabChild

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

        self.setWindowIcon(QIcon(constant.DEFAULT_ICON))

        self.exit_shortcut = Shortcut(QKeySequence(Qt.Key_Escape), self, self.exit)

        self.setWindowTitle(
            '{} v{} - {}'.format(constant.APP_SHORT_NAME,
                                 __version__,
                                 constant.APP_RELEASE_NAME))

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
        if constant.QT_APP:
            constant.QT_APP.exit(code)

    def closeEvent(self, event):  # noqa: N802
        self.exit()


def start_ui(show: bool = True):
    from PyQt5.QtWidgets import QApplication
    LOGGER.info('starting application')
    constant.QT_APP = QApplication([])
    main_ui = MainUi()
    constant.MAIN_UI = main_ui

    LOGGER.info('loading module: re-order')
    from emft.plugins.reorder.gui import TabChildReorder
    constant.MAIN_UI.add_tab(TabChildReorder(main_ui))

    # logger.info('loading module: dcs_installs')
    # from src.misc.fs import dcs_installs
    # dcs_installs.discover_dcs_installations()

    LOGGER.info('loading tab: skins')
    from emft.gui.tab_skins import TabChildSkins
    constant.MAIN_UI.add_tab(TabChildSkins(main_ui))

    LOGGER.info('loading tab: roster')
    from emft.gui.tab_roster import TabChildRoster
    constant.MAIN_UI.add_tab(TabChildRoster(main_ui))

    LOGGER.info('loading tab: radios')
    from emft.gui.tab_radios import TabChildRadios
    constant.MAIN_UI.add_tab(TabChildRadios(main_ui))

    LOGGER.info('loading tab: config')
    from emft.gui.tab_config import TabChildConfig
    constant.MAIN_UI.add_tab(TabChildConfig(main_ui))

    LOGGER.info('loading tab: log')
    from emft.gui.tab_log import TabChildLog
    constant.MAIN_UI.add_tab(TabChildLog(main_ui))

    LOGGER.info('loading tab: about')
    from emft.gui.tab_about import TabChildAbout
    constant.MAIN_UI.add_tab(TabChildAbout(main_ui))

    if show:
        constant.MAIN_UI.show()

    LOGGER.info('loading adapter: Progress')
    from emft.core import progress
    # noinspection PyTypeChecker
    progress.Progress.register_adapter(I)

    LOGGER.info('loading module: updater')
    from emft.updater import updater
    updater.updater.look_for_new_version(auto_update=True)

    LOGGER.info('starting GUI')

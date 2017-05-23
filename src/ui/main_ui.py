# coding=utf-8
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow
from utils import make_logger, nice_exit

# noinspection PyProtectedMember
from src import global_
from src.cfg import Config
from src.ui.base import TabWidget
from src.ui.main_ui_tab_widget import MainUiTabChild
from .base import Shortcut, VLayout, Widget
from .main_ui_interface import I
from .main_ui_mixins import MainUiMixins

logger = make_logger(__name__)


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
        nice_exit(code)

    def closeEvent(self, event):
        self.exit()


def start_ui(test=False):
    from PyQt5.QtWidgets import QApplication
    import sys
    logger.info('starting application')
    global_.QT_APP = QApplication([])
    main_ui = MainUi()
    global_.MAIN_UI = main_ui

    logger.info('loading module: re-order')
    from src.ui.tab_reorder import TabChildReorder
    global_.MAIN_UI.add_tab(TabChildReorder(main_ui))

    logger.info('loading module: dcs_installs')
    from src.misc.fs import dcs_installs
    dcs_installs.discover_dcs_installations()

    logger.info('loading tab: skins')
    from src.ui.tab_skins import TabChildSkins
    global_.MAIN_UI.add_tab(TabChildSkins(main_ui))

    logger.info('loading tab: roster')
    from src.ui.tab_roster import TabChildRoster
    global_.MAIN_UI.add_tab(TabChildRoster(main_ui))

    logger.info('loading tab: radios')
    from src.radio.ui import TabChildRadios
    global_.MAIN_UI.add_tab(TabChildRadios(main_ui))

    logger.info('loading tab: config')
    from src.ui.tab_config import TabChildConfig
    global_.MAIN_UI.add_tab(TabChildConfig(main_ui))

    logger.info('loading tab: log')
    from src.ui.tab_log import TabChildLog
    global_.MAIN_UI.add_tab(TabChildLog(main_ui))

    logger.info('loading tab: about')
    from src.ui.tab_about import TabChildAbout
    global_.MAIN_UI.add_tab(TabChildAbout(main_ui))

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

    logger.info('loading adapter: Progress')
    from utils import Progress
    # noinspection PyTypeChecker
    Progress.register_adapter(I)

    logger.info('loading module: updater')
    from src.updater import updater
    updater.find_and_install_latest_release(
        current_version=global_.APP_VERSION,
        executable_path='emft.exe',
        channel=Config().update_channel,
        cancel_update_hook=cancel_update_hook,
        pre_update_hook=pre_update_hook,
    )

    if test:
        logger.critical('RUNNING IN TEST MODE')
        import time
        import src.sentry.sentry
        from utils import ThreadPool, nice_exit
        src.sentry.sentry.CRASH = True

        def test_hook():
            logger.critical('TEST MODE: waiting 10 seconds')
            time.sleep(10)
            logger.critical('TEST MODE: end of timer')
            nice_exit()

        pool = ThreadPool(1, 'test', _daemon=True)
        pool.queue_task(test_hook)

    logger.info('starting GUI')
    sys.exit(global_.QT_APP.exec())

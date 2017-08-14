# coding=utf-8
"""
References all modules that add methods to the MainUI.

Those methods will be made available through the MainUI interface ("I") and will be thread-safe.
"""

from emft.gui.main_ui_msgbox_adapter import MainUiMsgBoxAdapter
from emft.gui.main_ui_progress_adapter import MainUIProgressAdapter
from emft.gui.main_ui_threading_adapter import MainUiThreadingAdapter
from emft.gui.tab_config_adapter import TabConfigAdapter
from emft.gui.tab_log_adapter import TabLogAdapter
from emft.gui.tab_roster_adapter import TabRosterAdapter
from emft.gui.tab_skins_adapter import TabSkinsAdapter
from emft.plugins.reorder.adapter.tab_reorder_adapter import TabReorderAdapter


# noinspection PyAbstractClass
class MainUiMixinsAdapter(
    MainUIProgressAdapter,
    MainUiMsgBoxAdapter,
    MainUiThreadingAdapter,
    TabConfigAdapter,
    TabLogAdapter,
    TabReorderAdapter,
    TabRosterAdapter,
    TabSkinsAdapter,
):
    pass

# coding=utf-8
"""
References all modules that add methods to the MainUI.

Those methods will be made available through the MainUI interface ("I") and will be thread-safe.
"""

from .main_ui_msgbox_adapter import MainUiMsgBoxAdapter
from .main_ui_progress_adapter import MainUIProgressAdapter
from .main_ui_threading_adapter import MainUiThreadingAdapter
from .tab_config_adapter import TabConfigAdapter
from .tab_log_adapter import TabLogAdapter
from .tab_roster_adapter import TabRosterAdapter
from .tab_skins_adapter import TabSkinsAdapter
from emft.reorder.adapter.tab_reorder_adapter import TabReorderAdapter


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

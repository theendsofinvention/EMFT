# coding=utf-8

from src.cfg import Config
from src.reorder.adapter.tab_reorder_adapter import TabReorderAdapter, TAB_NAME
from src.reorder.service.reorder_miz import ReorderMiz
from src.ui.base import VLayout, Label, Checkbox, GroupBox, Radio, HLayout, PushButton, HSpacer
from src.ui.main_ui_tab_widget import MainUiTabChild
from src.utils.custom_logging import make_logger
from .widget_manual_reorder import WidgetManualReorder
from .widget_auto_reorder import WidgetAutoReorder

logger = make_logger(__name__)


class TabChildReorder(MainUiTabChild, TabReorderAdapter):
    def tab_reorder_update_view_after_artifact_scan(self, *args, **kwargs):
        pass

    def tab_reorder_update_view_after_branches_scan(self, *args, **kwargs):
        pass

    def tab_reorder_change_active_profile(self, new_profile_name):
        pass

    def tab_clicked(self):
        pass

    @property
    def tab_title(self):
        return TAB_NAME

    def __init__(self, parent=None):
        MainUiTabChild.__init__(self, parent=parent)

        self.check_skip_options = Checkbox(
            'Skip "options" file',
            self._on_click_option_checkbox
        )

        self.radio_manual = Radio('Manual mode', self._on_click_radio_manual_or_auto)
        self.radio_auto = Radio('Auto mode', self._on_click_radio_manual_or_auto)

        self.widget_manual = WidgetManualReorder(self)
        self.widget_auto = WidgetAutoReorder(self)

        self.btn_reorder = PushButton(
            text='Reorder MIZ file',
            func=self._on_click_reorder_btn,
            parent=self,
            min_height=40,
        )

        self.setLayout(
            VLayout(
                [
                    Label(
                        'By design, LUA tables are unordered, which makes tracking changes extremely difficult.\n\n'
                        'This lets you reorder them alphabetically before you push them in a SCM.'
                    ),
                    GroupBox(
                        'Options',
                        VLayout(
                            [
                                self.check_skip_options,
                                Label(
                                    'The "options" file at the root of the MIZ is player-specific, and is of very'
                                    ' relative import for the MIZ file itself. To avoid having irrelevant changes in'
                                    ' the SCM, it can be safely skipped during reordering.'
                                ),
                            ],
                        ),
                    ),
                    GroupBox(
                        title='Select re-ordering method',
                        layout=HLayout(
                            [
                                HSpacer(),
                                self.radio_manual,
                                HSpacer(),
                                self.radio_auto,
                                HSpacer(),
                            ],
                        ),
                    ),
                    GroupBox(
                        title='Reordering setup',
                        layout=VLayout(
                            [
                                self.widget_manual,
                                self.widget_auto,
                            ],
                        ),
                    ),
                    self.btn_reorder,
                ],
                # set_stretch=[(3, 1)]
                # add_stretch=True,
            ),
        )

        self._load_from_config()

    def _load_from_config(self):
        self.radio_auto.setChecked(Config().auto_mode)
        self.radio_manual.setChecked(not Config().auto_mode)
        self.check_skip_options.setChecked(Config().skip_options_file)

    def _write_selected_mode_to_config(self):
        Config().auto_mode = self._auto_mode_is_selected

    @property
    def _manual_mode_is_selected(self):
        return self.radio_manual.isChecked()

    @property
    def _auto_mode_is_selected(self):
        return self.radio_auto.isChecked()

    def _on_click_option_checkbox(self):
        Config().skip_options_file = self.check_skip_options.isChecked()

    def _on_click_radio_manual_or_auto(self):
        self.widget_manual.setVisible(self.radio_manual.isChecked())
        self.widget_auto.setVisible(self.radio_auto.isChecked())
        self._write_selected_mode_to_config()

    def _reorder_manual(self):
        ReorderMiz().reorder_miz_file(
            miz_file_path=self.widget_manual.path_to_miz,
            output_folder_path=self.widget_manual.path_to_output_folder,
            skip_option_file=self.check_skip_options.isChecked(),
        )

    def _reorder_auto(self):
        ReorderMiz().reorder_miz_file(
            miz_file_path=self.widget_auto.path_to_miz,
            output_folder_path=self.widget_auto.path_to_output_folder,
            skip_option_file=self.check_skip_options.isChecked(),
        )

    def _on_click_reorder_btn(self):
        if self._manual_mode_is_selected:
            self._reorder_manual()
        elif self._auto_mode_is_selected:
            self._reorder_auto()

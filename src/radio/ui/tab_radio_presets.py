# coding=utf-8
import typing

from src.radio import radios
from src.radio.ui.tab_radio_edit import RadioEditTab
from src.ui.base import TabChild, VLayout, TabWidget, SIGNAL


class _RadiosTabWidget(TabWidget):
    """I'm so lazy ..."""

    @property
    def tabs(self) -> typing.Generator['RadioEditTab', None, None]:
        return super(_RadiosTabWidget, self).tabs

    def get_tab_from_title(self, tab_title: str) -> 'RadioEditTab':
        return super(_RadiosTabWidget, self).get_tab_from_title(tab_title)


class EditPresetsWidget(TabChild):

    data_changed = SIGNAL()

    def tab_leave(self):
        if self.data_has_changed:
            from src.global_ import MAIN_UI
            return MAIN_UI.confirm('You have unsaved changes in your radios preset\n\n'
                                   'Are you sure you want to leave?')
        return True

    def tab_clicked(self):
        pass

    @property
    def tab_title(self) -> str:
        return 'Edit presets'

    def __init__(self, parent=None):
        TabChild.__init__(self, parent)
        self.tab_widget = _RadiosTabWidget(self)
        self._parent_widget = parent

        for radio in radios:
            sub_tab = RadioEditTab(radio, self.tab_widget)
            sub_tab.data_changed.connect(self.on_data_changed)
            self.tab_widget.addTab(sub_tab)

        self.setLayout(
            VLayout(
                [
                    self.tab_widget
                ]
            )
        )
        self.data_has_changed = False

    def on_data_changed(self):
        self.data_has_changed = True
        # noinspection PyUnresolvedReferences
        self.data_changed.emit()
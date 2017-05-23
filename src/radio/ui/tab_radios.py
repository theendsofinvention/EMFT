# coding=utf-8
import os

from utils import make_logger, Path

from src.cfg import Config
from src.radio import MetaFilePresets
from src.radio.ui.tab_radio_presets import EditPresetsWidget
from src.radio.ui.tab_radios_adapter import TAB_NAME, TabRadiosAdapter
from src.ui.base import VLayout, TabWidget, HLayout, HSpacer, \
    LineEdit, PushButton, GroupBox, BrowseDialog
from src.ui.main_ui_tab_widget import MainUiTabChild

logger = make_logger(__name__)


class TabChildRadios(MainUiTabChild, TabRadiosAdapter):
    def tab_leave(self):
        if self.data_has_changed:
            return self.main_ui.confirm('You have unsaved changes in your radios preset\n\n'
                                        'Are you sure you want to leave?')
        return True

    def tab_clicked(self):
        pass

    @property
    def tab_title(self) -> str:
        return TAB_NAME

    def __init__(self, parent=None):
        super(TabChildRadios, self).__init__(parent)
        self.tab_widget = TabWidget(self)

        self.presets_editor_tab = EditPresetsWidget(self)
        self.presets_editor_tab.data_changed.connect(self.on_data_changed)
        self.tab_widget.addTab(self.presets_editor_tab)

        self.meta_path = LineEdit(Config().tab_radios_meta_path or '', self._on_meta_path_changed, read_only=True)
        self.browse_meta = PushButton('Browse', self._browse_preset_file)
        self.show_meta = PushButton('Show in explorer', self._show_preset_file)
        self.load_meta = PushButton('Reload presets file', self._load_preset_file)
        self.save_meta = PushButton('Save presets file', self._save_preset_file)

        self.setLayout(
            VLayout(
                [
                    GroupBox(
                        'Presets file',
                        HLayout(
                            [
                                self.meta_path,
                                self.browse_meta,
                                self.show_meta,
                                self.load_meta,
                                self.save_meta,
                                HSpacer()
                            ]
                        ),
                    ),
                    self.tab_widget
                ]
            )
        )
        self.__update()
        self.save_meta.setEnabled(False)
        self.data_has_changed = False

    def on_data_changed(self):
        self.data_has_changed = True
        self.save_meta.setEnabled(True)

    def __update(self):
        self.save_meta.setEnabled(bool(self.__meta_path))
        self.show_meta.setEnabled(bool(self.__meta_path))
        self.load_meta.setEnabled(bool(self.__meta_path))
        self._load_preset_file()

    @property
    def __meta_path(self) -> Path:
        if self.meta_path.text():
            return Path(self.meta_path.text())

    def _on_meta_path_changed(self, *_):
        Config().tab_radios_meta_path = self.meta_path.text()
        self.__update()

    def _show_preset_file(self):
        if self.__meta_path:
            os.startfile(str(self.__meta_path.dirname()))

    def _browse_preset_file(self):
        init_dir = Path(Config().tab_radios_meta_path_last_dir or '.')
        if not init_dir.exists():
            init_dir = '.'
        p = BrowseDialog.save_file(self, 'Select a preset file', filter_=['.radio_presets'], init_dir=init_dir)
        if p:
            self.meta_path.setText(p.abspath())
            Config().tab_radios_meta_path_last_dir = str(p.dirname())

    def _save_preset_file(self):
        if self.__meta_path:
            self.presets_editor_tab.blockSignals(True)
            meta = MetaFilePresets(self.__meta_path)
            for tab in self.presets_editor_tab.tab_widget.tabs:
                radio_name, radio_channels = tab.to_meta()
                meta[radio_name] = radio_channels
            meta.write()
            self.save_meta.setEnabled(False)
            self.data_has_changed = False
            self.presets_editor_tab.blockSignals(False)

    def _load_preset_file(self):
        if self.__meta_path:
            self.presets_editor_tab.blockSignals(True)
            meta = MetaFilePresets(self.__meta_path)
            meta.read()
            for radio in meta:
                radio_tab = self.presets_editor_tab.tab_widget.get_tab_from_title(radio)
                radio_tab.from_meta(meta[radio])
            self.save_meta.setEnabled(False)
            self.data_has_changed = False
            self.presets_editor_tab.blockSignals(False)

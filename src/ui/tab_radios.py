# coding=utf-8
import os
import typing
from collections import OrderedDict

from utils import make_logger, Path

from src.cfg import Config
from src.radio import radios, empty_presets, MetaChannel, MetaPresets, MetaRadio
from src.ui.base import VLayout, Label, TabWidget, TabChild, TableView, TableEditableModel, HLayout, HSpacer, \
    GridLayout, LineEdit, PushButton, GroupBox, BrowseDialog
from src.ui.main_ui_tab_widget import MainUiTabChild
from .tab_radios_adapter import TAB_NAME, TabRadiosAdapter

logger = make_logger(__name__)


class _RadioEditTab(TabChild):
    @property
    def tab_title(self) -> str:
        return self.name

    def tab_clicked(self):
        pass

    def __init__(self, radio_name, radio_freq_min, radio_freq_max, radio_channels_qty, radio_aicrafts,
                 widget_parent=None):
        TabChild.__init__(self, widget_parent)
        self.name = radio_name
        self.min = radio_freq_min
        self.max = radio_freq_max
        self.qty = radio_channels_qty
        self.ac = radio_aicrafts

        self.headers = ['Channel', 'Frequency', 'Description']

        self.table = TableView(self)
        self.model = TableEditableModel(
            data=list(
                list(x) for x in zip(
                    range(1, int(self.qty) + 1),
                    empty_presets[self.name],
                    [''] * self.qty
                )
            ),
            delegates=[
                None,
                TableEditableModel.FloatDelegate(self.min, self.max),
                TableEditableModel.StringDelegate(r'[a-zA-Z0-9\.\;\:\-]*')
            ],
            align=['c', 'c', 'l'],
            header_data=self.headers,
            parent=self
        )
        self.table.setModel(self.model)

        self.setLayout(
            VLayout(
                [
                    GridLayout(
                        [
                            [

                                Label('Aircrafts with this radio: {}'.format(', '.join(ac for ac in self.ac))),
                                (Label('Minimum value: {}'.format(self.min)), dict(align='c')),
                                (Label('Maximum value: {}'.format(self.max)), dict(align='r')),
                            ]
                        ],
                        auto_right=False
                    ),
                    self.table
                ]
            )
        )

    def to_meta(self):

        def get_channels():
            for c in range(self.qty):
                freq = float(self.model.data(self.model.index(c, 1)))
                freq = '{:07.3f}'.format(freq)
                desc = str(self.model.data(self.model.index(c, 2)))
                yield freq, desc

        return self.name, list(channel for channel in get_channels())

    def from_meta(self, channels):

        for idx, channel in enumerate(channels):
            freq, desc = channel
            self.model.setData(self.model.index(idx, 0), str(idx + 1))
            self.model.setData(self.model.index(idx, 1), str(freq))
            self.model.setData(self.model.index(idx, 2), str(desc))





class _RadiosTabWidget(TabWidget):
    """I'm so lazy ..."""

    @property
    def tabs(self) -> typing.Generator['_RadioEditTab', None, None]:
        return super(_RadiosTabWidget, self).tabs

    def get_tab_from_title(self, tab_title: str) -> '_RadioEditTab':
        return super(_RadiosTabWidget, self).get_tab_from_title(tab_title)


class EditPresetsWidget(TabChild):
    def tab_clicked(self):
        pass

    @property
    def tab_title(self) -> str:
        return 'Edit presets'

    def __init__(self, parent=None):
        TabChild.__init__(self, parent)
        self.tab_widget = _RadiosTabWidget(self)

        self.meta_path = LineEdit(Config().tab_radios_meta_path or '', self._on_meta_path_changed, read_only=True)
        self.browse_meta = PushButton('Browse', self._browse_preset_file)
        self.show_meta = PushButton('Show in explorer', self._show_preset_file)
        self.load_meta = PushButton('Reload presets file', self._load_preset_file)
        self.save_meta = PushButton('Save presets file', self._save_preset_file)

        for radio in radios:
            self.tab_widget.addTab(
                _RadioEditTab(radio.name, radio.min, radio.max, radio.qty, radio.ac, self.tab_widget)
            )

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
            os.startfile(self.__meta_path.dirname())

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
            meta = MetaPresets(self.__meta_path)
            for tab in self.tab_widget.tabs:
                radio_name, radio_channels = tab.to_meta()
                meta[radio_name] = radio_channels
            meta.write()

    def _load_preset_file(self):
        if self.__meta_path:
            meta = MetaPresets(self.__meta_path)
            meta.read()
            for radio in meta:
                radio_tab = self.tab_widget.get_tab_from_title(radio)
                radio_tab.from_meta(meta[radio])
                # print(radio, meta[radio])


class TabChildRadios(MainUiTabChild, TabRadiosAdapter):
    def tab_clicked(self):
        pass

    @property
    def tab_title(self) -> str:
        return TAB_NAME

    def __init__(self, parent=None):
        super(TabChildRadios, self).__init__(parent)
        self.tab_widget = TabWidget(self)

        self.tab_widget.addTab(EditPresetsWidget(self))

        self.setLayout(
            VLayout(
                [
                    self.tab_widget
                ]
            )
        )

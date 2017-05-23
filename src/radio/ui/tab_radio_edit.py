# coding=utf-8
from src.radio import empty_presets, Radio
from src.ui.base import TabChild, TableView, TableEditableModel, VLayout, GridLayout, Label, SIGNAL
from src.ui.main_ui_interface import I


class RadioEditTab(TabChild):

    data_changed = SIGNAL()

    @property
    def tab_title(self) -> str:
        return self.radio.name

    def tab_clicked(self):
        pass

    def __init__(self, radio: Radio, widget_parent=None):
        TabChild.__init__(self, widget_parent)
        self.radio = radio

        self.headers = ['Channel', 'Frequency', 'Description']

        self.table = TableView(self)
        self.model = TableEditableModel(
            data=list(
                list(x) for x in zip(
                    range(1, int(self.radio.channel_qty) + 1),
                    [self.radio.min_freq] * self.radio.channel_qty,
                    [''] * self.radio.channel_qty
                )
            ),
            delegates=[
                None,
                TableEditableModel.FloatDelegate(self.radio.min_freq, self.radio.max_freq),
                TableEditableModel.StringDelegate(r'[a-zA-Z0-9\.\;\:\- ]*')
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

                                Label('Aircrafts with this radio: {}'.format(', '.join(ac for ac in self.radio.aircrafts))),
                                (Label('Minimum value: {}'.format(self.radio.min_freq)), dict(align='c')),
                                (Label('Maximum value: {}'.format(self.radio.max_freq)), dict(align='r')),
                            ]
                        ],
                        auto_right=False
                    ),
                    self.table
                ]
            )
        )
        # noinspection PyUnresolvedReferences
        self.model.dataChanged.connect(self._on_data_change)
        self.data_has_changed = False

    def _on_data_change(self):
        self.data_has_changed = True
        # noinspection PyUnresolvedReferences
        self.data_changed.emit()

    def to_meta(self):

        def get_channels():
            for c in range(self.radio.channel_qty):
                freq = float(self.model.data(self.model.index(c, 1)))
                freq = '{:07.3f}'.format(freq)
                desc = str(self.model.data(self.model.index(c, 2)))
                yield freq, desc

        return self.radio.name, list(channel for channel in get_channels())

    def from_meta(self, channels):

        self.model.beginResetModel()
        for idx, channel in enumerate(channels):
            freq, desc = channel
            self.model.setData(self.model.index(idx, 0), str(idx + 1))
            self.model.setData(self.model.index(idx, 1), str(freq))
            self.model.setData(self.model.index(idx, 2), str(desc))
        self.model.endResetModel()
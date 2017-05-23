# coding=utf-8
from src.radio import empty_presets
from src.ui.base import TabChild, TableView, TableEditableModel, VLayout, GridLayout, Label, SIGNAL


class RadioEditTab(TabChild):

    data_changed = SIGNAL()

    @property
    def tab_title(self) -> str:
        return self.name

    def tab_clicked(self):
        pass

    def __init__(self, preset_widget, radio_name, radio_freq_min, radio_freq_max, radio_channels_qty, radio_aicrafts,
                 widget_parent=None):
        TabChild.__init__(self, widget_parent)
        self._preset_widget = preset_widget
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
        # noinspection PyUnresolvedReferences
        self.model.dataChanged.connect(lambda: self.data_changed.emit())

    def to_meta(self):

        def get_channels():
            for c in range(self.qty):
                freq = float(self.model.data(self.model.index(c, 1)))
                freq = '{:07.3f}'.format(freq)
                desc = str(self.model.data(self.model.index(c, 2)))
                yield freq, desc

        return self.name, list(channel for channel in get_channels())

    def from_meta(self, channels):

        self.model.beginResetModel()
        for idx, channel in enumerate(channels):
            freq, desc = channel
            self.model.setData(self.model.index(idx, 0), str(idx + 1))
            self.model.setData(self.model.index(idx, 1), str(freq))
            self.model.setData(self.model.index(idx, 2), str(desc))
        self.model.endResetModel()
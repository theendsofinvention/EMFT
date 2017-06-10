# coding=utf-8

from src.reorder.service.browse_for_files import BrowseForFiles
from src.ui.base import VLayout, Label, Widget, LineEdit, PushButton, GridLayout
from src.utils import Path, make_logger

logger = make_logger(__name__)


class WidgetAutoReorder(Widget):
    def __init__(self, parent=None):
        Widget.__init__(self, parent)

        self.help_label = Label(
            text='Manual re-ordering is the simplest method available.\n\n'
                 'You can select a single MIZ file, and output its re-ordered files in a folder of your choosing.\n\n'
        )

        self.label_miz = Label(
            text='Miz file:'
        )
        self.le_path_to_miz = LineEdit(
            text='',
            read_only=True
        )
        self.btn_browse_for_miz = PushButton(
            text='Browse',
            func=self._on_browse_for_miz_clicked,
            parent=self
        )
        self.btn_open_miz = PushButton(
            text='Open',
            func=self._on_open_miz_clicked,
            parent=self
        )

        self.label_output_folder = Label(
            text='Output folder:'
        )
        self.le_path_to_output_folder = LineEdit(
            text='',
            read_only=True
        )
        self.btn_browse_for_output_folder = PushButton(
            text='Browse',
            func=self._on_browse_for_miz_clicked,
            parent=self
        )
        self.btn_open_output_folder = PushButton(
            text='Open',
            func=self._on_open_miz_clicked,
            parent=self
        )

        self.setLayout(
            VLayout(
                [
                    self.help_label,
                    GridLayout(
                        [
                            [
                                self.label_miz,
                                self.le_path_to_miz,
                                self.btn_browse_for_miz,
                                self.btn_open_miz,
                            ],
                            [
                                self.label_output_folder,
                                self.le_path_to_output_folder,
                                self.btn_browse_for_output_folder,
                                self.btn_open_output_folder,
                            ],
                        ],
                    ),
                ],
                add_stretch=True
            ),
        )

    @property
    def _path_to_miz(self) -> Path:
        return Path(self.le_path_to_miz.text())

    @property
    def _path_to_output_folder(self) -> Path:
        return Path(self.le_path_to_output_folder.text())

    def _on_browse_for_miz_clicked(self):
        # noinspection PyUnusedLocal
        path_to_miz = BrowseForFiles.browse_for_miz(self)

    def _on_open_miz_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(self._path_to_miz)

    def _on_browse_for_output_folder_clicked(self):
        # noinspection PyUnusedLocal
        path_to_miz = BrowseForFiles.browse_for_output_folder(self)

    def _on_open_output_folder_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(self._path_to_miz)

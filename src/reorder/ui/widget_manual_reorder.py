# coding=utf-8

from src.cfg import Config
from src.reorder.service.browse_for_files import BrowseForFiles
from src.reorder.service.manage_output_folders import ManageOutputFolders
from src.reorder.ui.dialog_edit_output_folder import DialogEditOutputFolder
from src.reorder.value.output_folder_model import OutputFoldersModelContainer
from src.ui.base import VLayout, Label, Widget, LineEdit, PushButton, HLayout, GridLayout, Combo, HSpacer
from src.utils import Path, make_logger

logger = make_logger(__name__)


class WidgetManualReorder(Widget):
    def __init__(self, parent=None):
        Widget.__init__(self, parent)

        self.help_label = Label(
            text='Manual re-ordering is the simplest method available.\n\n'
                 'You can select a single MIZ file, and output its re-ordered files in a folder of your choosing.\n\n'
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

        self.combo_output_folder = Combo(
            self._on_combo_output_folder_activated,
            parent=self,
            model=OutputFoldersModelContainer().model
        )

        self.btn_add_output_folder = PushButton(
            text='Add',
            func=self._on_btn_add_output_folder_clicked
        )

        self.btn_remove_output_folder = PushButton(
            text='Remove',
            func=self._on_btn_remove_output_folder_clicked
        )

        self.label_output_folder_path = PushButton('', self._on_output_folder_clicked)
        self.label_output_folder_path.setFlat(True)

        self.setLayout(
            VLayout(
                [
                    self.help_label,
                    GridLayout(
                        [
                            [
                                Label('MizFile'),
                                self.le_path_to_miz,
                                self.btn_browse_for_miz,
                                self.btn_open_miz,
                            ],
                            [
                                Label('Output folder'),
                                self.combo_output_folder,
                                self.btn_add_output_folder,
                                self.btn_remove_output_folder,
                            ],
                            [
                                None,
                                HLayout(
                                    [
                                        Label('Selected output folder path:', word_wrap=False),
                                        self.label_output_folder_path,
                                        Label('(click to open in explorer)'),
                                        HSpacer(),
                                    ]
                                ),
                                None,
                            ],
                        ],
                    ),
                ],
                add_stretch=True
            ),
        )

        self._load_values_from_config()

    def _update_output_folder_path_label(self):
        if self.selected_output_folder_name:
            output_folder = ManageOutputFolders.get_by_name(self.selected_output_folder_name)
            self.label_output_folder_path.setText(str(output_folder.abspath()))

    def _load_values_from_config(self):
        if Config().last_used_output_folder_in_manual_mode:
            try:
                self.combo_output_folder.set_index_from_text(Config().last_used_output_folder_in_manual_mode)
                self._update_output_folder_path_label()
            except ValueError:
                pass
        if Config().last_miz_file_in_manual_mode:
            self.le_path_to_miz.setText(Config().last_miz_file_in_manual_mode)

    def _on_combo_output_folder_activated(self):
        if self.selected_output_folder_name:
            Config().last_used_output_folder_in_manual_mode = self.selected_output_folder_name
            self._update_output_folder_path_label()

    @property
    def path_to_miz(self) -> str:
        return str(Path(self.le_path_to_miz.text()).abspath())

    @property
    def path_to_output_folder(self):
        output_folder = ManageOutputFolders().get_by_name(self.selected_output_folder_name)
        return str(output_folder.abspath())

    @property
    def selected_output_folder_name(self) -> str:
        return self.combo_output_folder.currentText()

    def _on_browse_for_miz_clicked(self):
        path_to_miz = BrowseForFiles.browse_for_miz(self)
        if path_to_miz:
            self.le_path_to_miz.setText(str(path_to_miz.abspath()))
            Config().last_miz_file_in_manual_mode = self.path_to_miz

    def _on_open_miz_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(self.path_to_miz)

    def _on_btn_add_output_folder_clicked(self):
        dialog = DialogEditOutputFolder(self)
        dialog.exec()

    def _on_btn_remove_output_folder_clicked(self):
        ManageOutputFolders.remove_output_folder(self.selected_output_folder_name)

    def _on_output_folder_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(self.path_to_output_folder)

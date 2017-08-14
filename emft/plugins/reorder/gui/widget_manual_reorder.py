# coding=utf-8

from emft.config import Config
from emft.core.logging import make_logger
from emft.core.path import Path
from emft.gui.base import Combo, GridLayout, HLayout, HSpacer, Label, LineEdit, PushButton, VLayout, Widget
from emft.plugins.reorder.finder import FindOutputFolder
from emft.plugins.reorder.service import BrowseForFiles, ManageOutputFolders
from emft.plugins.reorder.value.output_folder_model import OutputFoldersModelContainer
from .dialog_edit_output_folder import DialogEditOutputFolder

LOGGER = make_logger(__name__)


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

        self.label_help_output_folder = Label(
            text='The output folder is where EMFT will unzip the re-ordered mission files. '
                 'All the content of the MIZ files will end up in that folder.\n\n'
                 'Usually, this will be your SCM folder (ie. your Github repository).',
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
                            [40],
                            [
                                Label('Output folder'),
                                self.combo_output_folder,
                                self.btn_add_output_folder,
                                self.btn_remove_output_folder,
                            ],
                            [
                                None,
                                (self.label_help_output_folder, dict(span=[1, -1])),
                            ],
                            [
                                None,
                                HLayout(
                                    [
                                        Label('Selected output folder path:', word_wrap=False),
                                        self.label_output_folder_path,
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

        ManageOutputFolders.watch_output_folder_change(self._on_active_output_folder_change)
        self._set_combo_current_index_to_active_output_folder()
        # self._load_values_from_config()

    def _set_combo_current_index_to_active_output_folder(self):
        output_folder_name = FindOutputFolder.get_active_output_folder_name()
        try:
            self.combo_output_folder.set_index_from_text(output_folder_name)
            self._update_output_folder_path_label()
        except ValueError:
            pass

    def _update_output_folder_path_label(self):
        output_folder = FindOutputFolder.get_active_output_folder()
        if output_folder:
            self.label_output_folder_path.setText(str(output_folder.abspath()))
            self.label_output_folder_path.set_text_color('blue')
        else:
            self.label_output_folder_path.set_text_color('black')
            self.label_output_folder_path.setText('')

    def _load_values_from_config(self):
        if Config().last_miz_file_in_manual_mode:
            self.le_path_to_miz.setText(Config().last_miz_file_in_manual_mode)
            self._update_output_folder_path_label()

    def _on_combo_output_folder_activated(self):
        if self.selected_output_folder_name:
            ManageOutputFolders.change_active_output_folder(self.selected_output_folder_name)
            Config().last_used_output_folder_in_manual_mode = self.selected_output_folder_name
            self._update_output_folder_path_label()

    @property
    def path_to_miz(self) -> str:
        return str(Path(self.le_path_to_miz.text()).abspath())

    @property
    def path_to_output_folder(self):
        output_folder = FindOutputFolder.get_by_name(self.selected_output_folder_name)
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
        dialog = DialogEditOutputFolder(parent=self)
        dialog.exec()

    def _on_btn_remove_output_folder_clicked(self):
        if self.selected_output_folder_name:
            ManageOutputFolders.remove_output_folder(self.selected_output_folder_name)

    def _on_output_folder_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(self.path_to_output_folder)

    def _on_active_output_folder_change(self):
        self._update_output_folder_path_label()
        self._set_combo_current_index_to_active_output_folder()

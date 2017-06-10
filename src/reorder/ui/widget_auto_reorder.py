# coding=utf-8

from src.cfg import Config
from src.reorder.service import BrowseForFiles, ManageProfiles

from src.reorder.ui.dialog_profile_editor import DialogProfileEditor
from src.reorder.value.auto_profile_model import AutoProfileModelContainer
from src.reorder.value import OutputFoldersModelContainer, AutoProfileModelContainer, ReorderProfile
from src.ui.base import VLayout, Label, Widget, PushButton, HLayout, GridLayout, Combo, HSpacer
from src.utils import Path, make_logger

logger = make_logger(__name__)


class WidgetAutoReorder(Widget):
    def __init__(self, parent=None):
        Widget.__init__(self, parent)

        self.help_label = Label(
            text='Auto-reordering works by comparing your local work with what\'s available online.\n\n'
                 'This relies on your MIZ file content being hosted on Github, while the MIz file itself '
                 'is build on Appveyor. To setup the auto-reordering mode, you\'ll need to provide URLs to '
                 'your Github repository and to your Appveyor repository.\n\n'
        )

        self.combo_profile = Combo(
            self._on_combo_profile_activated,
            parent=self,
            model=AutoProfileModelContainer().model
        )

        self.btn_add_profile = PushButton(
            text='Add',
            func=self._on_btn_add_profile_clicked
        )

        self.btn_remove_profile = PushButton(
            text='Remove',
            func=self._on_btn_remove_profile_clicked
        )

        self.label_profile_src_path = PushButton('', self._on_src_folder_clicked)
        self.label_profile_src_path.setFlat(True)

        self.label_profile_output_path = PushButton('', self._on_output_folder_clicked)
        self.label_profile_output_path.setFlat(True)

        self.label_profile_gh_repo = PushButton('', self._on_gh_repo_clicked)
        self.label_profile_gh_repo.setFlat(True)

        self.label_profile_av_repo = PushButton('', self._on_av_repo_clicked)
        self.label_profile_av_repo.setFlat(True)

        self.setLayout(
            VLayout(
                [
                    self.help_label,
                    GridLayout(
                        [
                            [
                                Label('Profile'),
                                self.combo_profile,
                                self.btn_add_profile,
                                self.btn_remove_profile,
                            ],
                            [
                                None,
                                GridLayout(
                                    [
                                        [
                                            Label('Selected profile source folder:', word_wrap=False),
                                            (self.label_profile_src_path, dict(align='l')),
                                            HSpacer(),
                                        ],
                                        [
                                            Label('Selected profile output folder:', word_wrap=False),
                                            (self.label_profile_output_path, dict(align='l')),
                                            HSpacer(),
                                        ],
                                        [
                                            Label('Selected profile Github repo:', word_wrap=False),
                                            (self.label_profile_gh_repo, dict(align='l')),
                                            HSpacer(),
                                        ],
                                        [
                                            Label('Selected profile Appveyor repo:', word_wrap=False),
                                            (self.label_profile_av_repo, dict(align='l')),
                                            HSpacer(),
                                        ]
                                    ],
                                    auto_right=False,
                                    stretch=[0, 0, 4],
                                ),
                            ],
                        ],
                    ),
                ],
                add_stretch=True
            ),
        )

        self._load_values_from_config()

    def _load_values_from_config(self):
        if Config().last_used_auto_profile:
            self.combo_profile.set_index_from_text(Config().last_used_auto_profile)
            self._update_labels()

    def _update_labels(self):
        params = [
            (self.label_profile_src_path, 'src_folder'),
            (self.label_profile_output_path, 'output_folder'),
            (self.label_profile_gh_repo, 'gh_repo'),
            (self.label_profile_av_repo, 'av_repo'),
        ]
        if self.active_profile:
            for label, attrib in params:
                label.setText(getattr(self.active_profile, attrib))
                label.set_text_color('blue')
        else:
            for label, _ in params:
                label.setText('No profile selected')
                label.set_text_color('black')

    @property
    def selected_profile_name(self):
        return self.combo_profile.currentText()

    @property
    def active_profile(self) -> ReorderProfile:
        if self.selected_profile_name:
            return ManageProfiles.get_by_name(self.selected_profile_name)

    def _on_src_folder_clicked(self):
        if self.active_profile:
            BrowseForFiles.show_file_or_folder_in_explorer(self.active_profile.src_folder)

    def _on_output_folder_clicked(self):
        if self.active_profile:
            BrowseForFiles.show_file_or_folder_in_explorer(self.active_profile.output_folder)

    def _on_gh_repo_clicked(self):
        if self.active_profile:
            BrowseForFiles.show_file_or_folder_in_explorer(self.active_profile.gh_repo)

    def _on_av_repo_clicked(self):
        if self.active_profile:
            BrowseForFiles.show_file_or_folder_in_explorer(self.active_profile.av_repo)

    def _on_btn_add_profile_clicked(self):
        dialog = DialogProfileEditor(self)
        dialog.exec()

    def _on_btn_remove_profile_clicked(self):
        if self.selected_profile_name:
            ManageProfiles.remove_output_folder(self.selected_profile_name)

    def _on_combo_profile_activated(self):
        if self.selected_profile_name:
            Config().last_used_auto_profile = self.selected_profile_name
            self._update_labels()

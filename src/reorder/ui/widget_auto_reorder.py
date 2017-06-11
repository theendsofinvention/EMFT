# coding=utf-8

from src.reorder.service import BrowseForFiles, ManageProfiles, ManageBranches, RemoteVersions
from src.reorder.ui.dialog_profile_editor import DialogProfileEditor
from src.reorder.value import AutoProfileModelContainer, BranchesModelContainer
from src.reorder.finder import FindProfile
from src.ui.base import VLayout, Label, Widget, PushButton, GridLayout, Combo, HSpacer
from src.utils import make_logger

logger = make_logger(__name__)


class WidgetAutoReorder(Widget):
    def __init__(self, parent=None):
        Widget.__init__(self, parent)

        self._remote_version = None

        self.help_label = Label(
            text='Auto-reordering works by comparing your local work with what\'s available online.\n\n'
                 'This relies on your MIZ file content being hosted on Github, while the MIz file itself '
                 'is build on Appveyor. To setup the auto-reordering mode, you\'ll need to provide URLs to '
                 'your Github repository and to your Appveyor repository.\n\n',
            word_wrap=True,
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

        self.combo_branch = Combo(
            on_change=self._on_combo_branch_activated,
            model=BranchesModelContainer().model
        )

        self.btn_refresh_branches = PushButton(
            text='Refresh',
            func=ManageBranches().refresh_gh_branches
        )

        self.label_latest_remote_version = Label('')

        self.btn_refresh_remote_version = PushButton(
            text='Refresh',
            func=self._refresh_remote_version
        )

        self.label_remote_version_version = Label('')
        self.label_remote_version_branch = Label('')
        self.label_remote_version_size = Label('')
        self.label_remote_version_name = Label('')
        self.label_remote_version_url = Label('')

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
                                    stretch=[0, 0, 4],
                                ),
                            ],
                            [
                                Label('Branch'),
                                self.combo_branch,
                                self.btn_refresh_branches,
                            ],
                            [
                                None,
                                GridLayout(
                                    [
                                        [
                                            Label('Version:'), (self.label_remote_version_version, dict(align='l')),
                                        ],
                                        [
                                            Label('Branch:'), (self.label_remote_version_branch, dict(align='l')),
                                        ],
                                        [
                                            Label('Size:'), (self.label_remote_version_size, dict(align='l')),
                                        ],
                                        [
                                            Label('Filename:'), (self.label_remote_version_name, dict(align='l')),
                                        ],
                                        [
                                            Label('URL:'), (self.label_remote_version_url, dict(align='l')),
                                        ],
                                    ],
                                    stretch=[0, 1]
                                ),
                                self.btn_refresh_remote_version
                            ],
                        ],
                    ),
                ],
                add_stretch=True
            ),
        )

        self._load_values_from_config()

    def _load_values_from_config(self):
        if FindProfile.get_active_profile():
            self.combo_profile.set_index_from_text(FindProfile.get_active_profile().name)
            self._update_profile_labels()
            if ManageBranches.get_active_branch():
                self.combo_branch.set_index_from_text(ManageBranches.get_active_branch().name)

    def _refresh_remote_version(self):
        self._remote_version = RemoteVersions.get_latest_remote_version(self.selected_branch_name)
        self._update_remote_version_labels()

    def _update_remote_version_labels(self):
        if self._remote_version:
            params = [
                ('version', 'version'),
                ('branch', 'branch'),
                ('download_url', 'url'),
                ('remote_file_name', 'name'),
                ('human_file_size', 'size'),
            ]
            for av, own in params:
                getattr(self, f'label_remote_version_{own}').setText(str(getattr(self._remote_version, av)))

    def _update_profile_labels(self):
        params = [
            (self.label_profile_src_path, 'src_folder'),
            (self.label_profile_output_path, 'output_folder'),
            (self.label_profile_gh_repo, 'gh_repo'),
            (self.label_profile_av_repo, 'av_repo'),
        ]
        active_profile = FindProfile().get_active_profile()
        if active_profile:
            for label, attrib in params:
                label.setText(getattr(active_profile, attrib))
                label.set_text_color('blue')
        else:
            for label, _ in params:
                label.setText('No profile selected')
                label.set_text_color('black')

    def _update_branch_combo(self):
        active_branch = ManageBranches.get_active_branch()
        if active_branch:
            self.combo_branch.set_index_from_text(active_branch.name)

    @property
    def selected_profile_name(self):
        return self.combo_profile.currentText()

    @property
    def selected_branch_name(self):
        return self.combo_branch.currentText()

    def _on_combo_profile_activated(self):
        if self.selected_profile_name:
            ManageProfiles.change_active_profile(self.selected_profile_name)
            ManageBranches.refresh_gh_branches()
            self._update_profile_labels()
            self._update_branch_combo()

    def _on_combo_branch_activated(self):
        print(self.selected_branch_name)
        if self.selected_branch_name:
            ManageBranches.change_active_branch(self.selected_branch_name)

    def _on_src_folder_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(FindProfile.get_active_profile().src_folder)

    def _on_output_folder_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(FindProfile.get_active_profile().output_folder)

    def _on_gh_repo_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(FindProfile.get_active_profile().gh_repo)

    def _on_av_repo_clicked(self):
        BrowseForFiles.show_file_or_folder_in_explorer(FindProfile.get_active_profile().av_repo)

    def _on_btn_add_profile_clicked(self):
        dialog = DialogProfileEditor(self)
        dialog.exec()

    def _on_btn_remove_profile_clicked(self):
        if self.selected_profile_name:
            ManageProfiles.remove_profile(self.selected_profile_name)

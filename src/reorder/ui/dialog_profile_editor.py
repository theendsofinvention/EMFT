from src.utils import make_logger

from src.reorder.value.local_profiles import LOCAL_PROFILES
from src.reorder.value.reorder_profile import ReorderProfile
from src.ui.base import Dialog, Label, GridLayout, LineEdit, VSpacer, PushButton, HLayout, BrowseDialog, \
    box_warning

logger = make_logger(__name__)


class DialogProfileEditor(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent=parent)
        self.setMinimumWidth(600)
        self._name_le = LineEdit('', validation_regex='[a-zA-Z0-9]*')
        self._gh_owner_le = LineEdit('')
        self._gh_repo_le = LineEdit('')
        self._av_owner_le = LineEdit('')
        self._av_repo_le = LineEdit('')
        self._src_folder = LineEdit('', read_only=True)
        self._browse_src_folder_btn = PushButton('Browse', self._on_browse_src_folder)
        self._output_folder = LineEdit('', read_only=True)
        self._browse_output_folder_btn = PushButton('Browse', self._on_browse_output_folder)
        self._cancel_btn = PushButton('Cancel', self._on_cancel, self)
        self._save_btn = PushButton('Save', self._on_save, self)
        self._save_btn.setDefault(True)

        self.setLayout(
            GridLayout(
                [
                    [Label('Profile name'), self._name_le],
                    [None, Label('(only letters and numbers)')],
                    [Label('Github repository owner'), self._gh_owner_le],
                    [Label('Github repository name'), self._gh_repo_le],
                    [Label('Appveyor repository owner'), self._av_owner_le],
                    [Label('Appveyor repository name'), self._av_repo_le],
                    [Label('Source folder'), HLayout([self._src_folder, self._browse_src_folder_btn])],
                    [Label('Output folder'), HLayout([self._output_folder, self._browse_output_folder_btn])],
                    [VSpacer(), None],
                    [
                        None,
                        HLayout(
                            [self._cancel_btn, self._save_btn],
                        ),
                    ],
                ],
            ),
        )

    def _on_browse_src_folder(self):
        p = BrowseDialog.get_directory(self, 'Select the source folder')
        if p:
            self._src_folder.setText(p.abspath())

    def _on_browse_output_folder(self):
        p = BrowseDialog.get_directory(self, 'Select the output folder')
        if p:
            self._output_folder.setText(p.abspath())

    def _on_save(self):
        if self.to_profile(self._name_le.text()):
            self.close()

    def _on_cancel(self):
        self.close()

    def _is_valid(self) -> bool:
        if not self._name_le.text():
            box_warning(self, 'Missing information', 'Please give a name to this profile')
        else:
            return True

    def to_profile(self, profile_name):
        if self._is_valid():
            try:
                profile = LOCAL_PROFILES[profile_name]
            except KeyError:
                profile = ReorderProfile(profile_name)
            logger.debug(f'profile is valid, saving to file: {profile.path.abspath()}')
            profile.av_owner = self._av_owner_le.text()
            profile.av_repo = self._av_repo_le.text()
            profile.gh_owner = self._gh_owner_le.text()
            profile.gh_repo = self._gh_repo_le.text()
            profile.src_folder = self._src_folder.text()
            profile.output_folder = self._output_folder.text()
            profile.write()
            return True

    @staticmethod
    def from_profile(profile_name, parent=None) -> 'DialogProfileEditor':
        profile = ReorderProfile(profile_name)
        if not profile.path.exists():
            FileNotFoundError(profile.path)
        dialog = DialogProfileEditor(parent=parent)
        dialog._name_le.setText(profile_name)
        dialog._av_owner_le.setText(profile.av_owner)
        dialog._av_repo_le.setText(profile.av_repo)
        dialog._gh_owner_le.setText(profile.gh_owner)
        dialog._gh_repo_le.setText(profile.gh_repo)
        dialog._src_folder.setText(profile.src_folder)
        dialog._output_folder.setText(profile.output_folder)
        return dialog

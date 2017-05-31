from src.ui.base import Dialog, Label, GridLayout, LineEdit, VSpacer, PushButton, HSpacer, HLayout
from src.reorder.value.reorder_profile import ReorderProfile


class ProfileEditor(Dialog):

    def __init__(self, parent=None):
        Dialog.__init__(self, parent=parent)
        self._name_le = LineEdit('', validation_regex='[a-zA-Z0-9]')
        self._gh_owner_le = LineEdit('')
        self._gh_repo_le = LineEdit('')
        self._av_owner_le = LineEdit('')
        self._av_repo_le = LineEdit('')

        self.setLayout(
            GridLayout(
                [
                    [Label('Name'), self._name_le],
                    [Label('Github repository owner'), self._gh_owner_le],
                    [Label('Github repository name'), self._gh_repo_le],
                    [Label('Appveyor repository owner'), self._av_owner_le],
                    [Label('Appeyor repository name'), self._av_repo_le],
                    [VSpacer(), None],
                    [
                        None,
                        HLayout(
                            [
                                PushButton('Save', self._on_save, self),
                                PushButton('Save', self._on_save, self),
                            ],
                        ),
                    ],
                ],
            ),
        )

    def _on_save(self):
        self.to_profile(self._name_le)
        self.close()

    def _on_cancel(self):
        self.close()

    def _is_valid(self) -> bool:
        return True

    def to_profile(self, profile_name):
        if self._is_valid():
            profile = ReorderProfile(profile_name)
            profile.av_owner = self._av_owner_le.text()
            profile.av_repo = self._av_repo_le.text()
            profile.gh_owner = self._gh_owner_le.text()
            profile.gh_repo = self._gh_repo_le.text()

    @staticmethod
    def from_profile(profile_name, parent=None) -> 'ProfileEditor':
        profile = ReorderProfile(profile_name)
        if not profile.path.exists():
            FileNotFoundError(profile.path)
        dialog = ProfileEditor(parent=parent)
        dialog._name_le.setText(profile_name)
        dialog._av_owner_le.setText(profile.av_owner)
        dialog._av_repo_le.setText(profile.av_repo)
        dialog._gh_owner_le.setText(profile.gh_owner)
        dialog._gh_repo_le.setText(profile.gh_repo)
        dialog.show()
        return dialog

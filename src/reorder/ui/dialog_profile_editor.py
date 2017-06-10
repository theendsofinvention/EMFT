from src.reorder.service import ConvertUrl, ManageProfiles
from src.ui.base import Dialog, Label, GridLayout, LineEdit, VSpacer, PushButton, HLayout, BrowseDialog, \
    box_warning
from src.utils import make_logger, Path

logger = make_logger(__name__)


class DialogProfileEditor(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent=parent)
        self.setMinimumWidth(600)
        self._name_le = LineEdit('', validation_regex='[a-zA-Z0-9]*')
        self._gh_repo_le = LineEdit('')
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
                    [Label('Github repository'), self._gh_repo_le],
                    [Label('Appveyor repository'), self._av_repo_le],
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
        if self.to_profile():
            self.close()

    def _on_cancel(self):
        self.close()

    def _is_valid(self) -> bool:
        if not self._name_le.text():
            box_warning(self, 'Missing information', 'Please give a name to this profile')
            return False
        elif not self._gh_repo_le.text():
            box_warning(self, 'Missing information', 'Please provide a Github repository')
            return False
        elif not self._av_repo_le.text():
            box_warning(self, 'Missing information', 'Please provide a Appveyor repository')
            return False
        elif not self._src_folder.text():
            box_warning(self, 'Missing information', 'Please provide a source folder')
            return False
        elif not self._output_folder.text():
            box_warning(self, 'Missing information', 'Please provide an output folder')
            return False
        else:
            if not Path(self._src_folder.text()).exists():
                box_warning(self, 'Incorrect information', f'The source folder does not exist:\n\n'
                                                           f'{self._src_folder.text()}')
                return False
            if not Path(self._output_folder.text()).exists():
                box_warning(self, 'Incorrect information', f'The output folder does not exist:\n\n'
                                                           f'{self._output_folder.text()}')
                return False
            try:
                ConvertUrl.convert_gh_url(self._gh_repo_le.text())
            except ValueError:
                box_warning(self, 'Incorrect information', 'The Github URL seems incorrect')
                return False
            try:
                ConvertUrl.convert_av_url(self._av_repo_le.text())
            except ValueError:
                box_warning(self, 'Incorrect information', 'The Appveyor URL seems incorrect')
                return False

        return True

    def to_profile(self):
        if self._is_valid():
            ManageProfiles.add_profile_from_values(
                name=self._name_le.text(),
                gh_repo=self._gh_repo_le.text(),
                av_repo=self._av_repo_le.text(),
                src_folder=self._src_folder.text(),
                output_folder=self._output_folder.text()
            )
            return True

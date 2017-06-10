# coding=utf-8


from src.reorder.service.browse_for_files import BrowseForFiles
from src.reorder.service.manage_output_folders import ManageOutputFolders
from src.ui.base import Dialog, LineEdit, Label, PushButton, GridLayout, box_warning


class DialogEditOutputFolder(Dialog):
    def __init__(self, name: str = None, path: str = None, parent=None):
        Dialog.__init__(self, parent)

        self.setWindowTitle('Edit output folder')

        self.label_help = Label(
            text='The output folder is where EMFT will unzip the re-ordered mission files. '
                 'All the content of the MIZ files will end up in that folder.\n\n'
                 'Usually, this will be your SCM folder (ie. your Github repository).',
        )

        self.le_name = LineEdit(
            text=name or '',
            clear_btn_enabled=True,
            validation_regex=r'[a-zA-Z0-9 -_]{0,16}'
        )

        self.le_path = LineEdit(
            text=path or '',
        )
        self.btn_browse_for_output_folder = PushButton(
            text='Browse',
            func=self._on_btn_browse_for_output_folder_clicked
        )

        self.btn_save = PushButton(
            text='Save',
            func=self._on_btn_save_clicked,
            min_height=30,
        )

        self.btn_cancel = PushButton(
            text='Cancel',
            func=self._on_btn_cancel_clicked,
            min_height=30,
        )

        self.setContentsMargins(15, 15, 15, 15)

        self.setLayout(
            GridLayout(
                [
                    [
                        (self.label_help, dict(span=[1, -1])),
                        None,
                        None,
                    ],
                    [
                        Label('Name'),
                        self.le_name,
                        None,
                    ],
                    [
                        Label('Path'),
                        self.le_path,
                        self.btn_browse_for_output_folder,
                    ],
                    [
                        None,
                        self.btn_save,
                        self.btn_cancel,
                    ],
                ],
            ),
        )
        self.setMinimumWidth(600)

    @property
    def name(self) -> str:
        return self.le_name.text()

    @property
    def output_folder_path(self) -> str:
        return self.le_path.text()

    def _on_btn_save_clicked(self):
        if not self.name:
            box_warning(self, 'Oops', 'Please provide a name')
        elif not self.output_folder_path:
            box_warning(self, 'Oops', 'Please provide an output folder')
        else:
            try:
                ManageOutputFolders().add_output_folder(self.name, self.output_folder_path)
            except (FileNotFoundError, FileExistsError, KeyError) as e:
                box_warning(self, 'Oops', ':\n\n'.join(str(e).capitalize().split(': ')))
            else:
                self.close()

    def _on_btn_cancel_clicked(self):
        print('cancel')
        self.close()

    def _on_btn_browse_for_output_folder_clicked(self):
        path = BrowseForFiles.browse_for_output_folder(self)
        if path:
            self.le_path.setText(path.abspath())

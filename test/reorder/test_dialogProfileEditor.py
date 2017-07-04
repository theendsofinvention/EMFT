# coding=utf-8

from unittest import mock

import pytest

from src.reorder.ui import dialog_profile_editor


class TestDialogProfileEditor:

    @pytest.fixture()
    def valid_dialog(self, qtbot):
        dialog = dialog_profile_editor.DialogProfileEditor()
        dialog.show()
        dialog._name_le.setText('name')
        dialog._gh_repo_le.setText(
            'https://github.com/132nd-vWing/132nd-Virtual-Wing-Training-Mission-Tblisi'
        )
        dialog._av_repo_le.setText(
            'https://ci.appveyor.com/project/132nd-etcher/132nd-virtual-wing-training-mission-tblisi'
        )
        dialog._src_folder.setText('.')
        dialog._output_folder.setText('.')
        qtbot.addWidget(dialog)
        yield dialog

    @pytest.fixture()
    def warning_box(self):
        with mock.patch.object(dialog_profile_editor, 'box_warning') as box:
            yield box

    def test_name_validation(
            self,
            warning_box,
            valid_dialog: dialog_profile_editor.DialogProfileEditor,
            qtbot
    ):
        valid_dialog._name_le.setText('')
        assert not valid_dialog._is_valid()
        warning_box.assert_called_once_with(
            valid_dialog,
            'Oops',
            'Please give a name to this profile'
        )
        warning_box.reset_mock()
        qtbot.keyClicks(valid_dialog._name_le, 'name')
        assert valid_dialog._is_valid()

    def test_src_folder(
            self,
            warning_box,
            valid_dialog: dialog_profile_editor.DialogProfileEditor,
    ):
        valid_dialog._src_folder.setText('')
        assert not valid_dialog._is_valid()
        warning_box.assert_called_once_with(
            valid_dialog,
            'Oops',
            'Please provide a source folder'
        )
        warning_box.reset_mock()
        valid_dialog._src_folder.setText('some folder')
        assert not valid_dialog._is_valid()
        warning_box.assert_called_once_with(
            valid_dialog,
            'Oops',
            'The source folder does not exist:\n\nsome folder'
        )
        warning_box.reset_mock()
        valid_dialog._src_folder.setText('.')
        assert valid_dialog._is_valid()
        warning_box.assert_not_called()

    def test_output_folder(
            self,
            warning_box,
            valid_dialog: dialog_profile_editor.DialogProfileEditor,
    ):
        valid_dialog._output_folder.setText('')
        assert not valid_dialog._is_valid()
        warning_box.assert_called_once_with(
            valid_dialog,
            'Oops',
            'Please provide an output folder'
        )
        warning_box.reset_mock()
        valid_dialog._output_folder.setText('some folder')
        assert not valid_dialog._is_valid()
        warning_box.assert_called_once_with(
            valid_dialog,
            'Oops',
            'The output folder does not exist:\n\nsome folder'
        )
        warning_box.reset_mock()
        valid_dialog._output_folder.setText('.')
        assert valid_dialog._is_valid()
        warning_box.assert_not_called()

    def test_gh_repo(
            self,
            warning_box,
            valid_dialog: dialog_profile_editor.DialogProfileEditor,
    ):
        def assert_wrong():
            assert not valid_dialog._is_valid()
            warning_box.assert_called_once_with(
                valid_dialog,
                'Incorrect information',
                'The Github URL seems incorrect'
            )
            warning_box.reset_mock()

        valid_dialog._gh_repo_le.setText('.')
        assert_wrong()
        valid_dialog._gh_repo_le.setText('some text')
        assert_wrong()
        valid_dialog._gh_repo_le.setText('https://github.com/132nd-etcher/EMFT.git')
        assert valid_dialog._is_valid()

    def test_av_repo(
            self,
            warning_box,
            valid_dialog: dialog_profile_editor.DialogProfileEditor,
    ):
        def assert_wrong():
            assert not valid_dialog._is_valid()
            warning_box.assert_called_once_with(
                valid_dialog,
                'Incorrect information',
                'The Appveyor URL seems incorrect'
            )
            warning_box.reset_mock()

        valid_dialog._av_repo_le.setText('.')
        assert_wrong()
        valid_dialog._av_repo_le.setText('some text')
        assert_wrong()
        valid_dialog._av_repo_le.setText('https://ci.appveyor.com/project/132nd-etcher/emft/build/artifacts')
        assert valid_dialog._is_valid()

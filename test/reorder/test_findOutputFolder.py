import os

import pytest

from src.reorder.finder import FindOutputFolder
from src.reorder.service import ManageOutputFolders


# coding=utf-8
class TestFindOutputFolder:
    def test_get_active_output_folder(self):
        assert FindOutputFolder.get_active_output_folder() is None
        assert FindOutputFolder.get_active_output_folder_name() is None
        ManageOutputFolders.add_output_folder('test', '.')
        assert FindOutputFolder.get_active_output_folder() == os.path.abspath('.')
        assert FindOutputFolder.get_active_output_folder_name() == 'test'
        os.makedirs('./test')
        ManageOutputFolders.add_output_folder('test2', './test')
        assert FindOutputFolder.get_active_output_folder() == os.path.abspath('./test')
        assert FindOutputFolder.get_active_output_folder_name() == 'test2'
        ManageOutputFolders.remove_output_folder('test2')
        assert FindOutputFolder.get_active_output_folder() == os.path.abspath('.')
        assert FindOutputFolder.get_active_output_folder_name() == 'test'
        ManageOutputFolders.remove_output_folder('test')
        assert FindOutputFolder.get_active_output_folder() is None
        assert FindOutputFolder.get_active_output_folder_name() is None

    def test_get_by_name(self):
        with pytest.raises(ValueError):
            FindOutputFolder.get_by_name('test')
        ManageOutputFolders.add_output_folder('test', '.')
        output_folder = FindOutputFolder.get_by_name('test')
        assert output_folder.abspath() == os.path.abspath('.')

    def test_get_name_from_output_folder(self):
        ManageOutputFolders.add_output_folder('test', '.')
        output_folder = FindOutputFolder.get_by_name('test')
        name = FindOutputFolder.get_name_from_output_folder(output_folder)
        assert name == 'test'

    def test_get_by_path(self):
        with pytest.raises(FileNotFoundError):
            FindOutputFolder.get_by_path('.')
        ManageOutputFolders.add_output_folder('test', '.')
        output_folder = FindOutputFolder.get_by_path('.')
        assert output_folder.abspath() == os.path.abspath('.')

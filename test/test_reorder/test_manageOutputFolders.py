import os

import pytest

from src.reorder.finder import FindOutputFolder
from src.reorder.service.manage_output_folders import ManageOutputFolders
from src.reorder.value import OutputFolder


# coding=utf-8
# noinspection PyUnusedLocal
class TestManageOutputFolders:
    manager = ManageOutputFolders()

    def test_add_output_folder(self, cleandir):
        os.makedirs('./some_path')
        self.manager.add_output_folder('name', './some_path')
        os.makedirs('./some_other_path')
        self.manager.add_output_folder('other_name', './some_other_path')
        f1 = FindOutputFolder.get_by_path('./some_other_path')
        f2 = FindOutputFolder.get_by_path('./some_path')
        f3 = FindOutputFolder.get_by_name('other_name')
        f4 = FindOutputFolder.get_by_name('name')
        for f in {f1, f2, f3, f4}:
            assert isinstance(f, OutputFolder)
        assert f1 is f3
        assert f2 is f4

    def test_path_not_found(self, cleandir):
        with pytest.raises(FileNotFoundError):
            self.manager.add_output_folder('path_not_found', './path_not_found')

    def test_name_exists(self, cleandir):
        os.makedirs('./test_name_exists')
        self.manager.add_output_folder('test_name_exists', './test_name_exists')
        with pytest.raises(FileExistsError):
            self.manager.add_output_folder('test_name_exists', './test_name_exists')

    def test_path_exists(self, cleandir):
        os.makedirs('./test_path_exists')
        self.manager.add_output_folder('test_path_exists', './test_path_exists')
        with pytest.raises(FileExistsError):
            self.manager.add_output_folder('test_path_exists_other_name', './test_path_exists')

    def test_path_does_not_exist(self, cleandir):
        with pytest.raises(FileNotFoundError):
            FindOutputFolder.get_by_path('./some_fancy_path')

import pytest
import os
from src.utils import Path
from src.reorder.service.manage_output_folders import ManageOutputFolders
from src.reorder.value import OutputFolder


# coding=utf-8
class TestManageOutputFolders:

    def test_add_output_folder(self, cleandir):
        manager = ManageOutputFolders()
        with pytest.raises(FileNotFoundError):
            manager.add_output_folder('name', './some_path')
        os.makedirs('./some_path')
        manager.add_output_folder('name', './some_path')
        with pytest.raises(FileExistsError):
            manager.add_output_folder('name', './some_path')
        with pytest.raises(FileExistsError):
            manager.add_output_folder('other_name', './some_path')
        with pytest.raises(FileNotFoundError):
            manager.get_by_path('./some_fancy_path')
        os.makedirs('./some_other_path')
        manager.add_output_folder('other_name', './some_other_path')
        f1 = manager.get_by_path('./some_other_path')
        f2 = manager.get_by_path('./some_path')
        f3 = manager.get_by_name('other_name')
        f4 = manager.get_by_name('name')
        for f in {f1, f2, f3, f4}:
            assert isinstance(f, OutputFolder)
        assert f1 is f3
        assert f2 is f4

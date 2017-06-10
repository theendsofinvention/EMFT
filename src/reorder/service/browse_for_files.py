# coding=utf-8
import os
from src.cfg import Config
from src.ui.base import BrowseDialog
from src.utils import Path


class BrowseForFiles:

    @staticmethod
    def browse_for_miz(parent=None) -> Path:
        init_dir = Config().last_browse_miz_dirname or '.'
        result = BrowseDialog.get_existing_file(
            parent=parent,
            title='Select MIZ file',
            filter_=['*.miz'],
            init_dir=init_dir,
        )
        if result:
            Config().last_browse_miz_dirname = str(result.dirname())
        return result

    @staticmethod
    def show_file_or_folder_in_explorer(path: Path or str):
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(str(path.abspath()))
        if path.isdir():
            os.startfile(str(path.abspath()))
        elif path.isfile():
            os.startfile(str(path.dirname().abspath()))

    @staticmethod
    def browse_for_output_folder(parent=None):
        init_dir = Config().last_browse_output_folder_dirname or '.'
        result = BrowseDialog.get_directory(
            parent=parent,
            title='Select the output folder',
            init_dir=init_dir,
        )
        if result:
            Config().last_browse_output_folder_dirname = str(result.dirname())
        return result

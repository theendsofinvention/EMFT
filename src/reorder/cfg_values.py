from src.utils import Path

from src.meta import MetaPropertyWithDefault, MetaGUIDPropertyWithDefault


class ReorderConfigValues:
    # noinspection PyPep8Naming
    @MetaPropertyWithDefault('All', str)
    def reorder_selected_auto_branch(self, value: str):
        return value

    @MetaPropertyWithDefault(False, bool)
    def auto_mode(self, value: bool):
        return value

    @MetaPropertyWithDefault(True, bool)
    def skip_options_file(self, value: bool):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def single_miz_last(self, value: str):
        if value:
            p = Path(value)
            if not p.exists():
                return None
            elif not p.isfile():
                return None
            elif not p.ext == '.miz':
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def auto_output_folder(self, value: str):
        if value:
            p = Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def single_miz_output_folder(self, value: str):
        if value:
            p = Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, str)
    def auto_source_folder(self, value: str):
        if value:
            p = Path(value)
            if not p.exists():
                return None
            elif not p.isdir():
                return None
            return str(p.abspath())

    @MetaGUIDPropertyWithDefault(None, dict)
    def output_folders(self, value: dict):
        return value

    @MetaGUIDPropertyWithDefault(None, dict)
    def reorder_auto_profiles(self, value: dict):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def last_used_output_folder_in_manual_mode(self, value: str):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def last_used_output_folder_in_auto_mode(self, value: str):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def last_browse_miz_dirname(self, value: str):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def last_browse_output_folder_dirname(self, value: str):
        return value

    @MetaGUIDPropertyWithDefault(None, str)
    def last_miz_file_in_manual_mode(self, value: str):
        return value

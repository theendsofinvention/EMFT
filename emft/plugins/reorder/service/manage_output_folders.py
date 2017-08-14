# coding=utf-8

from emft.config import Config
from emft.core.logging import make_logger
from emft.core.path import Path
from emft.plugins.reorder.finder import FindOutputFolder
from emft.plugins.reorder.value import OutputFolder, OutputFolders, OutputFoldersModelContainer

LOGGER = make_logger(__name__)


class ManageOutputFolders:
    _WATCHERS = []

    @staticmethod
    def watch_output_folder_change(func: callable):
        ManageOutputFolders._WATCHERS.append(func)

    @staticmethod
    def notify_watchers():
        for func in ManageOutputFolders._WATCHERS:
            func()

    @staticmethod
    def _set_combo_model():
        LOGGER.debug('resetting combo model')
        model = OutputFoldersModelContainer().model
        model.beginResetModel()
        model.clear()
        for output_folder_name in sorted(OutputFolders().keys()):
            LOGGER.debug(f'adding folder {output_folder_name}')
            model.appendRow(output_folder_name)
        model.endResetModel()

    @staticmethod
    def write_output_folders_to_config():
        Config().output_folders = {k: str(v.abspath()) for k, v in OutputFolders().data.items()}
        if FindOutputFolder.get_active_output_folder_name():
            Config().last_used_output_folder_in_manual_mode = FindOutputFolder.get_active_output_folder_name()

    @staticmethod
    def read_output_folders_from_config():
        if Config().output_folders:
            OutputFolders(init_dict={k: OutputFolder(v) for k, v in Config().output_folders.items()})
            ManageOutputFolders._set_combo_model()
        if Config().last_used_output_folder_in_manual_mode:
            ManageOutputFolders.change_active_output_folder(Config().last_used_output_folder_in_manual_mode)

    @staticmethod
    def add_output_folder(name: str, path: Path or str) -> bool:
        if isinstance(path, str):
            path = Path(path)
        if name in OutputFolders():
            raise FileExistsError(f'an output folder is already registered with that name: {name}')
        if not path.exists():
            raise FileNotFoundError(f'the output folder path does not exist: {path.abspath()}')
        try:
            FindOutputFolder.get_by_path(path)
        except FileNotFoundError:
            # All is fine, the path is not registered yet
            LOGGER.debug(f'adding output folder: {name} - "{path.abspath()}"')
            output_folder = OutputFolder(path.abspath())
            OutputFolders()[name] = output_folder
            ManageOutputFolders._set_combo_model()
            ManageOutputFolders.change_active_output_folder(name)
        else:
            raise FileExistsError(f'another output folder is already registered with the path: {path.abspath()}')
        return True

    @staticmethod
    def get_by_name(name: str):
        if name not in OutputFolders():
            raise KeyError(f'output folder not registered: {name}')
        return OutputFolders()[name]

    @staticmethod
    def get_by_path(path: Path or str):
        if isinstance(path, str):
            path = Path(path)
        for output_folder in OutputFolders().values():
            if output_folder.abspath() == path.abspath():
                return output_folder
        raise FileNotFoundError(f'no output folder registered with path: {path.abspath()}')

    @staticmethod
    def remove_output_folder(name: str):
        if name not in OutputFolders():
            raise KeyError(f'output folder not registered: {name}')
        del OutputFolders()[name]
        ManageOutputFolders._set_combo_model()
        ManageOutputFolders.write_output_folders_to_config()
        if OutputFolders().keys():
            ManageOutputFolders.change_active_output_folder(list(OutputFolders().keys())[0])
        else:
            OutputFolders.ACTIVE_OUTPUT_FOLDER = None
            OutputFolders.ACTIVE_OUTPUT_FOLDER_NAME = None
        ManageOutputFolders.notify_watchers()

    @staticmethod
    def change_active_output_folder(name: str):
        try:
            output_folder = FindOutputFolder().get_by_name(name)
        except ValueError:
            LOGGER.exception(f'output folder not found: {name}')
        else:
            OutputFolders.ACTIVE_OUTPUT_FOLDER = output_folder
            OutputFolders.ACTIVE_OUTPUT_FOLDER_NAME = name
            ManageOutputFolders.write_output_folders_to_config()
            ManageOutputFolders.notify_watchers()
            LOGGER.debug(f'output folder has changed to {name}')

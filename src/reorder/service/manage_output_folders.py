# coding=utf-8

from src.cfg import Config
from src.reorder.value import OutputFolder, OutputFolders, OutputFoldersModelContainer
from src.utils import Path, make_logger

logger = make_logger(__name__)


class ManageOutputFolders:
    @staticmethod
    def _set_combo_model():
        logger.debug('resetting combo model')
        model = OutputFoldersModelContainer().model
        model.beginResetModel()
        model.clear()
        for output_folder_name in OutputFolders().keys():
            logger.debug(f'adding folder {output_folder_name}')
            model.appendRow(output_folder_name)
        model.endResetModel()

    @staticmethod
    def write_output_folders_to_config():
        Config().output_folders = {k: str(v.abspath()) for k, v in OutputFolders().data.items()}

    @staticmethod
    def read_output_folders_from_config():
        if Config().output_folders:
            OutputFolders(init_dict={k: OutputFolder(v) for k, v in Config().output_folders.items()})
            ManageOutputFolders._set_combo_model()

    @staticmethod
    def add_output_folder(name: str, path: Path or str) -> bool:
        if isinstance(path, str):
            path = Path(path)
        if name in OutputFolders():
            raise FileExistsError(f'an output folder is already registered with that name: {name}')
        if not path.exists():
            raise FileNotFoundError(f'the output folder path does not exist: {path.abspath()}')
        try:
            ManageOutputFolders.get_by_path(path)
        except FileNotFoundError:
            # All is fine, the path is not registered yet
            logger.debug(f'adding output folder: {name} - "{path.abspath()}"')
            output_folder = OutputFolder(path.abspath())
            OutputFolders()[name] = output_folder
            ManageOutputFolders._set_combo_model()
            ManageOutputFolders.write_output_folders_to_config()
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

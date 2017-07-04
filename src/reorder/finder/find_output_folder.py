# coding=utf-8


from src.reorder.value import OutputFolder, OutputFolders
from src.utils import Path


class FindOutputFolder:
    @staticmethod
    def get_active_output_folder() -> OutputFolder:
        return OutputFolders.ACTIVE_OUTPUT_FOLDER

    @staticmethod
    def get_active_output_folder_name() -> str:
        return OutputFolders.ACTIVE_OUTPUT_FOLDER_NAME

    @staticmethod
    def get_by_name(output_folder_name: str) -> OutputFolder:
        try:
            return OutputFolders()[output_folder_name]
        except KeyError:
            raise ValueError(f'no output folder named: {output_folder_name}')

    @staticmethod
    def get_name_from_output_folder(output_folder: OutputFolder):
        for name, output_folder_ in OutputFolders().items():
            if output_folder_ == output_folder:
                return name
        raise FileNotFoundError(output_folder.abspath())

    @staticmethod
    def get_by_path(path: Path or str):
        if isinstance(path, str):
            path = Path(path)
        for output_folder in OutputFolders().values():
            if output_folder.abspath() == path.abspath():
                return output_folder
        raise FileNotFoundError(f'no output folder registered with path: {path.abspath()}')

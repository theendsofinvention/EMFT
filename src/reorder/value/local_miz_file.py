from src.utils import Path


class LocalMizFile(Path):

    def __init__(self, path_str: str):
        Path.__init__(self, path_str)

    def is_valid(self):
        if not self.exists():
            raise FileNotFoundError(self.abspath())
        if not self.isfile():
            raise TypeError(self.abspath())
        if not self.ext == '.miz':
            raise ValueError(self.abspath())
        return True
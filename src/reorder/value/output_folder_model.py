# coding=utf-8

from PyQt5.QtGui import QStandardItemModel, QStandardItem

from src.utils import Singleton


class OutputFoldersModelContainer(metaclass=Singleton):
    def __init__(self, parent=None):
        self._model = OutputFoldersModel(parent)

    @property
    def model(self) -> QStandardItemModel:
        return self._model


class OutputFoldersModel(QStandardItemModel):
    def __init__(self, parent=None):
        QStandardItemModel.__init__(self, parent)

    def appendRow(self, output_folder_name: str):  # noqa: N802
        item = QStandardItem(output_folder_name)
        super(OutputFoldersModel, self).appendRow(item)

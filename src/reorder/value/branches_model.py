# coding=utf-8

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from src.utils import Singleton


class BranchesModelContainer(metaclass=Singleton):
    def __init__(self, parent=None):
        self._model = BranchesModel(parent)

    @property
    def model(self) -> QStandardItemModel:
        return self._model


class BranchesModel(QStandardItemModel):
    def __init__(self, parent=None):
        QStandardItemModel.__init__(self, parent)

    def appendRow(self, branch_name: str):
        item = QStandardItem(branch_name)
        super(BranchesModel, self).appendRow(item)
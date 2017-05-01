# coding=utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QProgressDialog


class MainUiProgress:
    """"""

    progress = None

    @staticmethod
    def progress_start(title: str = '', length: int = 100, label: str = ''):
        MainUiProgress.progress = QProgressDialog()
        MainUiProgress.progress.setWindowFlags(Qt.FramelessWindowHint)
        MainUiProgress.progress.setWindowFlags(Qt.WindowTitleHint)
        MainUiProgress.progress.setMinimumWidth(400)
        from PyQt5.QtWidgets import QPushButton
        # QString() seems to be deprecated in v5
        # PyQt does not support setCancelButton(0) as it expects a QPushButton instance
        # Get your shit together, Qt !
        MainUiProgress.progress.findChild(QPushButton).hide()
        MainUiProgress.progress.setMinimumDuration(1)
        MainUiProgress.progress.setWindowModality(Qt.ApplicationModal)
        MainUiProgress.progress.setCancelButtonText('')
        MainUiProgress.progress.setWindowIcon(QIcon(':/ico/app.ico'))
        MainUiProgress.progress.setWindowTitle(title)
        MainUiProgress.progress.setLabelText(label)
        MainUiProgress.progress.setMaximum(length)
        MainUiProgress.progress.show()

    @staticmethod
    def progress_set_value(value: int):
        if MainUiProgress.progress:
            MainUiProgress.progress.setValue(value)

    @staticmethod
    def progress_set_label(value: str):
        if MainUiProgress.progress:
            MainUiProgress.progress.setLabelText(value)

    @staticmethod
    def progress_done():
        if MainUiProgress.progress:
            MainUiProgress.progress.setValue(MainUiProgress.progress.maximum())
            MainUiProgress.progress = None

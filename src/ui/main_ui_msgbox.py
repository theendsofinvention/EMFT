# coding=utf-8
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QPushButton

from src.global_ import APP_SHORT_NAME, DEFAULT_ICON

from .main_ui_msgbox_adapter import MainUiMsgBoxAdapter


class MainUiMsgBox(MainUiMsgBoxAdapter):

    def _run_box(
            self,
            text: str,
            title: str,
            ico: str,
            is_question=False,
            follow_up_on_yes: callable = None,
            follow_up_on_no: callable = None,
    ):

        msgbox = QMessageBox()

        if title is None:
            title = APP_SHORT_NAME

        if ico is None:
            ico = DEFAULT_ICON

        msgbox.setWindowIcon(QIcon(ico))
        msgbox.setText(text)
        msgbox.setWindowTitle(title)

        if is_question:
            msgbox.addButton(QMessageBox.Yes)
            msgbox.addButton(QMessageBox.No)

        else:
            msgbox.addButton(QPushButton('Ok'), QMessageBox.YesRole)

        if is_question:

            if msgbox.exec() == QMessageBox.Yes:
                if follow_up_on_yes:
                    follow_up_on_yes()

            else:
                if follow_up_on_no:
                    follow_up_on_no()

        else:

            msgbox.exec()
            if follow_up_on_yes:
                follow_up_on_yes()

    def msg(self, text: str, follow_up: callable = None, title: str = None, ico: str = None):
        self._run_box(text=text, follow_up_on_yes=follow_up, title=title, ico=ico)

    def error(self, text: str, follow_up: callable = None, title: str = None, ico: str = None):
        self._run_box(text=text, follow_up_on_yes=follow_up, title=title, ico=ico)

    def confirm(
            self,
            text: str,
            title: str = None,
            ico: str = None,
            follow_up_on_yes: callable = None,
            follow_up_on_no: callable = None
    ):

        if title is None:
            title = 'Please confirm'

        self._run_box(
            text=text,
            follow_up_on_yes=follow_up_on_yes,
            title=title,
            ico=ico,
            follow_up_on_no=follow_up_on_no,
            is_question=True)
# coding=utf-8
import abc


class MainUiMsgBoxAdapter:
    @abc.abstractmethod
    def msg(self, text: str, follow_up: callable = None, title: str = None):
        pass

    @abc.abstractmethod
    def error(self, text: str, follow_up: callable = None, title: str = None):
        pass

    @abc.abstractmethod
    def confirm(self, text: str, follow_up: callable, title: str = None, follow_up_on_no: callable = None):
        pass
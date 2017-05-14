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
    def confirm(
            self,
            text: str,
            title: str = None,
            ico: str = None,
            follow_up_on_yes: callable = None,
            follow_up_on_no: callable = None
    ):
        pass

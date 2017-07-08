# coding=utf-8

import pytest
from hypothesis import given
from hypothesis.strategies import text, integers

from src.utils import Progress, ProgressAdapter

not_a_string = [int(0), None, True, float(3.5)]
not_an_int = ['text', None]  # not including bool because it's an instance of int


class TestProgressAdapter(ProgressAdapter):
    @staticmethod
    def progress_set_label(value: str):
        pass

    @staticmethod
    def progress_done():
        pass

    @staticmethod
    def progress_set_value(value: int):
        pass

    @staticmethod
    def progress_start(title: str, length: int = 100, label: str = ''):
        pass


class TestProgress:
    @pytest.fixture(autouse=True)
    def reset_progress(self):
        Progress.done()

    def set_correct(self, value, func):
        getattr(Progress, func)(value)

    def set_wrong(self, value, func):
        with pytest.raises(TypeError):
            getattr(Progress, func)(value)

    def set_both(self, func, correct_value, wrong_value):
        self.set_correct(correct_value, func)
        self.set_wrong(wrong_value, func)

    def test_start(self):
        Progress.start(title='title')
        assert Progress.title == 'title'
        assert Progress.label == ''
        assert Progress.length == 100
        assert Progress.value == 0

    def test_double_start(self):
        Progress.start('test')
        with pytest.raises(RuntimeError):
            Progress.start('test')

    def test_is_started(self):
        Progress.start('test')
        assert Progress.length == 100
        assert Progress.started
        Progress.set_value(50)
        assert Progress.started
        assert Progress.value == 50
        Progress.set_value(100)
        assert not Progress.started

    @pytest.mark.parametrize('wrong_value', not_a_string)
    @given(correct_value=text())
    def test_label(self, correct_value, wrong_value):
        self.set_both('set_label', correct_value, wrong_value)

    @pytest.mark.parametrize('wrong_value', not_a_string)
    @given(correct_value=text())
    def test_title(self, correct_value, wrong_value):
        self.set_both('set_title', correct_value, wrong_value)

    @pytest.mark.parametrize('wrong_value', not_an_int)
    @given(correct_value=integers(min_value=0, max_value=100))
    def test_value(self, correct_value, wrong_value):
        self.set_both('set_value', correct_value, wrong_value)
        with pytest.raises(ValueError):
            Progress.set_value(Progress.length + 1)

    @pytest.mark.parametrize('wrong_value', not_an_int)
    @given(correct_value=integers(min_value=1, max_value=100))
    def test_length(self, correct_value, wrong_value):
        self.set_both('set_length', correct_value, wrong_value)
        with pytest.raises(ValueError):
            Progress.start('test', length=0)

    def test_adapter(self):
        class OtherAdapter(TestProgressAdapter):
            pass

        adapter = TestProgressAdapter
        other_adapter = OtherAdapter
        assert not Progress.adapters
        Progress.register_adapter(adapter)
        assert Progress.has_adapter(adapter)
        assert not Progress.has_adapter(other_adapter)
        Progress.register_adapter(other_adapter)
        assert Progress.has_adapter(other_adapter)

        Progress.unregister_adapter(other_adapter)
        assert not Progress.has_adapter(other_adapter)

        Progress.unregister_adapter(adapter)
        assert not Progress.has_adapter(adapter)

    @pytest.mark.parametrize('adapter', [None, True, 'test', 1])
    def test_wrong_adapter_register(self, adapter):
        with pytest.raises(TypeError):
            Progress.register_adapter(adapter)

    def test_adapter_double_register(self):
        adapter = TestProgressAdapter
        Progress.register_adapter(adapter)
        Progress.register_adapter(adapter)

# coding=utf-8

import time

import pytest
from hypothesis import strategies as st, given, example

from src.utils.threadpool import ThreadPool


def sleep(t=0.1):
    time.sleep(t)


def test_join():
    p = ThreadPool(1, 'test', False)
    p.queue_task(sleep)
    p.join_all()


def test_force_join():
    start = time.time()
    p = ThreadPool(1, 'test', False)
    p.queue_task(sleep, [10])
    p.join_all(False, False)
    assert time.time() - start < 2


def test_decrease_pool_size():
    p = ThreadPool(10)
    p.set_thread_count(0)


@given(x=st.one_of(st.booleans(), st.text(), st.none(), st.integers(), st.floats()))
@example(x=None)
def test_queue_wrong_task_type(x):
    p = ThreadPool(1, 'test', True)
    with pytest.raises(ValueError):
        p.queue_task(x)
    p.join_all(False, False)


def test_queue_task():
    p = ThreadPool(10, 'test', True)

    def some_func():
        return True

    for _ in range(100):
        assert p.queue_task(some_func)
    p.join_all()
    time.sleep(0.1)
    assert p.all_done()

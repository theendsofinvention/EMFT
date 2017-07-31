# coding=utf-8
"""
Creates a pool of threads that accepts any function, with or without arguments.

Workers can be linked together
"""
import threading
import time
import traceback

from src.utils.custom_logging import make_logger

# ----------------------------------------------
# Pre-Sentry
# ----------------------------------------------
# from src.utils.crash_reporter import send_crash_report
# ----------------------------------------------

LOGGER = make_logger(__name__)

SENTRY = None
test_exc = None


def register_sentry(sentry_client_instance):
    global SENTRY
    SENTRY = sentry_client_instance


class ThreadPool:
    """Flexible thread pool class.  Creates a pool of threads, then
    accepts tasks that will be dispatched to the next available
    thread."""

    def __init__(self, _num_threads, _basename=None, _daemon=None):

        """Initialize the thread pool with numThreads workers."""
        self.resize_lock = threading.Condition(threading.Lock())
        self.tasks = []
        self.basename_suffix = 1
        self.is_daemon = _daemon
        self.threads = []
        self.ongoing_jobs = 0
        self.is_joining = False
        self.basename = _basename
        self.task_lock = threading.Condition(threading.Lock())
        self.set_thread_count(_num_threads)

    def set_thread_count(self, new_num_threads):

        """ External method to set the current pool size.  Acquires
        the resizing lock, then calls the internal version to do real
        work.
        :param new_num_threads: """

        # Can't change the thread count if we're shutting down the pool!
        if self.is_joining:
            return False

        self.resize_lock.acquire()
        try:
            self.set_thread_count_no_lock(new_num_threads)
        finally:
            self.resize_lock.release()
        return True

    def set_thread_count_no_lock(self, new_num_threads):

        """Set the current pool size, spawning or terminating threads
        if necessary.  Internal use only; assumes the resizing lock is
        held."""

        # If we need to grow the pool, do so
        while new_num_threads > len(self.threads):
            if self.basename:
                thread_name = '{}_{}'.format(self.basename, self.basename_suffix)
                self.basename_suffix += 1
            else:
                thread_name = None
            new_thread = ThreadPoolThread(self, _thread_name=thread_name, _daemon=self.is_daemon)
            self.threads.append(new_thread)
            new_thread.start()
        # If we need to shrink the pool, do so
        while new_num_threads < len(self.threads):
            self.threads[0].kill()
            del self.threads[0]

    def get_thread_count(self):

        """Return the number of threads in the pool."""

        self.resize_lock.acquire()
        try:
            return len(self.threads)
        finally:
            self.resize_lock.release()

    def queue_task(self,
                   task: callable,
                   args: list = None,
                   kwargs: dict = None,
                   _task_callback: callable = None,
                   _err_callback: callable = None,
                   _err_args: list = None,
                   _err_kwargs: dict = None,
                   _task_id: str = None
                   ):

        """
        Inserts a task into the queue
        :param _task_id: gives an ID to the task in order to parse the result against something tangible
        :param task: callable task
        :param args: args for the task as a list
        :param kwargs: kwargs for the task as a dict
        :param _task_callback: callback once the task is done (return value will be passed to it)
        :param _err_callback: callable to run in case of an error
        :param _err_args: args to _err_callback
        :param _err_kwargs: kwargs to _err_callback
        """
        if self.is_joining:
            return False
        if task is None or isinstance(task, bool) or not callable(task):
            raise ValueError('task must be a callable, got {}'.format(type(task)))

        self.task_lock.acquire()
        try:
            self.tasks.append((task, args, kwargs, _task_callback, _err_callback, _err_args, _err_kwargs, _task_id))
            self.ongoing_jobs += 1
            return True
        finally:
            self.task_lock.release()

    def task_done(self):
        """
        Called by worker thread when a task is done (when the function called by the Worker returned)
        """
        self.task_lock.acquire()
        try:
            if self.ongoing_jobs > 0:
                self.ongoing_jobs -= 1
        finally:
            self.task_lock.release()

    def get_next_task(self):

        """ Retrieve the next task from the task queue.  For use
        only by ThreadPoolThread objects contained in the pool."""

        self.task_lock.acquire()
        try:
            if not self.tasks:
                return None, None, None, None, None, None, None, None
            else:
                return self.tasks.pop(0)
        finally:
            self.task_lock.release()

    def join_all(self, wait_for_pending_tasks=True, wait_for_running_tasks=True):

        """ Clear the task queue and terminate all pooled threads,
        optionally allowing the tasks and threads to finish.
        :param wait_for_pending_tasks: whether or not to process pending tasks before joining
        :param wait_for_running_tasks: whether or not to wait for running tasks before joining"""

        # Mark the pool as joining to prevent any more task queueing
        self.is_joining = True

        # Wait for tasks to finish
        if wait_for_pending_tasks:
            while self.tasks:
                time.sleep(.1)

        # Tell all the threads to quit
        self.resize_lock.acquire()
        try:
            self.set_thread_count_no_lock(0)
            self.is_joining = True

            # Wait until all threads have exited
            if wait_for_running_tasks:
                for t in self.threads:
                    t.join()
                    del t

            # Reset the pool for potential reuse
            self.is_joining = False
        finally:
            self.resize_lock.release()

    def all_done(self):
        """
        Checks for ongoing activities in this ThreadPool
        :return: True if all Workers are done, False otherwise
        """
        return self.ongoing_jobs == 0


class ThreadPoolThread(threading.Thread):
    """ Pooled thread class. """

    threadSleepTime = 0.1

    def __init__(self, _pool, _thread_name, _daemon):

        """ Initialize the thread and remember the pool. """

        threading.Thread.__init__(self, name=_thread_name, daemon=_daemon)
        self.__pool = _pool
        self.__isDying = False
        self.exc_info = None

    @staticmethod
    def __run_with_optional_args(runnable: callable, args: list, kwargs: dict):
        if args and kwargs:
            return runnable(*args, **kwargs)
        elif args:
            return runnable(*args)
        elif kwargs:
            return runnable(**kwargs)
        else:
            return runnable()

    def __run(self, cmd, args, kwargs, callback, err_call_back, err_args, err_kwargs, task_id):
        # noinspection PyBroadException
        try:
            return_value = self.__run_with_optional_args(cmd, args, kwargs)
            if callback is not None:
                if task_id is not None:
                    callback((task_id, return_value))
                else:
                    callback(return_value)
        except SystemExit:
            import _thread
            _thread.interrupt_main()
        except KeyboardInterrupt:
            import _thread
            _thread.interrupt_main()
        except:
            import sys

            if hasattr(sys, '_called_from_test'):
                global test_exc
                test_exc = sys.exc_info()

            LOGGER.error(
                'caught error in worker thread:'
                '\ncmd: {} args: {} kwargs: {}'
                '\n{}'
                '\n{}: {}'.format(
                    cmd, args, kwargs,
                    ''.join([x for x in traceback.format_tb(sys.exc_info()[2])]),
                    sys.exc_info()[0], sys.exc_info()[1]
                )
            )
            if err_call_back:
                self.__run_with_optional_args(err_call_back, err_args, err_kwargs)
            else:
                if SENTRY:
                    SENTRY.captureException(sys.exc_info())
        finally:
            self.__pool.task_done()

    def run(self):

        """ Until told to quit, retrieve the next task and execute
        it, calling the callback if any.  """

        while not self.__isDying:
            cmd, args, kwargs, callback, err_call_back, err_args, err_kwargs, task_id = self.__pool.get_next_task()
            if cmd is None:
                time.sleep(ThreadPoolThread.threadSleepTime)
            else:
                if SENTRY:
                    with SENTRY.context:
                        self.__run(cmd, args, kwargs, callback, err_call_back, err_args, err_kwargs, task_id)
                else:
                    self.__run(cmd, args, kwargs, callback, err_call_back, err_args, err_kwargs, task_id)

    def kill(self):

        """ Exit the run loop next time through."""

        self.__isDying = True

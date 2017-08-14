# coding=utf-8
# pylint: disable=global-statement

import os

import click

# noinspection PyUnresolvedReferences
import emft.core.filter_warnings  # noqa: F401 # pylint: disable=unused-import
from emft import cli
from emft.core import nice_exit

LOGGER = None
PROFILER = None


def check_cert():
    """
    Checks availability of "cacert.pem" file installed by the certifi module
    """
    LOGGER.info('certificate: checking')
    import certifi
    from emft.core.path import Path
    cacert = str(Path(certifi.where()).abspath())
    if not os.path.exists(cacert):
        raise FileNotFoundError(cacert)
    # # noinspection SpellCheckingInspection
    # if not cacert.crc32() == 'D069EE01':
    #     raise ImportError('cacert.pem file is corrupted: {}'.format(cacert.crc32()))
    LOGGER.debug('setting up local cacert file to: {}'.format(cacert))
    os.environ['REQUESTS_CA_BUNDLE'] = cacert
    LOGGER.info('certificate: checked')


def _setup_logger(verbose):
    from emft.core.logging import make_logger, get_console_handler, DEBUG, INFO
    from emft.core.logging import persistent_logging_handler
    # noinspection PyProtectedMember
    from emft.core.constant import PATH_LOG_FILE

    global LOGGER
    LOGGER = make_logger(log_file_path=PATH_LOG_FILE, custom_handler=persistent_logging_handler)

    console_handler = get_console_handler()
    if verbose:
        console_handler.setLevel(DEBUG)
    else:
        console_handler.setLevel(INFO)


def _start_profiler(profile):
    if profile:
        global PROFILER

        from pyinstrument import Profiler
        LOGGER.critical('Running profiler')
        PROFILER = Profiler(use_signal=False)
        PROFILER.start()


def _stop_profiler():
    if PROFILER:
        PROFILER.stop()
        with open(f'profiler.html', 'w') as profiler_report:
            profiler_report.write(PROFILER.output_html())


def _another_instance_is_running():
    """Another instance is locking the log file"""
    from PyQt5.QtWidgets import QApplication, QMessageBox  # pylint: disable=no-name-in-module
    from PyQt5.QtGui import QIcon  # pylint: disable=no-name-in-module
    # noinspection PyUnresolvedReferences
    from emft.resources import qt_resource  # noqa: F401  # pylint: disable=unused-variable
    from emft.core.constant import APP_SHORT_NAME, DEFAULT_ICON
    # noinspection PyArgumentList
    app = QApplication.instance()

    if not app:
        # noinspection PyUnusedLocal
        app = QApplication([])
    msgbox = QMessageBox(
        QMessageBox.Critical,
        'Uh oh...',
        f'Another instance of {APP_SHORT_NAME} is already running =)'
    )
    msgbox.setWindowIcon(QIcon(DEFAULT_ICON))
    msgbox.exec()
    nice_exit()


@click.group(invoke_without_command=True, chain=True)
@click.pass_context
@click.option('-t', '--test', is_flag=True, help='Test and exit')
@click.option('-p', '--profile', is_flag=True, help='Profile execution')
@click.option('-v', '--verbose', is_flag=True, help='Outputs debug messages')
def main(ctx, test, profile, verbose):  # pylint: disable=too-many-locals
    """Init Sentry"""
    # noinspection PyUnresolvedReferences
    from emft.core.sentry import SENTRY
    from emft.core.threadpool import register_sentry
    register_sentry(SENTRY)

    try:
        _setup_logger(verbose)

    except PermissionError:
        _another_instance_is_running()

    else:

        _start_profiler(profile)

        # Say hello !
        from emft.__version__ import __version__
        LOGGER.info(f'EMFT {__version__}')

        # Init config
        # noinspection PyUnresolvedReferences
        from emft.config.cfg import Config
        SENTRY.register_context('config', Config())

        if ctx.invoked_subcommand is None:
            # Intercept SIGINT
            import signal as core_sig
            # Intercept OS signals to trigger a nice exit
            core_sig.signal(core_sig.SIGINT, nice_exit)

            # noinspection PyBroadException
            try:
                check_cert()

                from emft.updater import initialize_updater

                initialize_updater(
                    current_version=__version__,
                    av_user='132nd-etcher',
                    av_repo='EMFT',
                    local_executable='emft.exe',
                    channel=Config().update_channel,
                )

                from emft.plugins import reorder
                reorder.initialize()

                from emft.gui.main_ui import start_ui
                start_ui(show=bool(not test))

                from emft.core.constant import QT_APP

                if test:
                    LOGGER.critical('RUNNING IN TEST MODE')
                    import time
                    from emft.core.threadpool import ThreadPool

                    def test_hook():
                        LOGGER.critical('TEST MODE: waiting 10 seconds')
                        time.sleep(10)
                        LOGGER.critical('TEST MODE: end of timer')
                        QT_APP.exit(0)
                        # nice_exit()

                    pool = ThreadPool(1, 'test', _daemon=True)
                    pool.queue_task(test_hook)

                exit_code = QT_APP.exec()

                _stop_profiler()

            except SystemExit as exc:
                LOGGER.info('caught SystemExit')
                exit_code = exc.code or 1
            except:  # pylint: disable=bare-except
                LOGGER.exception('caught exception in main loop')
                SENTRY.captureException()
                exit_code = 1

            LOGGER.info('bye bye ! =)')
            nice_exit(exit_code)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

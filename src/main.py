# coding=utf-8

if __name__ == '__main__':

    """Setup logging"""
    from utils.custom_logging import make_logger
    # noinspection PyProtectedMember
    from src.global_ import PATH_LOG_FILE
    from src.misc.logging_handler import persistent_logging_handler
    logger = make_logger(__name__, log_file_path=PATH_LOG_FILE, custom_handler=persistent_logging_handler)

    """Say hello !"""
    from src.__version__ import __version__
    logger.info(__version__)

    """Init config"""
    # noinspection PyUnresolvedReferences
    from src.cfg.cfg import Config

    """Init Sentry"""
    # noinspection PyUnresolvedReferences
    from src.sentry import SENTRY
    from utils.threadpool import register_sentry
    register_sentry(SENTRY)
    SENTRY.register_context('config', Config())

    """Intercept SIGINT"""
    import signal as core_sig
    from utils import nice_exit
    # Intercept OS signals to trigger a nice exit
    core_sig.signal(core_sig.SIGINT, nice_exit)

    import src.emft
    try:
        src.emft.main()
    except SystemExit as e:
        logger.info('caught SystemExit, bye bye !')
        nice_exit(e.code)
    except:
        logger.exception('caught exception in main loop')
        raise

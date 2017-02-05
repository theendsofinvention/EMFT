# coding=utf-8

if __name__ == '__main__':

    """Setup logging"""
    from src.utils.custom_logging import make_logger
    # noinspection PyProtectedMember
    from src._global import PATH_LOG_FILE
    logger = make_logger(__name__, log_file_path=PATH_LOG_FILE)

    """Say hello !"""
    from src.__version__ import __version__
    logger.info(__version__)

    """Init config"""
    # noinspection PyUnresolvedReferences
    from src.cfg.cfg import Config

    """Init Sentry"""
    # noinspection PyUnresolvedReferences
    from src.sentry import sentry

    """Intercept SIGINT"""
    import signal as core_sig
    from src.utils import nice_exit
    # Intercept OS signals to trigger a nice exit
    core_sig.signal(core_sig.SIGINT, nice_exit)


    # def ph(data):
    #     print(data)
    #
    #
    # from src.utils.downloader import Downloader
    #
    # d = Downloader(
    #     url=r'http://download.thinkbroadband.com/100MB.zip',
    #     filename='./test',
    #     progress_hooks=[ph]
    # )
    # d.download()

    import src.emft
    src.emft.main()

from src.cfg import Config
from src.miz import Miz
from src.reorder.finder import FindProfile, FindRemoteVersion, FindOutputFolder
from src.ui.main_ui_interface import I
from src.utils import ThreadPool, make_logger, Path

logger = make_logger(__name__)


class ReorderMiz:
    _POOL = ThreadPool(1, 'reorder', _daemon=True)

    @staticmethod
    def _on_reorder_error(miz_file):
        # noinspection PyCallByClass
        I.error(f'Could not unzip the following file:\n\n{miz_file}\n\n'
                'Please check the log, and eventually send it to me along with the MIZ file '
                'if you think this is a bug.')

    @staticmethod
    def manual_reorder(path_to_miz: str):
        error = None
        miz_file = Path(path_to_miz)
        output_folder = FindOutputFolder.get_active_output_folder()
        if not miz_file.exists():
            error = f'MIZ file does not exist: {miz_file.abspath()}'
        if not output_folder:
            error = 'no output folder selected'
        else:
            if not output_folder.exists():
                error = f'output folder does not exist:\n\n{miz_file.abspath()}'
        if error:
            logger.error(error)
            I.error(error.replace(':', ':\n\n').capitalize())
            return
        ReorderMiz.reorder_miz_file(
            miz_file_path=str(miz_file.abspath()),
            output_folder_path=output_folder,
            skip_option_file=Config().skip_options_file,
        )

    @staticmethod
    def auto_reorder():
        profile = FindProfile.get_active_profile()
        if not profile:
            logger.error('no active profile')
            return
        latest = FindRemoteVersion.get_latest()
        if not latest:
            logger.error('no remote version')
            return
        local_file = Path(profile.src_folder).joinpath(latest.remote_file_name).abspath()
        if not local_file.exists():
            logger.error(f'local file not found: {local_file.abspath()}')
        ReorderMiz.reorder_miz_file(
            miz_file_path=str(local_file.abspath()),
            output_folder_path=profile.output_folder,
            skip_option_file=Config().skip_options_file,
        )

    @staticmethod
    def reorder_miz_file(
            miz_file_path: str,
            output_folder_path: str,
            skip_option_file: bool
    ):
        ReorderMiz._POOL.queue_task(
            task=Miz.reorder,
            kwargs=dict(
                miz_file_path=miz_file_path,
                target_dir=output_folder_path,
                skip_options_file=skip_option_file
            ),
            _err_callback=ReorderMiz._on_reorder_error,
            _err_args=[miz_file_path],
        )

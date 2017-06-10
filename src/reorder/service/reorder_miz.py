from src.miz import Miz
from src.ui.main_ui_interface import I
from src.utils import ThreadPool

REORDER_THREAD = ThreadPool(1, 'reorder', _daemon=True)


class ReorderMiz:
    @staticmethod
    def _on_reorder_error(miz_file):
        # noinspection PyCallByClass
        I.error(f'Could not unzip the following file:\n\n{miz_file}\n\n'
                'Please check the log, and eventually send it to me along with the MIZ file '
                'if you think this is a bug.')

    @staticmethod
    def reorder_miz_file(
            miz_file_path: str,
            output_folder_path: str,
            skip_option_file: bool
    ):
        REORDER_THREAD.queue_task(
            task=Miz.reorder,
            kwargs=dict(
                miz_file_path=miz_file_path,
                target_dir=output_folder_path,
                skip_options_file=skip_option_file
            ),
            _err_callback=ReorderMiz._on_reorder_error,
            _err_args=[miz_file_path],
        )

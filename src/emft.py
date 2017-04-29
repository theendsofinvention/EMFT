import os
import subprocess
import sys
from json import loads

import click
from natsort.natsort import natsorted

from utils.custom_logging import make_logger, DEBUG, INFO
from utils.custom_path import Path

__version__ = None

if hasattr(sys, 'frozen'):
    __version__ = Path(sys.executable).get_win32_file_info().file_version
elif os.environ.get('APPVEYOR'):
    __version__ = loads(subprocess.check_output(
        [r'C:\ProgramData\chocolatey\bin\gitversion.exe']).decode().rstrip()).get('FullSemVer')
else:
    # This is a potential security breach, but I'm leaving it as is as it should only be running scripted
    __version__ = loads(subprocess.check_output(['gitversion']).decode().rstrip()).get('FullSemVer')

__guid__ = '4ae6dbb7-5b26-28c6-b797-2272f5a074f3'

__appname__ = 'TEMP'

logger = make_logger(__name__, ch_level=INFO)


def find_latest_trmt(folder: Path or str):
    return natsorted([Path(f).abspath() for f in Path(folder).listdir('TRMT_*.miz')]).pop()


def check_cert():
    logger.info('certificate: checking')
    import certifi
    import os

    from utils.custom_path import Path
    cacert = Path(certifi.where())
    # noinspection SpellCheckingInspection
    if not cacert.crc32() == 'D069EE01':
        raise ImportError('cacert.pem file is corrupted: {}'.format(cacert.crc32()))
    logger.debug('setting up local cacert file to: {}'.format(str(cacert)))
    os.environ['REQUESTS_CA_BUNDLE'] = str(cacert)
    logger.info('certificate: checked')


@click.command()
@click.option('-t', '--test', is_flag=True, help='Test and exit')
# @click.option('-m', '--mizfile', nargs=1, type=str, default=None, help='Source MIZ file.')
# @click.option('-o', '--output', nargs=1, default='./output', help='Directory to store the results in.')
# @click.option('-l', '--latest', nargs=1, default=None,
#               help='Folder that contains the TRMT files; the latest will be picked automatically.')
@click.option('-v', '--verbose', is_flag=True, help='Outputs debug messages')
def main(test, verbose):

    # from src.miz.miz import Miz
    #
    # with Miz(r'C:\Users\bob\Saved Games\DCS\Missions\132nd\TRMT_2.4.0.86.miz') as miz:
    #     mission = miz.mission
    #     miz._encode_mission()
    #     os.remove(r'C:\Users\bob\Saved Games\DCS\Missions\132nd\TRMT_2.4.0.86_EMFT\mission')
    #     os.rename(miz.mission_file_path, r'C:\Users\bob\Saved Games\DCS\Missions\132nd\TRMT_2.4.0.86_EMFT\mission')
    #     # miz.zip()
    #
    #
    # # for client in mission.get_clients_groups():
    # #     print(client.group_name)
    #
    # exit(0)

    if verbose:
        from utils.custom_logging import CH
        CH.setLevel(DEBUG)

    check_cert()

    from src.ui.main_ui import start_ui
    start_ui(test)

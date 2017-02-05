# coding=utf-8
"""
Runs a process in an external thread and logs the output to a standard Python logger
"""
from zipfile import ZipFile
import os
import subprocess
import threading
from json import loads

import certifi
import click

from src import _global
from src.utils.custom_logging import DEBUG, make_logger
from src.utils.custom_path import Path

logger = make_logger(__name__)
logger.setLevel(DEBUG)

# noinspection PyPep8Naming
class __LogPipe(threading.Thread):
    def __init__(self, logger, level):
        """Setup the object with a logger and a loglevel and start the thread"""
        threading.Thread.__init__(self)
        self.daemon = True
        self.level = level
        self.logger = logger
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe"""
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything"""
        for line in iter(self.pipeReader.readline, ''):
            # print(line.strip(os.linesep))
            self.logger.error(line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe"""
        os.close(self.fdWrite)


def run_piped_process(args, logger, level=DEBUG, cwd=None, env=None, exe=None):
    """
    Runs a standard process and pipes its output to a Python logger
    :param args: process and arguments ias a list
    :param logger: logger to send data to
    :param level: logging level, defaults to DEBUG
    :param cwd: working dir to spawn the process in (defaults to current)
    """
    log_pipe = __LogPipe(logger, level)

    logger.info('running: {} {} (in {})'.format(exe, ' '.join(args), cwd))
    with subprocess.Popen(args, stdout=log_pipe, stderr=log_pipe, cwd=cwd, env=env, executable=exe) as p:
        p.communicate()
        if p.returncode != 0:
            logger.error('return code: {}'.format(p.returncode))
            raise RuntimeError('command failed: {}'.format(args))
        log_pipe.close()


def patch_exe(path_to_exe: str or Path,
              version: str,
              app_name: str,
              app_long_name: str,
              wkdir: str or Path,
              build: str):

    path_to_exe = Path(path_to_exe)
    wkdir = Path(wkdir)

    logger.info('patch exe: start')
    app_name = app_name

    if not path_to_exe.exists():
        raise FileNotFoundError(path_to_exe)
    if not wkdir.exists():
        raise FileNotFoundError(wkdir)

    logger.debug('short name: {}'.format(app_name))
    logger.debug('version: {}'.format(version))
    logger.debug('patching: {}'.format(path_to_exe.abspath()))

    cmd = [
        'verpatch',
        path_to_exe,
        '/high',
        version,
        # '{}'.format(version),
        '/va',
        '/pv', version,
        # '/s', 'description', app_long_name,
        '/s', 'product', app_name,
        '/s', 'copyright', '2017 etcher',
        '/s', 'company', 'etcher',
        '/s', 'build', str(build),
        '/s', 'PrivateBuild', str(build),
        # '/sc', 'some comments',
        '/langid', '1033',
    ]
    run_piped_process(cmd, logger=logger, cwd=wkdir)


def pre_build(env):
    logger.info('building UI resource files')
    run_piped_process(
        args=[
            os.path.join(env, r'scripts\pyrcc5.exe'),
            # str(Path('./src/ui/qt_resources.qrc').abspath()),
            './src/ui/qt_resource.qrc',
            '-o',
            # str(Path('./src/ui/qt_resources.py').abspath())
            './src/ui/qt_resource.py'
        ],
        logger=logger,
    )


# certifi-2017.1.23 cffi-1.9.1 cryptography-1.7.2 idna-2.2 packaging-16.8 paramiko-2.1.1 pyasn1-0.1.9 pycparser-2.17 pyparsing-2.1.10 scp-0.10.2 setuptools-34.1.1

def build(env):
    logger.info('reading GitVersion output')
    version = loads(subprocess.check_output(['gitversion'], cwd='.').decode().rstrip())
    logger.debug('gitversion says: {}'.format(version))
    logger.info('compiling packed executable')
    run_piped_process([
        os.path.join(env, 'python.exe'),
        '-m', 'PyInstaller',
        # os.path.join(env, r'scripts/pyupdater.exe'), 'build',
        '--noconfirm',
        '--onefile',
        '--clean',
        '--icon', './src/ui/app.ico',
        '--workpath', './build',
        '--paths', os.path.join(env, r'Lib\site-packages\PyQt5\Qt\bin'),
        '--log-level=WARN',
        '--add-data', '{};{}'.format(certifi.where(), '.'),
        '--name', _global.APP_SHORT_NAME,
        '--distpath', './dist',
        '--windowed',
        './main.py',
        # '--app-version={}'.format(version.get('SemVer')),
        # '-k',
        # '--clean',
    ], logger=logger, cwd='.')
    logger.info('patching exe resources')
    patch_exe(
        path_to_exe=Path('./dist/EMFT.exe'),
        version=version.get('SemVer'),
        app_name=_global.APP_SHORT_NAME,
        app_long_name=_global.APP_FULL_NAME,
        wkdir=Path('.'),
        build=version.get('InformationalVersion'),
    )
    # with ZipFile(Path('./pyu-data/new').joinpath('EMFT-win-{}.zip'.format(version.get('LegacySemVer'))), mode='w') as z:
    #     z.write('./pyu-data/new/win.exe', arcname='EMFT.exe')
    # run_piped_process([
    #     os.path.join(env, r'scripts/pyupdater.exe'), 'pkg', '-p'
    # ], logger=logger, cwd='.')
    # run_piped_process([
    #     os.path.join(env, r'scripts/pyupdater.exe'), 'upload', '--service', 'scp'
    # ], logger=logger, cwd='.')

    logger.info('all done')


@click.command()
@click.argument('env', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('-p', '--pre', is_flag=True, help='Pre build only')
def main(env, pre):
    pre_build(env)
    if pre:
        exit(0)
    build(env)


if __name__ == '__main__':
    main()

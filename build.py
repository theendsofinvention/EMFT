# coding=utf-8
"""
Runs a process in an external thread and logs the output to a standard Python logger
"""
import os
import re
import subprocess
import threading
from json import loads

import certifi
import click

try:
    from src import global_
    from utils.custom_logging import DEBUG, make_logger
    from utils.custom_path import Path
except ImportError or ModuleNotFoundError:
    import sys

    subprocess.check_call(
        [os.path.join(sys.argv[1], 'scripts/pip.exe'), 'install', '-r', 'own-requirements.txt'],
        stdout=subprocess.PIPE
    )
    from src import global_
    from utils.custom_logging import DEBUG, make_logger
    from utils.custom_path import Path

logger = make_logger(__name__)
logger.setLevel(DEBUG)

requirements = None


# noinspection PyPep8Naming
class __LogPipe(threading.Thread):
    def __init__(self, logger_, level):
        threading.Thread.__init__(self)
        self.daemon = True
        self.level = level
        self.logger = logger_
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        return self.fdWrite

    def run(self):
        for line in iter(self.pipeReader.readline, ''):
            self.logger.error(line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        os.close(self.fdWrite)


def run_piped_process(args, logger_, level=DEBUG, cwd=None, env=None, exe=None):
    """
    Runs a standard process and pipes its output to a Python logger
    :param exe: executable
    :param env: working dir
    :param args: process and arguments ias a list
    :param logger_: logger to send data to
    :param level: logging level, defaults to DEBUG
    :param cwd: working dir to spawn the process in (defaults to current)
    """
    log_pipe = __LogPipe(logger_, level)

    logger_.info('running: {} {} (in {})'.format(exe, ' '.join(args), cwd))
    with subprocess.Popen(args, stdout=log_pipe, stderr=log_pipe, cwd=cwd, env=env, executable=exe) as p:
        p.communicate()
        if p.returncode != 0:
            logger_.error('return code: {}'.format(p.returncode))
            raise RuntimeError('command failed: {}'.format(args))
        log_pipe.close()


def patch_exe(path_to_exe: str or Path,
              version: str,
              app_name: str,
              wkdir: str or Path,
              build_: str):
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
        '/va',
        '/pv', version,
        '/s', 'product', app_name,
        '/s', 'copyright', '2017 etcher',
        '/s', 'company', 'etcher',
        '/s', 'build', str(build_),
        '/s', 'PrivateBuild', str(build_),
        '/langid', '1033',
    ]
    run_piped_process(cmd, logger_=logger, cwd=wkdir)


def pre_build(env):
    logger.info('building UI resource files')
    run_piped_process(
        args=[
            os.path.join(env, r'scripts\pyrcc5.exe'),
            './src/ui/qt_resource.qrc',
            '-o',
            './src/ui/qt_resource.py'
        ],
        logger_=logger,
    )


# certifi-2017.1.23 cffi-1.9.1 cryptography-1.7.2 idna-2.2 packaging-16.8
# paramiko-2.1.1 pyasn1-0.1.9 pycparser-2.17 pyparsing-2.1.10 scp-0.10.2 setuptools-34.1.1

def build(env):
    logger.info('reading GitVersion output')
    version = loads(subprocess.check_output(['gitversion'], cwd='.').decode().rstrip())
    logger.debug('gitversion says: {}'.format(version))
    logger.info('compiling packed executable')
    run_piped_process([
        os.path.join(env, 'python.exe'),
        '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--clean',
        '--icon', './src/ui/app.ico',
        '--workpath', './build',
        '--paths', os.path.join(env, r'Lib\site-packages\PyQt5\Qt\bin'),
        '--log-level=WARN',
        '--add-data', '{};{}'.format(certifi.where(), '.'),
        '--name', global_.APP_SHORT_NAME,
        '--distpath', './dist',
        '--windowed',
        './src/main.py',
    ], logger_=logger, cwd='.')
    logger.info('patching exe resources')
    patch_exe(
        path_to_exe=Path('./dist/EMFT.exe'),
        version=version.get('SemVer'),
        app_name=global_.APP_SHORT_NAME,
        wkdir=Path('.'),
        build_=version.get('InformationalVersion'),
    )

    logger.info('all done')


def get_installed_packages(env):
    global requirements
    if requirements is None:
        requirements = subprocess.Popen(
            [os.path.join(env, 'scripts/pip.exe'), 'freeze'],
            stdout=subprocess.PIPE
        ).stdout.read().decode('utf8')
        requirements = requirements.rstrip()
        requirements = requirements.replace('\r\n', '\n')
        # requirements = requirements.replace(r'PyInstaller==3.3.dev0+gb78bfe5',
        #                                     r'git+https://github.com/132nd-etcher/pyinstaller.git#egg=PyInstaller')
        requirements = re.sub(r'SLTP==\d+.\d+.\d+.*\n?', r'', requirements)
        requirements = re.sub(r'utils==\d+.\d+.\d+.*\n?', r'', requirements)
        requirements.strip()
    return requirements


def _write_requirements_in():
    Path('requirements.in').write_lines(x.split('==')[0] for x in requirements.split('\n'))


def _write_own_requirements():
    own_requirements = [
        'git+https://github.com/132nd-etcher/sltp.git#egg=sltp',
        'git+https://github.com/132nd-etcher/utils.git#egg=utils'
    ]
    Path('own-requirements.txt').write_text('\n'.join(own_requirements))


def _compile_requirements(env, upgrade=False):

    args = [os.path.join(env, 'scripts/pip-compile.exe')]

    if upgrade:
        args.append('--upgrade')

    logger.debug('\n' +subprocess.Popen(
        args,
        stdout=subprocess.PIPE
    ).stdout.read().decode('utf8'))

    req_file = Path('requirements.txt')
    req_file.write_lines([x for x in req_file.lines() if not x.startswith('#')])


def sync_requirements(env):
    logger.debug('\n'+subprocess.Popen(
        [os.path.join(env, 'scripts/pip-sync.exe')],
        stdout=subprocess.PIPE
    ).stdout.read().decode('utf8'))


def install_own_requirements(env):
    logger.debug('\n' +subprocess.Popen(
        [os.path.join(env, 'scripts/pip.exe'), 'install', '-r', 'own-requirements.txt'],
        stdout=subprocess.PIPE
    ).stdout.read().decode('utf8'))


def build_requirements(env):
    get_installed_packages(env)
    _write_own_requirements()
    _write_requirements_in()
    _compile_requirements(env)


def update_requirements(env):
    get_installed_packages(env)
    _write_own_requirements()
    _write_requirements_in()
    _compile_requirements(env, upgrade=True)
    sync_requirements(env)
    install_own_requirements(env)


def generate_changelog(env):
    logger.debug('building changelog')
    changelog = subprocess.Popen(
        [os.path.join(env, 'scripts/gitchangelog.exe'), '0.4.1..HEAD'],
        stdout=subprocess.PIPE
    ).stdout.read().decode('utf8')
    with open('CHANGELOG.rst', mode='w') as f:
        f.write(changelog)


def install_local_dependencies(env):
    import pip
    pip.main(['install', '-U', '--upgrade-strategy', 'only-if-needed', 'git+file://f:/dev/utils@develop'])
    pip.main(['install', '-U', '--upgrade-strategy', 'only-if-needed', 'git+file://f:/dev/sltp@develop'])


@click.command()
@click.argument('env', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('-p', '--pre', is_flag=True, help='Pre build only')
@click.option('-l', '--local-develop',
              is_flag=True, help='Only install local repositories from develop branch')
@click.option('-r', '--req', is_flag=True, help='Req build only')
@click.option('-c', '--cha', is_flag=True, help='Changelog build only')
@click.option('-u', '--update-req', is_flag=True, help='Update all requirements')
@click.option('-s', '--sync_req', is_flag=True, help='Sync requirements')
def main(env, pre, req, cha, local_develop, update_req, sync_req):
    if sync_req:
        sync_requirements(env)
        install_own_requirements(env)
        return
    if update_req:
        update_requirements(env)
        return
    if local_develop:
        install_local_dependencies(env)
        return
    if cha:
        generate_changelog(env)
        return
    if req:
        build_requirements(env)
        return
    pre_build(env)
    if pre:
        exit(0)
    build(env)


if __name__ == '__main__':
    main()

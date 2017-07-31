import datetime
import os
import platform
import re
import shlex
import subprocess
import sys
from json import loads

import certifi
import click
import semantic_version

from setup import install_requires, dev_requires, test_requires


def find_executable(executable: str, path=None):  # noqa: C901
    # noinspection SpellCheckingInspection
    """
    https://gist.github.com/4368898

    Public domain code by anatoly techtonik <techtonik@gmail.com>

    AKA Linux `which` and Windows `where`

    Find if ´executable´ can be run. Looks for it in 'path'
    (string that lists directories separated by 'os.pathsep';
    defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.
    """

    if '_known_executables' in globals():
        global _known_executables
    else:
        _known_executables = {}

    if not executable.endswith('.exe'):
        executable = f'{executable}.exe'

    if executable in _known_executables:
        return _known_executables[executable]

    click.secho(f'looking for executable: {executable}', fg='blue', nl=False)

    executable_path = os.path.abspath(os.path.join(sys.exec_prefix, 'Scripts', executable))
    if os.path.exists(executable_path):
        click.secho(f' -> {click.format_filename(executable_path)}', fg='blue')
        _known_executables[executable] = executable_path
        return executable_path

    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    ext_list = ['']
    path_ext = os.environ['PATHEXT'].lower().split(os.pathsep)
    (base, ext) = os.path.splitext(executable)
    if ext.lower() not in path_ext:
        ext_list = path_ext
    for ext in ext_list:
        exec_name = executable + ext
        if os.path.isfile(exec_name):
            click.secho(f' -> {click.format_filename(exec_name)}', fg='blue')
            _known_executables[executable] = exec_name
            return exec_name
        else:
            for p in paths:
                f = os.path.join(p, exec_name)
                if os.path.isfile(f):
                    click.secho(f' -> {click.format_filename(f)}', fg='blue')
                    _known_executables[executable] = f
                    return f
    else:
        click.secho(f' -> not found', fg='red', err=True)
        raise FileNotFoundError()


def do_ex(cmd, cwd='.'):
    def _popen_pipes(cmd_, cwd_):
        def _always_strings(env_dict):
            """
            On Windows and Python 2, environment dictionaries must be strings
            and not unicode.
            """
            if IS_WINDOWS:
                env_dict.update(
                    (key, str(value))
                    for (key, value) in env_dict.items()
                )
            return env_dict

        return subprocess.Popen(
            cmd_,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd_),
            env=_always_strings(dict(
                os.environ,
                # try to disable i18n
                LC_ALL='C',
                LANGUAGE='',
                HGPLAIN='1',
            ))
        )

    def _ensure_stripped_str(str_or_bytes):
        if isinstance(str_or_bytes, str):
            return '\n'.join(str_or_bytes.strip().splitlines())
        else:
            return '\n'.join(str_or_bytes.decode('utf-8', 'surogate_escape').strip().splitlines())

    cmd.insert(0, find_executable(cmd.pop(0)))
    click.secho(f'{cmd}', nl=False, fg='magenta')
    p = _popen_pipes(cmd, cwd)
    out, err = p.communicate()
    click.secho(f' -> {p.returncode}', fg='magenta')
    return _ensure_stripped_str(out), _ensure_stripped_str(err), p.returncode


def do(cmd, cwd='.'):
    if not isinstance(cmd, (list, tuple)):
        cmd = shlex.split(cmd)

    # click.secho(f'running: {cmd}', nl=False, fg='magenta')

    out, err, ret = do_ex(cmd, cwd)
    if out:
        click.secho(f'{out}', fg='cyan')
    if err:
        click.secho(f'{err}', fg='red')
    if ret:
        exit(ret)
    return out


def get_gitversion() -> dict:
    try:
        if os.environ.get('APPVEYOR'):
            exe = find_executable('gitversion', r'C:\ProgramData\chocolatey\bin')
        else:
            exe = find_executable('gitversion')
    except FileNotFoundError:
        click.secho(
            '"gitversion.exe" not been found in your PATH.\n'
            'GitVersion is used to infer the current version from the Git repository.\n'
            'setuptools_scm plans on switching to using the Semver scheme in the future; when that happens, '
            'I\'ll remove the dependency to GitVersion.\n'
            'In the meantime, GitVersion can be obtained via Chocolatey (recommended): '
            'https://chocolatey.org/packages/GitVersion.Portable\n'
            'If you already have chocolatey installed, you can simply run the following command (as admin):\n\n'
            '\t\t"choco install gitversion.portable -pre -y"\n\n'
            'If you\'re not comfortable using the command line, there is a GUI tool for Chocolatey available at:\n\n'
            '\t\thttps://github.com/chocolatey/ChocolateyGUI/releases\n\n'
            'Or you can install directly from :\n\n'
            '\t\thttps://github.com/GitTools/GitVersion/releases',
            err=True,
        )
        raise SystemExit()
    return loads(subprocess.getoutput([exe]).rstrip())


def get_pep440_version() -> str:
    convert_prereleases = (
        dict(
            prerelease='alpha',
            converts_to='a',
        ),
        dict(
            prerelease='beta',
            converts_to='b',
        ),
        dict(
            prerelease='exp',
            converts_to='rc',
        ),
        dict(
            prerelease='patch',
            converts_to='post',
        ),
    )

    semver = semantic_version.Version.coerce(__version__.get('FullSemVer'))
    version_str = f'{semver.major}.{semver.minor}.{semver.patch}'
    prerelease = semver.prerelease

    # Pre-release
    if prerelease:
        assert isinstance(prerelease, tuple)

        # Convert the pre-release tag to a valid PEP440 tag and strip it
        for convert_scheme in convert_prereleases:
            if prerelease[0] in convert_scheme['prerelease']:
                version_str += convert_scheme['converts_to']
                prerelease = prerelease[1:]
                break
        else:
            raise ValueError(f'unknown pre-release tag: {version_str.prerelease[0]}')

        # If there is a distance to the last tag, add a ".dev[distance]" suffix
        if re.match(r'[\d]+', prerelease[-1]):
            version_str += f'{prerelease[-1]}'
            # prerelease = prerelease[:-1]

    # Regular release
    else:
        version_str = f'{version_str.major}.{version_str.minor}.{version_str.patch}'

    # Add SemVer, Sha and last commit date to the build tag
    # local_version = re.sub(r'[^a-zA-Z0-9\.]', '.', __version__.get('FullSemVer'))
    # commit_date = re.sub(r'-0', '.', __version__.get('CommitDate'))
    # version += f'+{local_version}.{__version__.get("Sha")}.{commit_date}'.replace('-', '.')

    return version_str


class Checks:
    @staticmethod
    def pylint(**kwargs):
        do(['pylint'])

    @staticmethod
    def prospector():
        do(['prospector'])

    @staticmethod
    def pytest():
        do(['pytest'])

    @staticmethod
    def flake8():
        do(['flake8'])

    @staticmethod
    def safety():
        do(['safety', 'check', '--bare'])


class HouseKeeping:
    SRC_FILE = 'temp'

    @classmethod
    def _write_requirements(cls, packages_list, outfile, prefix_list=None):
        with open(cls.SRC_FILE, 'w') as source_file:
            source_file.write('\n'.join(packages_list))
        packages, _, ret = do_ex([
            'pip-compile',
            '--index',
            '--upgrade',
            '--annotate',
            '--no-header',
            '-n',
            cls.SRC_FILE
        ])
        os.remove(cls.SRC_FILE)
        with open(outfile, 'w') as req_file:
            if prefix_list:
                for prefix in prefix_list:
                    req_file.write(f'{prefix}\n')
            for package in packages.splitlines():
                req_file.write(f'{package}\n')

    @classmethod
    def write_prod(cls):
        cls._write_requirements(
            packages_list=install_requires,
            outfile='requirements.txt'
        )

    @classmethod
    def write_test(cls):
        cls._write_requirements(
            packages_list=test_requires,
            outfile='requirements-test.txt',
            prefix_list=['-r requirements.txt']
        )

    @classmethod
    def write_dev(cls):
        cls._write_requirements(
            packages_list=dev_requires,
            outfile='requirements-dev.txt',
            prefix_list=['-r requirements.txt', '-r requirements-test.txt']
        )

    @classmethod
    def write_requirements(cls):
        cls.write_prod()
        cls.write_test()
        cls.write_dev()

    @classmethod
    def write_changelog(cls, commit: bool, push: bool = False):
        changelog = do(['gitchangelog', '0.4.1..HEAD'])
        with open('CHANGELOG.rst', mode='w') as f:
            f.write(re.sub('(\s*\r\n){2,}', '\r\n', changelog))
        if commit:
            do_ex(['git', 'add', 'CHANGELOG.rst'])
            _, _, ret = do_ex(['git', 'commit', '-m', 'chg: dev: updated changelog [skip ci]'])
            if ret == 0 and push:
                do_ex(['git', 'push'])

    @classmethod
    def compile_qt_resources(cls):
        do([
            'pyrcc5',
            './emft/ui/qt_resource.qrc',
            '-o', './emft/ui/qt_resource.py',
        ])

    @classmethod
    def write_version(cls):
        with open('./emft/__version_frozen__.py', 'w') as version_file:
            version_file.write(
                f"# coding=utf-8\n"
                f"__version__ = '{__semver__}'\n"
                f"__pep440__ = '{get_pep440_version()}'\n")


class Make:
    @classmethod
    def install_pyinstaller(cls):
        do(['pip', 'install',
            'git+https://github.com/132nd-etcher/pyinstaller.git@develop#egg=pyinstaller==3.3.dev0+g2fcbe0f'])

    @classmethod
    def freeze(cls):
        do([
            sys.executable,
            '-m', 'PyInstaller',
            '--log-level=WARN',
            '--noconfirm', '--onefile', '--clean', '--windowed',
            '--icon', './emft/ui/app.ico',
            '--workpath', './build',
            '--distpath', './dist',
            '--paths', f'{os.path.join(sys.exec_prefix, "Lib/site-packages/PyQt5/Qt/bin")}',
            '--add-data', f'{certifi.where()};.',
            '--name', 'EMFT',
            './emft/main.py'
        ])

    @classmethod
    def patch_exe(cls):
        if not find_executable('verpatch'):
            click.secho(
                '"verpatch.exe" not been found in your PATH.\n'
                'Verpatch is used to embed resources like the version after the compilation.\n'
                'I\'m waiting on PyInstaller to port their own resources patcher to Python 3 so I can remove the '
                'dependency to this external tool...\n'
                'In the meanwhile, "verpatch" can be obtained at: https://ddverpatch.codeplex.com/releases',
                err=True, fg='red'
            )
            raise FileNotFoundError()
        year = datetime.datetime.now().year
        do([
            'verpatch',
            './dist/EMFT.exe',
            '/high',
            __version__['FullSemVer'],
            '/va',
            '/pv', __version__['FullSemVer'],
            '/s', 'desc', 'EtchersMissionFilesTools',
            '/s', 'product', 'EMFT',
            '/s', 'title', 'EMFT',
            '/s', 'copyright', f'{year}-132nd-etcher',
            '/s', 'company', '132nd-etcher,132nd-Entropy,132nd-Neck',
            '/s', 'SpecialBuild', f'{__version__["BranchName"]}@{__version__["Sha"]}',
            '/s', 'PrivateBuild', f'{__version__["InformationalVersion"]}.{__version__["CommitDate"]}',
            '/langid', '1033',
        ])

    @classmethod
    def build_doc(cls):
        do([
            'sphinx-build',
            '-b',
            'html',
            'doc',
            'doc/html'
        ])


@click.group(invoke_without_command=True)
@click.option('--install/--no-install', default=True)
@click.pass_context
def cli(ctx, install):
    if install:
        do(['pip', 'install', '-r', 'requirements-dev.txt'])
    if ctx.invoked_subcommand is None:
        Checks.safety()
        Checks.flake8()
        Checks.pytest()
        # Checks.pylint()  # TODO
        # Checks.prospector()  # TODO
        HouseKeeping.compile_qt_resources()
        HouseKeeping.write_changelog(commit=True)
        HouseKeeping.write_requirements()
        Make.install_pyinstaller()
        Make.freeze()
        Make.patch_exe()
        Make.build_doc()


@cli.command()
@click.option('--prod/--no-prod', default=True)
@click.option('--test/--no-test', default=True)
@click.option('--dev/--no-dev', default=True)
@click.pass_context
def reqs(ctx, prod, test, dev):
    if prod:
        HouseKeeping.write_prod()
    if test:
        HouseKeeping.write_test()
    if dev:
        HouseKeeping.write_dev()


@cli.command()
@click.pass_context
def version(ctx):
    HouseKeeping.write_version()


@cli.command()
@click.option('--commit/--no-commit', default=True)
@click.pass_context
def chglog(ctx, commit):
    HouseKeeping.write_changelog(commit)


@cli.command()
@click.pass_context
def pyrcc(ctx):
    HouseKeeping.compile_qt_resources()


@cli.command()
@click.pass_context
def pytest(ctx):
    Checks.pytest()


@cli.command()
@click.pass_context
def flake8(ctx):
    Checks.flake8()


@cli.command()
@click.pass_context
def prospector(ctx):
    Checks.prospector()


@cli.command()
@click.pass_context
def pylint(ctx):
    Checks.pylint()


@cli.command()
@click.pass_context
def safety(ctx):
    Checks.safety()


@cli.command()
@click.pass_context
def doc(ctx):
    Make.build_doc()


@cli.command()
@click.option('--install/--no-install', default=True)
@click.pass_context
def freeze(ctx, install):
    if install:
        Make.install_pyinstaller()
    Make.freeze()


@cli.command()
@click.pass_context
def patch(ctx):
    Make.patch_exe()


if __name__ == '__main__':
    IS_WINDOWS = platform.system() == 'Windows'

    __version__ = get_gitversion()
    __semver__ = __version__.get("FullSemVer")
    __pep440__ = get_pep440_version()
    click.secho(f'SemVer: {__semver__}', fg='blue')

    cli(obj={})

# coding=utf-8
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

    click.secho(f'looking for executable: {executable}', fg='green', nl=False)

    executable_path = os.path.abspath(os.path.join(sys.exec_prefix, 'Scripts', executable))
    if os.path.exists(executable_path):
        click.secho(f' -> {click.format_filename(executable_path)}', fg='green')
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
            click.secho(f' -> {click.format_filename(exec_name)}', fg='green')
            _known_executables[executable] = exec_name
            return exec_name
        else:
            for p in paths:
                f = os.path.join(p, exec_name)
                if os.path.isfile(f):
                    click.secho(f' -> {click.format_filename(f)}', fg='green')
                    _known_executables[executable] = f
                    return f
    else:
        click.secho(f' -> not found', fg='red', err=True)
        raise FileNotFoundError()


def do_ex(ctx, cmd, cwd='.'):
    def _popen_pipes(ctx, cmd_, cwd_):
        def _always_strings(ctx, env_dict):
            """
            On Windows and Python 2, environment dictionaries must be strings
            and not unicode.
            """
            if ctx.obj['is_windows']:
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
            env=_always_strings(
                ctx,
                dict(
                    os.environ,
                    # try to disable i18n
                    LC_ALL='C',
                    LANGUAGE='',
                    HGPLAIN='1',
                )
            )
        )

    def _ensure_stripped_str(ctx, str_or_bytes):
        if isinstance(str_or_bytes, str):
            return '\n'.join(str_or_bytes.strip().splitlines())
        else:
            return '\n'.join(str_or_bytes.decode('utf-8', 'surogate_escape').strip().splitlines())

    cmd.insert(0, find_executable(cmd.pop(0)))
    click.secho(f'{cmd}', nl=False, fg='magenta')
    p = _popen_pipes(ctx, cmd, cwd)
    out, err = p.communicate()
    click.secho(f' -> {p.returncode}', fg='magenta')
    return _ensure_stripped_str(ctx, out), _ensure_stripped_str(ctx, err), p.returncode


def do(ctx, cmd, cwd='.'):
    if not isinstance(cmd, (list, tuple)):
        cmd = shlex.split(cmd)

    # click.secho(f'running: {cmd}', nl=False, fg='magenta')

    out, err, ret = do_ex(ctx, cmd, cwd)
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


def get_pep440_version(version) -> str:
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

    semver = semantic_version.Version.coerce(version)
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
    def pylint(ctx):
        do(ctx, ['pylint'])

    @staticmethod
    def prospector(ctx):
        do(ctx, ['prospector'])

    @staticmethod
    def pytest(ctx):
        do(ctx, ['pytest'])

    @staticmethod
    def flake8(ctx):
        do(ctx, ['flake8'])

    @staticmethod
    def safety(ctx):
        do(ctx, ['safety', 'check', '--bare'])


class HouseKeeping:
    SRC_FILE = 'temp'

    @classmethod
    def _write_requirements(cls, ctx, packages_list, outfile, prefix_list=None):
        with open(cls.SRC_FILE, 'w') as source_file:
            source_file.write('\n'.join(packages_list))
        packages, _, ret = do_ex(
            ctx,
            [
                'pip-compile',
                '--index',
                '--upgrade',
                '--annotate',
                '--no-header',
                '-n',
                cls.SRC_FILE
            ]
        )
        os.remove(cls.SRC_FILE)
        with open(outfile, 'w') as req_file:
            if prefix_list:
                for prefix in prefix_list:
                    req_file.write(f'{prefix}\n')
            for package in packages.splitlines():
                req_file.write(f'{package}\n')

    @classmethod
    def write_prod(cls, ctx):
        sys.path.insert(0, os.path.abspath('.'))
        from setup import install_requires
        cls._write_requirements(
            ctx,
            packages_list=install_requires,
            outfile='requirements.txt'
        )
        sys.path.pop(0)

    @classmethod
    def write_test(cls, ctx):
        from setup import test_requires
        cls._write_requirements(
            ctx,
            packages_list=test_requires,
            outfile='requirements-test.txt',
            prefix_list=['-r requirements.txt']
        )

    @classmethod
    def write_dev(cls, ctx):
        from setup import dev_requires
        cls._write_requirements(
            ctx,
            packages_list=dev_requires,
            outfile='requirements-dev.txt',
            prefix_list=['-r requirements.txt', '-r requirements-test.txt']
        )

    @classmethod
    def write_requirements(cls, ctx):
        cls.write_prod(ctx)
        cls.write_test(ctx)
        cls.write_dev(ctx)

    @classmethod
    def write_changelog(cls, ctx, commit: bool, push: bool = False):
        changelog = do(ctx, ['gitchangelog', '0.4.1..HEAD'])
        with open('CHANGELOG.rst', mode='w') as f:
            f.write(re.sub('(\s*\r\n){2,}', '\r\n', changelog))
        if commit:
            do_ex(ctx, ['git', 'add', 'CHANGELOG.rst'])
            _, _, ret = do_ex(ctx, ['git', 'commit', '-m', 'chg: dev: updated changelog [skip ci]'])
            if ret == 0 and push:
                do_ex(ctx, ['git', 'push'])

    @classmethod
    def compile_qt_resources(cls, ctx):
        do(ctx, [
            'pyrcc5',
            './emft/ui/qt_resource.qrc',
            '-o', './emft/ui/qt_resource.py',
        ])

    @classmethod
    def write_version(cls, ctx):
        with open('./emft/__version_frozen__.py', 'w') as version_file:
            version_file.write(
                f"# coding=utf-8\n"
                f'__version__ = \'{ctx.obj["semver"]}\'\n'
                f'__pep440__ = \'{ctx.obj["pep440"]}\'\n')


class Make:
    @classmethod
    def install_pyinstaller(cls, ctx):
        do(ctx, ['pip', 'install',
                 'git+https://github.com/132nd-etcher/pyinstaller.git@develop#egg=pyinstaller==3.3.dev0+g2fcbe0f'])

    @classmethod
    def freeze(cls, ctx):
        do(ctx, [
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
    def patch_exe(cls, ctx):
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
        do(ctx, [
            'verpatch',
            './dist/EMFT.exe',
            '/high',
            ctx.obj['semver'],
            '/va',
            '/pv', ctx.obj['semver'],
            '/s', 'desc', 'EtchersMissionFilesTools',
            '/s', 'product', 'EMFT',
            '/s', 'title', 'EMFT',
            '/s', 'copyright', f'{year}-132nd-etcher',
            '/s', 'company', '132nd-etcher,132nd-Entropy,132nd-Neck',
            '/s', 'SpecialBuild', f'{ctx.obj["version"]["BranchName"]}@{ctx.obj["version"]["Sha"]}',
            '/s', 'PrivateBuild', f'{ctx.obj["version"]["InformationalVersion"]}.{ctx.obj["version"]["CommitDate"]}',
            '/langid', '1033',
        ])

    @classmethod
    def build_doc(cls, ctx):
        do(ctx, [
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
    if not os.path.exists('.git') or not os.path.exists('emft'):
        click.secho('emft-build is meant to be ran in EMFT Git repository.\n'
                    'You can clone the repository by running:\n\n'
                    '\tgit clone https://github.com/132nd-etcher/EMFT.git\n\n'
                    'Then cd into it and try again.',
                    fg='red', err=True)
        exit(-1)
    if not hasattr(ctx, 'obj') or ctx.obj is None:
        ctx.obj = {}

    ctx.obj['is_windows'] = platform.system() == 'Windows'
    ctx.obj['version'] = get_gitversion()
    ctx.obj['semver'] = ctx.obj['version'].get("FullSemVer")
    ctx.obj['pep440'] = get_pep440_version(ctx.obj['semver'])

    click.secho(f"SemVer: {ctx.obj['semver']}", fg='green')

    if not all(
        (
            os.path.exists('requirements.txt'),
            os.path.exists('requirements-dev.txt'),
            os.path.exists('requirements-test.txt'),
        )
    ):
        HouseKeeping.write_requirements(ctx)

    if install:
        do(ctx, ['pip', 'install', '-r', 'requirements-dev.txt'])
    if ctx.invoked_subcommand is None:
        Checks.safety(ctx)
        Checks.flake8(ctx)
        Checks.pytest(ctx)
        # Checks.pylint()  # TODO
        # Checks.prospector()  # TODO
        HouseKeeping.compile_qt_resources(ctx)
        HouseKeeping.write_changelog(ctx, commit=True)
        HouseKeeping.write_requirements(ctx)
        Make.install_pyinstaller(ctx)
        Make.freeze(ctx)
        Make.patch_exe(ctx)
        Make.build_doc(ctx)


@cli.command()
@click.option('--prod/--no-prod', default=True)
@click.option('--test/--no-test', default=True)
@click.option('--dev/--no-dev', default=True)
@click.pass_context
def reqs(ctx, prod, test, dev):
    if prod:
        HouseKeeping.write_prod(ctx)
    if test:
        HouseKeeping.write_test(ctx)
    if dev:
        HouseKeeping.write_dev(ctx)


@cli.command()
@click.pass_context
def version(ctx):
    HouseKeeping.write_version(ctx)


@cli.command()
@click.option('--commit/--no-commit', default=True)
@click.pass_context
def chglog(ctx, commit):
    HouseKeeping.write_changelog(ctx, commit)


@cli.command()
@click.pass_context
def pyrcc(ctx):
    HouseKeeping.compile_qt_resources(ctx)


@cli.command()
@click.pass_context
def pytest(ctx):
    Checks.pytest(ctx)


@cli.command()
@click.pass_context
def flake8(ctx):
    Checks.flake8(ctx)


@cli.command()
@click.pass_context
def prospector(ctx):
    Checks.prospector(ctx)


@cli.command()
@click.pass_context
def pylint(ctx):
    Checks.pylint(ctx)


@cli.command()
@click.pass_context
def safety(ctx):
    Checks.safety(ctx)


@cli.command()
@click.pass_context
def doc(ctx):
    Make.build_doc(ctx)


@cli.command()
@click.option('--install/--no-install', default=True)
@click.pass_context
def freeze(ctx, install):
    if install:
        Make.install_pyinstaller(ctx)
    Make.freeze(ctx)


@cli.command()
@click.pass_context
def patch(ctx):
    Make.patch_exe(ctx)


if __name__ == '__main__':
    cli(obj={})

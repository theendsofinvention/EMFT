# coding=utf-8
"""
Collections of tools to build EMFT
"""
import datetime
import importlib
import os
import re
import shlex
import subprocess
import sys
import typing
from json import loads

import certifi
import click

# noinspection SpellCheckingInspection
PYINSTALLER_NEEDED_VERSION = '3.3.dev0+g2fcbe0f'


def ensure_repo():
    """
    Makes sure the current working directory is EMFT's Git repository.
    """
    if not os.path.exists('.git') or not os.path.exists('emft'):
        click.secho('emft-build is meant to be ran in EMFT Git repository.\n'
                    'You can clone the repository by running:\n\n'
                    '\tgit clone https://github.com/132nd-etcher/EMFT.git\n\n'
                    'Then cd into it and try again.',
                    fg='red', err=True)
        exit(-1)


def ensure_module(module_name: str):
    """
    Makes sure that a module is importable.

    In case the module cannot be found, print an error and exit.

    Args:
        module_name: name of the module to look for
    """
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError:
        click.secho(
            f'Module not found: {module_name}\n'
            f'Install it manually with: "pip install {module_name}"\n'
            f'Or install all dependencies with: "pip install -r requirements-dev.txt"',
            fg='red', err=True)
        exit(-1)


def find_executable(executable: str, path: str = None) -> typing.Union[str, None]:  # noqa: C901
    # noinspection SpellCheckingInspection
    """
    https://gist.github.com/4368898

    Public domain code by anatoly techtonik <techtonik@gmail.com>

    Programmatic equivalent to Linux `which` and Windows `where`

    Find if ´executable´ can be run. Looks for it in 'path'
    (string that lists directories separated by 'os.pathsep';
    defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.

    Args:
        executable: executable name to look for
        path: root path to examine (defaults to system PATH)

    """

    if not executable.endswith('.exe'):
        executable = f'{executable}.exe'

    if executable in find_executable.known_executables:  # type: ignore
        return find_executable.known_executables[executable]  # type: ignore

    click.secho(f'looking for executable: {executable}', fg='green', nl=False)

    if path is None:
        path = os.environ['PATH']
    paths = [os.path.abspath(os.path.join(sys.exec_prefix, 'Scripts'))] + path.split(os.pathsep)
    if os.path.isfile(executable):
        executable_path = os.path.abspath(executable)
    else:
        for path_ in paths:
            executable_path = os.path.join(path_, executable)
            if os.path.isfile(executable_path):
                break
        else:
            click.secho(f' -> not found', fg='red', err=True)
            return None

    find_executable.known_executables[executable] = executable_path  # type: ignore
    click.secho(f' -> {click.format_filename(executable_path)}', fg='green')
    return executable_path


find_executable.known_executables = {}  # type: ignore


def do_ex(ctx: click.Context, cmd: typing.List[str], cwd: str = '.') -> typing.Tuple[str, str, int]:
    """
    Executes a given command

    Args:
        ctx: Click context
        cmd: command to run
        cwd: working directory (defaults to ".")

    Returns: stdout, stderr, exit_code

    """

    def _popen_pipes(ctx_, cmd_, cwd_):
        def _always_strings(ctx__, env_dict):
            """
            On Windows and Python 2, environment dictionaries must be strings
            and not unicode.
            """
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
                ctx_,
                dict(
                    os.environ,
                    # try to disable i18n
                    LC_ALL='C',
                    LANGUAGE='',
                    HGPLAIN='1',
                )
            )
        )

    def _ensure_stripped_str(_, str_or_bytes):
        if isinstance(str_or_bytes, str):
            return '\n'.join(str_or_bytes.strip().splitlines())
        else:
            return '\n'.join(str_or_bytes.decode('utf-8', 'surogate_escape').strip().splitlines())

    exe = find_executable(cmd.pop(0))
    if not exe:
        exit(-1)
    cmd.insert(0, exe)
    click.secho(f'{cmd}', nl=False, fg='magenta')
    p = _popen_pipes(ctx, cmd, cwd)
    out, err = p.communicate()
    click.secho(f' -> {p.returncode}', fg='magenta')
    return _ensure_stripped_str(ctx, out), _ensure_stripped_str(ctx, err), p.returncode


def do(ctx: click.Context, cmd: typing.List[str], cwd: str = '.') -> str:
    """
    Executes a command and returns the result

    Args:
        ctx: click context
        cmd: command to execute
        cwd: working directory (defaults to ".")

    Returns: stdout
    """
    if not isinstance(cmd, (list, tuple)):
        cmd = shlex.split(cmd)

    out, err, ret = do_ex(ctx, cmd, cwd)
    if out:
        click.secho(f'{out}', fg='cyan')
    if err:
        click.secho(f'{err}', fg='red')
    if ret:
        click.secho(f'command failed: {cmd}', err=True, fg='red')
        exit(ret)
    return out


def get_gitversion() -> dict:
    """
    Uses GitVersion (https://github.com/GitTools/GitVersion) to infer project's current version

    Returns Gitversion JSON output as a dict
    """
    if os.environ.get('APPVEYOR'):
        exe = find_executable('gitversion', r'C:\ProgramData\chocolatey\bin')
    else:
        exe = find_executable('gitversion')
    if not exe:
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
        exit(-1)
    return loads(subprocess.getoutput([exe]).rstrip())


def get_pep440_version(version: str) -> str:
    """
    Converts a Semver to a PEP440 version

    Args:
        version: valid Semver string

    Returns: valid PEP440 version
    """
    import semantic_version

    convert_prereleases = {
        'alpha': 'a',
        'beta': 'b',
        'exp': 'rc',
        'patch': 'post',
    }

    semver = semantic_version.Version.coerce(version)
    version_str = f'{semver.major}.{semver.minor}.{semver.patch}'
    prerelease = semver.prerelease

    # Pre-release
    if prerelease:
        assert isinstance(prerelease, tuple)

        # Convert the pre-release tag to a valid PEP440 tag and strip it
        if prerelease[0] in convert_prereleases:
            version_str += convert_prereleases[prerelease[0]]
            prerelease = prerelease[1:]
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


def _write_requirements(ctx: click.Context, packages_list, outfile, prefix_list=None):
    with open('temp', 'w') as source_file:
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
            'temp'
        ]
    )
    os.remove('temp')
    with open(outfile, 'w') as req_file:
        if prefix_list:
            for prefix in prefix_list:
                req_file.write(f'{prefix}\n')
        for package in packages.splitlines():
            req_file.write(f'{package}\n')


def _install_pyinstaller(ctx: click.Context, force: bool = False):
    """
    Installs pyinstaller package from a custom repository

    The latest official master branch of Pyinstaller does not work with the version of Python I'm using at this time

    Args:
        ctx: lick context (passed automatically by Click)
        force: uses "pip --upgrade" to force the installation of this specific version of PyInstaller
    """
    repo = r'git+https://github.com/132nd-etcher/pyinstaller.git@develop#egg=pyinstaller==3.3.dev0+g2fcbe0f'
    if force:
        do(ctx, ['pip', 'install', '--upgrade', repo])
    else:
        do(ctx, ['pip', 'install', repo])


def _get_version(ctx: click.Context):
    if not hasattr(ctx, 'obj') or ctx.obj is None:
        ctx.obj = {}

    try:
        from emft.__version_frozen__ import __version__, __pep440__
        ctx.obj['semver'] = __version__
        ctx.obj['pep440'] = __pep440__
    except ModuleNotFoundError:
        ctx.invoke(pin_version)

    click.secho(f"Semver: {ctx.obj['semver']}", fg='green')
    click.secho(f"PEP440: {ctx.obj['pep440']}", fg='green')


# noinspection PyUnusedLocal
def _print_version(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing:
        return

    ensure_repo()

    _get_version(ctx)
    exit(0)


# @click.group(invoke_without_command=True)
@click.group(chain=True)
@click.option('-v', '--version',
              is_flag=True, is_eager=True, expose_value=False, callback=_print_version, default=False,
              help='Print version and exit')
@click.pass_context
def cli(ctx):
    """
    Handles all the tasks to build a working EMFT application

    This tool is installed as a setuptools entry point, which means it should be accessible from your terminal once EMFT
    is installed in develop mode.

    Just type the following in whatever shell you fancy:
    """

    ensure_repo()

    _get_version(ctx)

    # if ctx.invoked_subcommand is None:
    #     Checks.safety(ctx)
    #     Checks.flake8(ctx)
    #     Checks.pytest(ctx)
    #     # Checks.pylint()  # TODO
    #     # Checks.prospector()  # TODO
    #     HouseKeeping.compile_qt_resources(ctx)
    #     HouseKeeping.write_changelog(ctx, commit=True)
    #     HouseKeeping.write_requirements(ctx)
    #     Make.install_pyinstaller(ctx)
    #     Make.freeze(ctx)
    #     Make.patch_exe(ctx)
    #     Make.build_doc(ctx)


@cli.command()
@click.option('--prod/--no-prod', default=True, help='Whether or not to write "requirement.txt"')
@click.option('--test/--no-test', default=True, help='Whether or not to write "requirement-test.txt"')
@click.option('--dev/--no-dev', default=True, help='Whether or not to write "requirement-dev.txt"')
@click.pass_context
def reqs(ctx: click.Context, prod, test, dev):
    """Write requirements files"""
    if not find_executable('pip-compile'):
        click.secho('Missing module "pip-tools".\n'
                    'Install it manually with: "pip install pip-tools"\n'
                    'Or install all dependencies with: "pip install -r requirements-dev.txt"',
                    err=True, fg='red')
        exit(-1)
    if prod:
        sys.path.insert(0, os.path.abspath('.'))
        from setup import install_requires
        _write_requirements(
            ctx,
            packages_list=install_requires,
            outfile='requirements.txt'
        )
        sys.path.pop(0)
    if test:
        """Writes requirements-test.txt"""
        from setup import test_requires
        _write_requirements(
            ctx,
            packages_list=test_requires,
            outfile='requirements-test.txt',
            prefix_list=['-r requirements.txt']
        )
    if dev:
        """Writes requirements-dev.txt"""
        from setup import dev_requires
        _write_requirements(
            ctx,
            packages_list=dev_requires,
            outfile='requirements-dev.txt',
            prefix_list=['-r requirements.txt', '-r requirements-test.txt']
        )


@cli.command()
@click.pass_context
def pin_version(ctx):
    """
    Writes the project's version to "emft/__version_frozen__.py (both Semver and PEP440)

    Args:
        ctx: click context (passed automatically by Click)
    """
    ensure_module('semantic_version')

    ctx.obj['version'] = get_gitversion()  # this is needed for later patching
    ctx.obj['semver'] = ctx.obj['version'].get("FullSemVer")
    ctx.obj['pep440'] = get_pep440_version(ctx.obj['semver'])

    with open('./emft/__version_frozen__.py', 'w') as version_file:
        version_file.write(
            f"# coding=utf-8\n"
            f'__version__ = \'{ctx.obj["semver"]}\'\n'
            f'__pep440__ = \'{ctx.obj["pep440"]}\'\n')


@cli.command()
@click.option('--commit/--no-commit', default=True, help='commit the changes (default: True)')
@click.option('--push/--no-push', default=False, help='push the changes (default: False)')
@click.pass_context
def chglog(ctx, commit, push):
    """Write changelog"""
    ensure_module('gitchangelog')
    find_executable('git')
    """
    Write the changelog using "gitchangelog" (https://github.com/vaab/gitchangelog)
    """
    changelog = do(ctx, ['gitchangelog', '0.4.1..HEAD'])
    with open('CHANGELOG.rst', mode='w') as f:
        f.write(re.sub(r'(\s*\r\n){2,}', '\r\n', changelog))
    if commit:
        do_ex(ctx, ['git', 'add', 'CHANGELOG.rst'])
        _, _, ret = do_ex(ctx, ['git', 'commit', '-m', 'chg: dev: updated changelog [skip ci]'])
        if ret == 0 and push:
            do_ex(ctx, ['git', 'push'])


@cli.command()
@click.pass_context
def pyrcc(ctx):
    """Compiles Qt resources (icons, pictures, ...)  to a usable python script"""
    if not find_executable('pyrcc5'):
        click.secho('Unable to find "pyrcc5" executable.\n'
                    f'Install it manually with: "pip install pyqt5"\n'
                    f'Or install all dependencies with: "pip install -r requirements-dev.txt"',
                    err=True, fg='red'
                    )
    do(ctx, [
        'pyrcc5',
        './emft/ui/qt_resource.qrc',
        '-o', './emft/ui/qt_resource.py',
    ])


@cli.command()
@click.pass_context
def pytest(ctx):
    """
    Runs Pytest (https://docs.pytest.org/en/latest/)
    """
    ensure_module('pytest')
    do(ctx, ['pytest'])


@cli.command()
@click.pass_context
def flake8(ctx):
    """
    Runs Flake8 (http://flake8.pycqa.org/en/latest/)
    """
    ensure_module('flake8')
    do(ctx, ['flake8'])


@cli.command()
@click.pass_context
def prospector(ctx):
    """
    Runs Landscape.io's Prospector (https://github.com/landscapeio/prospector)

    This includes flake8 & Pylint
    """
    ensure_module('prospector')
    do(ctx, ['prospector'])


@cli.command()
@click.pass_context
@click.argument('src', type=click.Path(exists=True), default='emft')
@click.option('-r', '--reports', is_flag=True, help='Display full report')
@click.option('-f', '--format', 'format_',
              type=click.Choice(['text', 'parseable', 'colorized', 'json']), default='colorized')
def pylint(ctx, src, reports, format_):
    """
    Analyze a given python SRC (module or package) with Pylint (SRC must exist)

    Default module: "./emft"
    """
    ensure_module('pylint')
    cmd = ['pylint', src, f'--output-format={format_}']
    if reports:
        cmd.append('--reports=y')
    do(ctx, cmd)


@cli.command()
@click.pass_context
def safety(ctx):
    """
    Runs Pyup's Safety tool (https://pyup.io/safety/)
    """
    ensure_module('safety')
    do(ctx, ['safety', 'check', '--bare'])


@cli.command()
@click.pass_context
def doc(ctx):
    """
    Builds the documentation using Sphinx (http://www.sphinx-doc.org/en/stable)
    """
    do(ctx, [
        'sphinx-build',
        '-b',
        'html',
        'doc',
        'doc/html'
    ])


@cli.command()
@click.option('--install/--no-install', default=True, help='automatically install custom Pyinstaller version')
@click.option('--force', is_flag=True, help='force installation of needed version')
@click.pass_context
def freeze(ctx, install: bool, force: bool):
    """
    Creates a Win32 executable file from EMFT's source
    """
    if install:
        _install_pyinstaller(ctx, force)

    pyinstaller_version, _, _ = do_ex(ctx, [sys.executable, '-m', 'PyInstaller', '--version'])
    pyinstaller_version = pyinstaller_version.strip()

    click.secho(f'current version of pyinstaller: {pyinstaller_version}', fg='green')
    # noinspection SpellCheckingInspection
    if not pyinstaller_version.strip() in (PYINSTALLER_NEEDED_VERSION, f'{PYINSTALLER_NEEDED_VERSION}0'):
        click.secho('EMFT needs a very specific version of PyInstaller to compile successfully.\n'
                    'You can force the installation of that version using the command:\n\n'
                    '\temft-build freeze --force', err=True, fg='red')
        exit(-1)

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


@cli.command()
@click.pass_context
def patch(ctx):
    """
    Uses "verpatch" (https://ddverpatch.codeplex.com) to write resource information into the PE
    """
    if not find_executable('verpatch'):
        click.secho(
            '"verpatch.exe" not been found in your PATH.\n'
            'Verpatch is used to embed resources like the version after the compilation.\n'
            'I\'m waiting on PyInstaller to port their own resources patcher to Python 3 so I can remove the '
            'dependency to this external tool...\n'
            'In the meanwhile, "verpatch" can be obtained at: https://ddverpatch.codeplex.com/releases',
            err=True, fg='red'
        )
        exit(-1)

    if ctx.obj.get('version') is None:
        ctx.invoke(pin_version)

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


@cli.command()
@click.pass_context
def test_build(ctx):
    """
    Runs the embedded tests in the resulting EMFT.exe
    """
    do(ctx, ['./dist/emft.exe', '--test'])


if __name__ == '__main__':
    cli(obj={})

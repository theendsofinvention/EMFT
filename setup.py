# coding=utf-8

import os

from setuptools import setup


def read_local_files(*file_paths: str) -> str:
    """
    Reads one or more text files and returns them joined together.

    A title is automatically created based on the file name.

    :param file_paths: list of files to aggregate

    """

    def _read_single_file(file_path):
        with open(file_path) as f:
            filename = os.path.splitext(file_path)[0]
            title = f'{filename}\n{"=" * len(filename)}'
            return '\n\n'.join((title, f.read()))

    return '\n' + '\n\n'.join(map(_read_single_file, file_paths))


dependency_links = [r'https://github.com/tomp/python-metar.git']

# noinspection SpellCheckingInspection
install_requires = [
    'pyinstrument',
    'semantic_version',
    'colorama',
    'transitions',
    'click',
    'certifi',
    'humanize',
    'mpmath',
    'natsort',
    'path.py',
    'pefile',
    'polycircles',
    'pyqt5',
    'raven',
    'requests',
    'ruamel.yaml',
    'simplekml',
    'urllib3<1.23,>=1.21.1',  # Specific from requests
    'pytaf',
    'metar',
    'pendulum',
]

# noinspection SpellCheckingInspection
test_requires = [
    'pytest',
    'coverage',
    'httmock',
    'hypothesis',
    'pytest-cache',
    'pytest-catchlog',
    'pytest-cov',
    'pytest-mock',
    'pytest-pep8',
    'pytest-pycharm',
    'pytest-qt',
    'datadiff',
]

dev_requires = [
    'pylint',
    'flake8',
    'prospector',
    'safety',
    'sphinx',
    'gitchangelog',
    'certifi',
    'pip-tools',
    'sphinx_autodoc_typehints',
    'sphinx-click',
    'sphinx-git',
    'sphinxjp.themes.basicstrap',
]

setup_requires = [
    'setuptools_scm',
    'pytest-runner',
]

entry_points = '''
[console_scripts]
emft=emft.main:main
emft-build=emft.build:cli
'''

if __name__ == '__main__':
    setup(
        name='EMFT',
        author='132nd-etcher',
        zip_safe=False,
        author_email='emft@daribouca.net',
        platforms=['win32'],
        url=r'https://github.com/132nd-etcher/EMFT',
        download_url=r'https://github.com/132nd-etcher/EMFT/releases',
        description='Set of tools for the DCS mission builder',
        license='GPLv3',
        py_modules=['emft'],
        long_description=read_local_files('README.rst', 'CHANGELOG.rst'),
        packages=['emft'],
        include_package_data=True,
        install_requires=install_requires,
        entry_points=entry_points,
        tests_require=test_requires,
        use_scm_version=True,
        setup_requires=setup_requires,
        dependency_links=dependency_links,
        python_requires='>=3.6',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Topic :: Utilities',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Environment :: Win32 (MS Windows)',
            'Natural Language :: English',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Microsoft :: Windows :: Windows 7',
            'Operating System :: Microsoft :: Windows :: Windows 8',
            'Operating System :: Microsoft :: Windows :: Windows 8.1',
            'Operating System :: Microsoft :: Windows :: Windows 10',
            'Programming Language :: Cython',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: Implementation',
            'Programming Language :: Python :: Implementation :: CPython',
            'Topic :: Games/Entertainment',
            'Topic :: Utilities',
        ],
    )

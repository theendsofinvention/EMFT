# coding=utf-8

# coding=utf-8

from setuptools import setup

install_requires = [
    'click',
    'certifi',
    'humanize',
    'mpmath',
    'natsort',
    'path.py',
    'pefile',
    'polycircles',
    'PyQt5',
    'raven',
    'requests',
    'ruamel.yaml',
    'semver',
    'simplekml',
    'urllib3',
]

test_requires = [
    'pytest',
    'pytest-cache',
    'pytest-catchlog',
    'pytest-cov',
    'pytest-mock',
    'pytest-pep8',
    'pytest-pycharm',
    'pytest-qt',
    'pytest-runner',
    'coverage',
    'mock',
    'httmock',
    'hypothesis',
]

setup_requires = [
    'pytest-runner',
    'setuptools_scm',
]

entry_points = '''
[console_scripts]
convert=src.main:main
'''

setup(
    name='convert',
    use_scm_version=True,
    py_modules=['src'],
    install_requires=install_requires,
    entry_points=entry_points,
    tests_require=test_requires,
    setup_requires=setup_requires,
    test_suite='pytest -c ./test/.pytest',
)

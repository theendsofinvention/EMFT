# coding=utf-8

import pip


if __name__ == '__main__':
    pip.main(['install', '-U', '--no-deps', 'git+file://f:/dev/utils@develop'])
    pip.main(['install', '-U', '--no-deps', 'git+file://f:/dev/sltp@develop'])
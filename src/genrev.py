# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

# native
from os import path

__all__ = ()

CWD = path.abspath(path.curdir).replace('\\', '/')
APP_REV_FILE_PATH = f'{CWD}/src/version.py'
STR_APP_REVISION = 'APP_REVISION = \''

UTF8 = 'utf-8'


def write_revision_date() -> None:
    with open(APP_REV_FILE_PATH, 'r+', encoding=UTF8) as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            if line.startswith(STR_APP_REVISION):
                revision = line[line.find('\'') + 1:line.rfind('\'')]
                lines[idx] = f'{STR_APP_REVISION}{int(revision) + 1:d}\'\n'
                break
        f.flush()
        f.seek(0)
        f.truncate()
        f.writelines(lines)


if __name__ == '__main__':
    write_revision_date()

#
#
#########################################

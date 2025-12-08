# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

# native
import os

__all__ = ()

CWD = os.path.abspath(os.path.curdir).replace('\\', '/')
APP_REV_FILE_PATH = f'{CWD}/src/version.py'
STR_APP_REVISION = 'APP_REVISION = \''
PYPROJECT_TOML_FILE_PATH = f'{CWD}/pyproject.toml'
STR_TOML_VERSION = 'version = \''

UTF8 = 'utf-8'


class Version:
    revision: int = 0


def write_revision_date() -> None:
    with open(APP_REV_FILE_PATH, 'r+', encoding=UTF8, newline='\n') as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            if line.startswith(STR_APP_REVISION):
                revision = line[line.find('\'') + 1:line.rfind('\'')]
                Version.revision = int(revision) + 1
                lines[idx] = f'{STR_APP_REVISION}{Version.revision:d}\'\n'
                break
        f.flush()
        f.seek(0)
        f.truncate()
        f.writelines(lines)


def write_revision_date_toml() -> None:
    assert Version.revision
    with open(PYPROJECT_TOML_FILE_PATH, 'r+', encoding=UTF8, newline='\n') as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            if line.startswith(STR_TOML_VERSION):
                first_idx = line.rfind('.') + 1
                last_idx = line.find('\'', first_idx + 1)
                while last_idx > 0 and not line[last_idx - 1].isnumeric():
                    last_idx -= 1
                lines[idx] = f'{line[:first_idx]}{Version.revision:d}{line[last_idx:]}'
                break
        f.flush()
        f.seek(0)
        f.truncate()
        f.writelines(lines)


if __name__ == '__main__':
    write_revision_date()
    write_revision_date_toml()


#
#
#########################################

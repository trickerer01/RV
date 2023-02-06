# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, listdir
from re import match
from typing import Set

from defs import ExtraConfig, Log, normalize_path, re_rvfile

__all__ = ('scan_dest_folder', 'file_exists_in_folder')

found_filenames_base = set()  # type: Set[str]
found_filenames_all = set()  # type: Set[str]


def scan_dest_folder() -> None:
    global found_filenames_base
    global found_filenames_all

    if path.exists(ExtraConfig.dest_base):
        Log.info('Scanning dest folder...')
        subfolders = list()
        cur_names = listdir(ExtraConfig.dest_base)
        for idx_c in reversed(range(len(cur_names))):
            fullpath_c = f'{ExtraConfig.dest_base}{cur_names[idx_c]}'
            if path.isdir(fullpath_c):
                subfolders.append(normalize_path(fullpath_c))
                del cur_names[idx_c]
            elif path.isfile(fullpath_c):
                found_filenames_all.add(cur_names[idx_c])
        found_filenames_base = cur_names
        for subfolder in subfolders:
            for sub_name in listdir(subfolder):
                fullpath_s = f'{subfolder}{sub_name}'
                if path.isfile(fullpath_s):
                    found_filenames_all.add(sub_name)
        Log.info(f'Found {len(found_filenames_base):d} files in base and '
                 f'{len(found_filenames_all) - len(found_filenames_base):d} files in {len(subfolders):d} subfolders '
                 f'(total files: {len(found_filenames_all):d})')


def file_exists_in_folder(base_folder: str, idi: int, quality: str, check_subfolders: bool) -> bool:
    if path.exists(base_folder):
        for fname in sorted(found_filenames_all if check_subfolders else found_filenames_base):
            try:
                f_match = match(re_rvfile, fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if str(idi) == f_id and quality == f_quality:
                    return True
            except Exception:
                continue
    return False

#
#
#########################################

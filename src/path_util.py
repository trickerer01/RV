# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, listdir
from re import match
from typing import Set, List, Optional

from defs import ExtraConfig, Log, normalize_path, re_rvfile, prefixp
from scenario import DownloadScenario

__all__ = ('file_exists_in_folder', 'prefilter_existing_items', 'scan_dest_folder')

found_filenames_base = set()  # type: Set[str]
found_filenames_all = set()  # type: Set[str]


def scan_dest_folder() -> None:
    """
    Scans base destination folder plus one level of subfolders and
    stores found files in two lists: one for base folder and another for all scanned folders\n\n
    |folder1:\n\n
    |__subfolder1:\n\n
    |____file2\n\n
    |__file1\n\n
    => files1 = ['file1'], files2 = ['file1','file2']\n\n
    This function may only be called once!
    """
    global found_filenames_base
    global found_filenames_all

    assert len(found_filenames_all) == 0
    if path.isdir(ExtraConfig.dest_base):
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
    if path.isdir(base_folder):
        for fname in sorted(found_filenames_all if check_subfolders else found_filenames_base):
            try:
                f_match = match(re_rvfile, fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if str(idi) == f_id and (quality is None or quality == f_quality):
                    return True
            except Exception:
                continue
    return False


def prefilter_existing_items(id_sequence: List[int], scenario: Optional[DownloadScenario]) -> List[int]:
    """
    This function filters out existing items with desired quality\n\n
    (which may sometimes be inaccessible).\n\n
    This function may only be called once!
    """
    removed_ids = list()
    for id_ in id_sequence:
        file_exists = False
        if scenario:
            for sc in scenario.queries:
                quality = sc.quality
                subfolder = sc.subfolder
                file_exists = file_exists_in_folder(f'{ExtraConfig.dest_base}{subfolder}', id_, quality, True)
                if file_exists:
                    break
        else:
            file_exists = file_exists_in_folder(ExtraConfig.dest_base, id_, ExtraConfig.quality, True)

        if file_exists:
            Log.info(f'Info: {prefixp()}{id_:d}.mp4 found in {ExtraConfig.dest_base} (or subfolder). Skipped.')
            removed_ids.append(id_)

    return removed_ids

#
#
#########################################

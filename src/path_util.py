# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, listdir
from re import match
from typing import List, Optional, Dict

from defs import ExtraConfig, Log, MAX_DEST_SCAN_SUB_DEPTH, normalize_path, re_rvfile, prefixp
from scenario import DownloadScenario

__all__ = ('file_exists_in_folder', 'prefilter_existing_items', 'scan_dest_folder')

found_filenames_dict = dict()  # type: Dict[str, List[str]]


def scan_dest_folder() -> None:
    """
    Scans base destination folder plus {MAX_DEST_SCAN_SUB_DEPTH} levels of subfolders and
    stores found files in dict (key=folder_name)\n\n
    |folder1:\n\n
    |__subfolder1:\n\n
    |____file2\n\n
    |____file3\n\n
    |__file1\n\n
    => files{'folder1': ['file1'], 'subfolder1': ['file2','file3']}\n\n
    This function may only be called once!
    """

    assert len(found_filenames_dict.keys()) == 0
    if path.isdir(ExtraConfig.dest_base):
        Log.info('Scanning dest folder...')

        def scan_folder(base_folder: str, level: int) -> None:
            for cname in listdir(base_folder):
                fullpath = f'{base_folder}{cname}'
                if path.isdir(fullpath):
                    fullpath = normalize_path(fullpath)
                    if level < MAX_DEST_SCAN_SUB_DEPTH:
                        found_filenames_dict[fullpath] = list()
                        scan_folder(fullpath, level + 1)
                elif path.isfile(fullpath):
                    found_filenames_dict[base_folder].append(cname)

        found_filenames_dict[ExtraConfig.dest_base] = list()
        scan_folder(ExtraConfig.dest_base, 0)
        base_files_count = len(found_filenames_dict.get(ExtraConfig.dest_base))
        total_files_count = sum(len(li) for li in found_filenames_dict.values())
        Log.info(f'Found {base_files_count:d} files in base and '
                 f'{total_files_count - base_files_count:d} files in {len(found_filenames_dict.keys()) - 1:d} subfolders '
                 f'(total files: {total_files_count:d}, scan depth: {MAX_DEST_SCAN_SUB_DEPTH:d})')


def file_exists_in_folder(base_folder: str, idi: int, quality: str) -> bool:
    if path.isdir(base_folder):
        orig_file_names = found_filenames_dict.get(normalize_path(base_folder))
        if orig_file_names is not None:
            for fname in orig_file_names:
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
        found_folder = ''
        if scenario:
            for sc in scenario.queries:
                if file_exists_in_folder(f'{ExtraConfig.dest_base}{sc.subfolder}', id_, sc.quality):
                    found_folder = f'{ExtraConfig.dest_base}{sc.subfolder}'
                    break
        else:
            for fullpath in found_filenames_dict.keys():
                if file_exists_in_folder(fullpath, id_, ExtraConfig.quality):
                    found_folder = fullpath
                    break

        if len(found_folder) > 0:
            Log.info(f'Info: {prefixp()}{id_:d}.mp4 found in \'{normalize_path(found_folder)}\'. Skipped.')
            removed_ids.append(id_)

    return removed_ids

#
#
#########################################

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, listdir
from typing import List, Optional, Dict

from defs import ExtraConfig, Log, MAX_DEST_SCAN_SUB_DEPTH, normalize_path, re_media_filename, prefixp
from scenario import DownloadScenario

__all__ = ('file_already_exists', 'prefilter_existing_items', 'scan_dest_folder')

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


def file_exists_in_folder(base_folder: str, idi: int, quality: str) -> str:
    orig_file_names = found_filenames_dict.get(normalize_path(base_folder))
    if path.isdir(base_folder) and orig_file_names is not None:
        for fname in orig_file_names:
            try:
                f_match = re_media_filename.match(fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if str(idi) == f_id and (quality is None or quality == f_quality):
                    return f'{normalize_path(base_folder)}{fname}'
            except Exception:
                continue
    return ''


def file_already_exists(idi: int, quality: str) -> str:
    scenario = ExtraConfig.scenario  # type: Optional[DownloadScenario]
    if scenario:
        for q in scenario.queries:
            fullpath = file_exists_in_folder(f'{ExtraConfig.dest_base}{q.subfolder}', idi, quality or q.quality)
            if len(fullpath) > 0:
                return fullpath
    else:
        for fullpath in found_filenames_dict.keys():
            fullpath = file_exists_in_folder(fullpath, idi, quality or ExtraConfig.quality)
            if len(fullpath) > 0:
                return fullpath
    return ''


def prefilter_existing_items(id_sequence: List[int]) -> List[int]:
    """
    This function filters out existing items with desired quality\n\n
    (which may sometimes be inaccessible).\n\n
    This function may only be called once!
    """
    removed_ids = list()
    for id_ in id_sequence:
        fullpath = file_already_exists(id_, '')
        if len(fullpath) > 0:
            Log.info(f'Info: {prefixp()}{id_:d}.mp4 found in \'{path.split(fullpath)[0]}/\'. Skipped.')
            removed_ids.append(id_)
    return removed_ids

#
#
#########################################

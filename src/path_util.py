# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from collections.abc import MutableSequence

import psutil

from config import Config
from defs import DEFAULT_EXT, PREFIX, Quality
from iinfo import VideoInfo
from logger import Log
from rex import re_media_filename
from util import normalize_path

__all__ = (
    'file_already_exists',
    'file_already_exists_arr',
    'is_file_being_used',
    'prefilter_existing_items',
    'register_new_file',
    'try_rename',
    'unregister_unfinished_file',
)

found_filenames_dict: dict[str, list[str]] = {}
media_matches_cache: dict[str, tuple[str, Quality]] = {}


def report_duplicates() -> None:
    found_vs: dict[str, list[str]] = {}
    fvks: list[str] = []
    for k, filenames in found_filenames_dict.items():
        if not filenames:
            continue
        for fname in filenames:
            if not fname.startswith(PREFIX):
                continue
            fm = re_media_filename.fullmatch(fname)
            if fm:
                fid = fm.group(1)
                if fid not in found_vs:
                    found_vs[fid] = []
                elif fid not in fvks:
                    fvks.append(fid)
                found_vs[fid].append(k + fname)
    if fvks:
        Log.info('Duplicates found:')
        n = '\n  - '
        for kk in fvks:
            Log.info(f' {PREFIX}{kk}.{DEFAULT_EXT}:{n}{n.join(found_vs[kk])}')
    else:
        Log.info('No duplicates found')


def scan_dest_folder() -> None:
    """
    Scans base destination folder plus {Config.folder_scan_depth} levels of subfolders and
    stores found files in dict (key=folder_name)\n
    |folder1:
    |__subfolder1:
    |____file2
    |____file3
    |__file1
    => files{'folder1': ['file1'], 'subfolder1': ['file2','file3']}\n
    This function may only be called once!
    """
    assert len(found_filenames_dict.keys()) == 0
    if os.path.isdir(Config.dest_base) or Config.folder_scan_levelup:
        Log.info('Scanning dest folder...')
        dest_base = Config.dest_base
        scan_depth = Config.folder_scan_depth + Config.folder_scan_levelup
        for _ in range(Config.folder_scan_levelup):
            longpath, dirname = os.path.split(os.path.abspath(dest_base))
            dest_base = normalize_path(longpath)
            if not dirname:
                break

        def scan_folder(base_folder: str, level: int) -> None:
            if os.path.isdir(base_folder):
                with os.scandir(base_folder) as listing:
                    for dentry in listing:
                        fullpath = f'{base_folder}{dentry.name}'
                        if dentry.is_dir():
                            fullpath = normalize_path(fullpath)
                            if level < scan_depth:
                                found_filenames_dict[fullpath] = []
                                scan_folder(fullpath, level + 1)
                        elif dentry.is_file():
                            found_filenames_dict[base_folder].append(dentry.name)

        found_filenames_dict[dest_base] = []
        scan_folder(dest_base, 0)
        if Config.dest_base not in found_filenames_dict:
            found_filenames_dict[Config.dest_base] = []
            scan_folder(Config.dest_base, Config.folder_scan_levelup)
        base_files_count = len(found_filenames_dict[dest_base])
        total_files_count = sum(len(li) for li in found_filenames_dict.values())
        Log.info(f'Found {base_files_count:d} file(s) in base and '
                 f'{total_files_count - base_files_count:d} file(s) in {len(found_filenames_dict.keys()) - 1:d} subfolder(s) '
                 f'(total files: {total_files_count:d}, scan depth: {scan_depth:d})')

    if Config.report_duplicates:
        report_duplicates()


def get_media_file_match(fname: str) -> tuple[str, Quality]:
    if fname not in media_matches_cache:
        f_match = re_media_filename.match(fname)
        f_id, f_quality = (f_match.group(1), Quality(f_match.group(2) or '')) if f_match else ('', '')
        media_matches_cache[fname] = (f_id, f_quality)
    return media_matches_cache[fname]


def register_new_file(vi: VideoInfo) -> None:
    base_folder = vi.my_folder
    if not file_exists_in_folder(base_folder, vi.id, vi.quality, False):
        if found_filenames_dict.get(base_folder) is None:
            found_filenames_dict[base_folder] = [vi.filename]
        else:
            found_filenames_dict[base_folder].append(vi.filename)


def unregister_unfinished_file(vi: VideoInfo) -> None:
    base_folder = vi.my_folder
    if file_exists_in_folder(base_folder, vi.id, vi.quality, False):
        found_filenames_dict[base_folder].remove(vi.filename)


def file_exists_in_folder(base_folder: str, idi: int, quality: Quality, check_folder: bool) -> str:
    orig_file_names = found_filenames_dict.get(base_folder)
    if orig_file_names is not None and (not check_folder or os.path.isdir(base_folder)):
        for fname in orig_file_names:
            f_id, f_quality = get_media_file_match(fname)
            if f_id and str(idi) == f_id and (not quality or not f_quality or quality <= f_quality):
                return f'{normalize_path(base_folder)}{fname}'
    return ''


def file_already_exists(idi: int, quality: Quality | None = None, check_folder=True) -> str:
    for fullpath in found_filenames_dict:
        fullpath = file_exists_in_folder(fullpath, idi, quality or Config.quality, check_folder)
        if len(fullpath) > 0:
            return fullpath
    return ''


def file_exists_in_folder_arr(base_folder: str, idi: int, quality: Quality) -> list[str]:
    orig_file_names = found_filenames_dict.get(base_folder)
    folder_files: list[str] = []
    if orig_file_names is not None and os.path.isdir(base_folder):
        for fname in orig_file_names:
            f_id, f_quality = get_media_file_match(fname)
            if f_id and str(idi) == f_id and (not quality or not f_quality or quality == f_quality):
                folder_files.append(f'{normalize_path(base_folder)}{fname}')
    return folder_files


def file_already_exists_arr(idi: int, quality: Quality) -> list[str]:
    found_files: list[str] = []
    for fullpath in found_filenames_dict:
        found_files.extend(file_exists_in_folder_arr(fullpath, idi, quality or Config.quality))
    return found_files


def prefilter_existing_items(vi_list: MutableSequence[VideoInfo]) -> None:
    """
    This function filters out existing items with desired quality
    (which may sometimes be inaccessible).\n
    This function may only be called once!
    """
    scan_dest_folder()
    if Config.continue_mode:
        return

    i: int
    for i in reversed(range(len(vi_list))):
        if fullpath := file_already_exists(vi_list[i].id, None, False):
            Log.info(f'Info: {vi_list[i].sname} found in \'{os.path.split(fullpath)[0]}/\'. Skipped.')
            del vi_list[i]


def is_file_being_used(filepath: str) -> str:
    """
    :param filepath: Path the to file in question
    :return: Formatted string containing short process identity info or an empty string

    Can only check processes owned by current user unless launched with admin/superuser privileges
    """
    mypid = os.getpid()
    for p in psutil.process_iter():
        try:
            with p.oneshot():
                if p.pid == mypid:
                    continue
                if not (p.name().startswith('python') or os.path.basename(p.exe()).startswith('python')):
                    continue
                user_name = p.username()
                opened_files = p.open_files()
                for fpath in opened_files:
                    if os.path.samefile(filepath, fpath.path):
                        return f'{p.exe()} <{user_name}> (pid: {p.pid:d})'
        except Exception as e:
            if isinstance(e, psutil.Error):
                pass
            else:
                import traceback
                Log.error(f'is_file_being_used(): Error: {traceback.format_exc()}')
    return ''


def try_rename(oldpath: str, newpath: str) -> bool:
    try:
        if oldpath == newpath:
            return True
        newpath_folder = os.path.split(newpath.strip('/'))[0]
        if not os.path.isdir(newpath_folder):
            os.makedirs(newpath_folder)
        os.rename(oldpath, newpath)
        return True
    except Exception:
        return False

#
#
#########################################

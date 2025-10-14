# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from enum import IntEnum

from config import Config
from defs import DEFAULT_EXT, DEFAULT_QUALITY, PREFIX, UTF8, Quality
from logger import Log
from rex import re_infolist_filename
from util import format_time, normalize_filename, normalize_path

__all__ = ('VideoInfo', 'export_video_info', 'get_min_max_ids')


class VideoInfo:  # up to ~3 Kb (when all info is filled, asizeof)
    class State(IntEnum):
        NEW = 0
        QUEUED = 1
        ACTIVE = 2
        SCANNING = 3
        SCANNED = 4
        DOWNLOAD_PENDING = 5
        DOWNLOADING = 6
        WRITING = 7
        DONE = 8
        FAILED = 9

    class Flags(IntEnum):
        NONE = 0x0
        ALREADY_EXISTED_EXACT = 0x1
        ALREADY_EXISTED_SIMILAR = 0x2
        FILE_WAS_CREATED = 0x4
        RETURNED_404 = 0x8

    def __init__(self, m_id: int, m_title='', m_link='', m_subfolder='', m_filename='', m_rating='', m_duration=0) -> None:
        self._id = m_id or 0

        self.title: str = m_title or ''
        self.link: str = m_link or ''
        self.subfolder: str = m_subfolder or ''
        self.filename: str = m_filename or ''
        self.rating: str = m_rating or ''
        self.duration: int = m_duration or 0
        self.quality: Quality = Config.quality or DEFAULT_QUALITY
        self.tags: str = ''
        self.description: str = ''
        self.comments: str = ''
        self.uploader: str = ''
        self.private: bool = False
        self.expected_size: int = 0
        self.bytes_written: int = 0
        self.dstart_time: int = 0
        self.start_size: int = 0
        self.start_time: int = 0
        self.last_check_size: int = 0
        self.last_check_time: int = 0

        self._state = VideoInfo.State.NEW
        self._flags = VideoInfo.Flags.NONE

    def set_state(self, state: VideoInfo.State) -> None:
        self._state = state

    def set_flag(self, flag: VideoInfo.Flags) -> None:
        self._flags |= flag

    def has_flag(self, flag: int | VideoInfo.Flags) -> bool:
        return bool(self._flags & flag)

    def __eq__(self, other: VideoInfo | int) -> bool:
        return self.id == other.id if isinstance(other, type(self)) else self.id == other if isinstance(other, int) else False

    def __str__(self) -> str:
        return (
            f'[{self.state_str}] {self.fduration} \'{PREFIX}{self.id:d}_{self.title}.{DEFAULT_EXT}\' ({self.quality})'
            f'\nDest: \'{self.my_fullpath}\'\nLink: \'{self.link}\''
        )

    @property
    def id(self) -> int:
        return self._id

    @property
    def fduration(self) -> str:
        return f'[{format_time(self.duration)}]'

    @property
    def sname(self) -> str:
        return f'{PREFIX}{self.id:d}.{DEFAULT_EXT}'

    @property
    def sdname(self) -> str:
        return f'{self.fduration} {self.sname}'

    @property
    def sfsname(self) -> str:
        return normalize_filename(self.sname, self.subfolder)

    @property
    def sffilename(self) -> str:
        return normalize_filename(self.filename, self.subfolder)

    @property
    def my_sfolder(self) -> str:
        return normalize_path(self.subfolder)

    @property
    def my_folder(self) -> str:
        return normalize_path(f'{Config.dest_base}{self.subfolder}')

    @property
    def my_fullpath(self) -> str:
        return normalize_filename(self.filename, self.my_folder)

    @property
    def state(self) -> VideoInfo.State:
        return self._state

    @property
    def state_str(self) -> str:
        return self._state.name

    __repr__ = __str__


def get_min_max_ids(seq: Iterable[VideoInfo]) -> tuple[int, int]:
    return min(seq, key=lambda x: x.id).id, max(seq, key=lambda x: x.id).id


def try_merge_info_files(info_dict: dict[int, str], subfolder: str, list_type: str) -> list[str]:
    parsed_files: list[str] = []
    if not Config.merge_lists:
        return parsed_files
    dir_fullpath = normalize_path(f'{Config.dest_base}{subfolder}')
    if not os.path.isdir(dir_fullpath):
        return parsed_files
    # Log.debug(f'\nMerging {Config.dest_base}{subfolder} \'{list_type}\' info lists...')
    info_lists: list[re.Match[str]] = sorted(filter(
        lambda x: bool(x), [re_infolist_filename.fullmatch(f.name) for f in os.scandir(dir_fullpath)
                            if f.is_file() and f.name.startswith(f'{PREFIX}!{list_type}_')],
    ), key=lambda m: m.string)
    if not info_lists:
        return parsed_files
    parsed_dict: dict[int, str] = {}
    for fmatch in info_lists:
        fmname = fmatch.string
        # Log.debug(f'Parsing {fmname}...')
        list_fullpath = f'{dir_fullpath}{fmname}'
        try:
            with open(list_fullpath, 'rt', encoding=UTF8) as listfile:
                last_id = 0
                for line in listfile.readlines():
                    line = line.strip('\ufeff')
                    if line in ('', '\n'):
                        continue
                    if line.startswith(PREFIX):
                        delim_idx = line.find(':')
                        idi = line[len(PREFIX):delim_idx]
                        last_id = int(idi)
                        # Log.debug(f'new id: {last_id:d}{f" (override!)" if last_id in parsed_dict else ""}...')
                        parsed_dict[last_id] = ''
                        if len(line) > delim_idx + 2:
                            parsed_dict[last_id] += line[delim_idx + 2:].strip()
                            # Log.debug(f'at {last_id:d}: (in place) now \'{parsed_dict[last_id]}\'')
                            last_id = 0
                    else:
                        assert last_id
                        if not parsed_dict[last_id]:
                            line = f'\n{line}'
                        parsed_dict[last_id] += line
                        # Log.debug(f'at {last_id:d}: adding \'{line}\'')
                parsed_files.append(list_fullpath)
        except Exception:
            Log.error(f'Error reading from {fmname}. Skipped')
            continue
    for k, v in parsed_dict.items():
        if k not in info_dict:
            info_dict[k] = v
    return parsed_files


def export_video_info(info_list: Iterable[VideoInfo]) -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on video info"""
    tags_dict: dict[str, dict[int, str]] = {}
    desc_dict: dict[str, dict[int, str]] = {}
    comm_dict: dict[str, dict[int, str]] = {}
    for vi in info_list:
        if vi.link:
            for d, s in zip((tags_dict, desc_dict, comm_dict), (vi.tags, vi.description, vi.comments), strict=True):
                if vi.subfolder not in d:
                    d[vi.subfolder] = {}
                d[vi.subfolder][vi.id] = s
    for conf, dct, name, proc_cb in zip(
        (Config.save_tags, Config.save_descriptions, Config.save_comments),
        (tags_dict, desc_dict, comm_dict),
        ('tags', 'descriptions', 'comments'),
        (lambda tags: f' {tags.strip()}\n', lambda description: f'{description}\n', lambda comments: f'{comments}\n'),
        strict=True,
    ):
        if not conf:
            continue
        for subfolder, sdct in dct.items():
            merged_files = try_merge_info_files(sdct, subfolder, name)
            if not sdct:
                continue
            if Config.skip_empty_lists and not any(sdct[idi] for idi in sdct):
                continue
            keys = sorted(sdct.keys())
            min_id, max_id = keys[0], keys[-1]
            info_folder = f'{Config.dest_base}{subfolder}'
            fullpath = f'{normalize_path(info_folder)}{PREFIX}!{name}_{min_id:d}-{max_id:d}.txt'
            if not os.path.isdir(info_folder):
                os.makedirs(info_folder)
            with open(fullpath, 'wt', encoding=UTF8) as sfile:
                sfile.writelines(f'{PREFIX}{idi:d}:{proc_cb(sdct[idi])}' for idi in keys)
            [os.remove(merged_file) for merged_file in merged_files if merged_file != fullpath]

#
#
#########################################

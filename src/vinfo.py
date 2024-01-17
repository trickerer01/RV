# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from enum import IntEnum
from typing import Dict, Iterable, Union, List, Tuple

from config import Config
from defs import PREFIX, UTF8, DEFAULT_QUALITY
from util import normalize_path, normalize_filename

__all__ = ('VideoInfo', 'get_min_max_ids', 'export_video_info')


class VideoInfo:  # up to ~3 Kb (when all info is filled, asizeof)
    class State(IntEnum):
        NEW = 0
        QUEUED = 1
        ACTIVE = 2
        DOWNLOADING = 3
        WRITING = 4
        DONE = 5
        FAILED = 6

    def __init__(self, m_id: int, m_title='', m_link='', m_subfolder='', m_filename='', m_rating='') -> None:
        self.my_id = m_id or 0
        self.my_title = m_title or ''
        self.my_link = m_link or ''
        self.my_subfolder = m_subfolder or ''
        self.my_filename = m_filename or ''
        self.my_rating = m_rating or ''

        self.my_quality = Config.quality or DEFAULT_QUALITY
        self.my_tags = ''
        self.my_description = ''
        self.my_comments = ''
        self.my_expected_size = 0
        self.my_start_size = 0
        self.my_start_time = 0
        self.my_last_check_size = 0
        self.my_last_check_time = 0
        self._state = VideoInfo.State.NEW

    def set_state(self, state: VideoInfo.State) -> None:
        self._state = state

    def __eq__(self, other: Union[VideoInfo, int]) -> bool:
        return self.my_id == other.my_id if isinstance(other, type(self)) else self.my_id == other if isinstance(other, int) else False

    def __repr__(self) -> str:
        return (
            f'[{self.state_str}] \'{PREFIX}{self.my_id:d}_{self.my_title}.mp4\' ({self.my_quality})'
            f'\nDest: \'{self.my_fullpath}\'\nLink: \'{self.my_link}\''
        )

    @property
    def my_sfolder(self) -> str:
        return normalize_path(self.my_subfolder)

    @property
    def my_folder(self) -> str:
        return normalize_path(f'{Config.dest_base}{self.my_subfolder}')

    @property
    def my_fullpath(self) -> str:
        return normalize_filename(self.my_filename, self.my_folder)

    @property
    def state_str(self) -> str:
        return self._state.name


def get_min_max_ids(seq: List[VideoInfo]) -> Tuple[int, int]:
    return min(seq, key=lambda x: x.my_id).my_id, max(seq, key=lambda x: x.my_id).my_id


def export_video_info(info_list: Iterable[VideoInfo]) -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on video info"""
    tags_dict, desc_dict, comm_dict = dict(), dict(), dict()  # type: Dict[str, Dict[int, str]]
    for vi in info_list:
        if vi.my_link:
            for d, s in zip((tags_dict, desc_dict, comm_dict), (vi.my_tags, vi.my_description, vi.my_comments)):
                if vi.my_subfolder not in d:
                    d[vi.my_subfolder] = dict()
                d[vi.my_subfolder][vi.my_id] = s
    for conf, dct, name, proc_cb in zip(
        (Config.save_tags, Config.save_descriptions, Config.save_comments),
        (tags_dict, desc_dict, comm_dict),
        ('tags', 'descriptions', 'comments'),
        (lambda tags: f' {tags.strip()}\n', lambda description: f'{description}\n', lambda comment: f'{comment}\n')
    ):
        if not conf:
            continue
        for subfolder, sdct in dct.items():
            if not sdct:
                continue
            keys = sorted(sdct.keys())
            min_id, max_id = keys[0], keys[-1]
            fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{PREFIX}!{name}_{min_id:d}-{max_id:d}.txt'
            with open(fullpath, 'wt', encoding=UTF8) as sfile:
                sfile.writelines(f'{PREFIX}{idi:d}:{proc_cb(sdct[idi])}' for idi in keys)

#
#
#########################################

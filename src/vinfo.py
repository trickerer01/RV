# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from enum import IntEnum
from typing import Dict, Iterable, Union, Tuple

from config import Config
from defs import PREFIX, UTF8, DEFAULT_QUALITY, DEFAULT_EXT
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
        self._id = m_id or 0

        self.title = m_title or ''
        self.link = m_link or ''
        self.subfolder = m_subfolder or ''
        self.filename = m_filename or ''
        self.rating = m_rating or ''
        self.quality = Config.quality or DEFAULT_QUALITY  # type: str
        self.tags = ''
        self.description = ''
        self.comments = ''
        self.expected_size = 0
        self.start_size = 0
        self.start_time = 0
        self.last_check_size = 0
        self.last_check_time = 0

        self._state = VideoInfo.State.NEW

    def set_state(self, state: VideoInfo.State) -> None:
        self._state = state

    def __eq__(self, other: Union[VideoInfo, int]) -> bool:
        return self.id == other.id if isinstance(other, type(self)) else self.id == other if isinstance(other, int) else False

    def __str__(self) -> str:
        return (
            f'[{self.state_str}] \'{PREFIX}{self.id:d}_{self.title}.{DEFAULT_EXT}\' ({self.quality})'
            f'\nDest: \'{self.my_fullpath}\'\nLink: \'{self.link}\''
        )

    @property
    def id(self) -> int:
        return self._id

    @property
    def sname(self) -> str:
        return f'{PREFIX}{self.id:d}.{DEFAULT_EXT}'

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
    def state_str(self) -> str:
        return self._state.name

    __repr__ = __str__


def get_min_max_ids(seq: Iterable[VideoInfo]) -> Tuple[int, int]:
    return min(seq, key=lambda x: x.id).id, max(seq, key=lambda x: x.id).id


def export_video_info(info_list: Iterable[VideoInfo]) -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on video info"""
    tags_dict, desc_dict, comm_dict = dict(), dict(), dict()  # type: Dict[str, Dict[int, str]]
    for vi in info_list:
        if vi.link:
            for d, s in zip((tags_dict, desc_dict, comm_dict), (vi.tags, vi.description, vi.comments)):
                if vi.subfolder not in d:
                    d[vi.subfolder] = dict()
                d[vi.subfolder][vi.id] = s
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

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from enum import IntEnum
from typing import Dict, Optional, Callable, Iterable, Union

from defs import Config, normalize_path, normalize_filename, prefixp, UTF8, DEFAULT_QUALITY

__all__ = ('VideoInfo', 'export_video_info')


class VideoInfo:  # up to ~3 Kb (when all info is filled, asizeof)
    class VIState(IntEnum):
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
        self._state = VideoInfo.VIState.NEW

    def set_state(self, state: VideoInfo.VIState) -> None:
        self._state = state

    def __eq__(self, other: Union[VideoInfo, int]) -> bool:
        return self.my_id == other.my_id if isinstance(other, type(self)) else self.my_id == other if isinstance(other, int) else False

    def __repr__(self) -> str:
        return (
            f'[{self.state_str}] \'{prefixp()}{self.my_id:d}_{self.my_title}.mp4\' ({self.my_quality})'
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


async def export_video_info(info_list: Iterable[VideoInfo]) -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on video info"""
    tags_dict, desc_dict, comm_dict = dict(), dict(), dict()  # type: Dict[str, Dict[int, str]]
    for vi in info_list:
        if vi.my_link:
            for d, s in zip((tags_dict, desc_dict, comm_dict), (vi.my_tags, vi.my_description, vi.my_comments)):
                if vi.my_subfolder not in d:
                    d[vi.my_subfolder] = dict()
                d[vi.my_subfolder][vi.my_id] = s
    for conf, dct, name, proc_cb in (
        (Config.save_tags, tags_dict, 'tags', lambda tags: f' {tags.strip()}\n'),
        (Config.save_descriptions, desc_dict, 'descriptions', lambda description: f'{description}\n'),
        (Config.save_comments, comm_dict, 'comments', lambda comment: f'{comment}\n')
    ):  # type: Optional[bool], Dict[str, Dict[int, str]], str, Callable[[str], str]
        if conf is True:
            for subfolder, sdct in dct.items():
                if len(sdct) > 0:
                    min_id, max_id = min(sdct.keys()), max(sdct.keys())
                    fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{prefixp()}!{name}_{min_id:d}-{max_id:d}.txt'
                    with open(fullpath, 'wt', encoding=UTF8) as sfile:
                        sfile.writelines(f'{prefixp()}{idi:d}:{proc_cb(elem)}' for idi, elem in sorted(sdct.items(), key=lambda t: t[0]))

#
#
#########################################

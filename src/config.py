# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace
from typing import Optional, List

from aiohttp import ClientTimeout

from defs import CONNECT_TIMEOUT_BASE

__all__ = ('Config',)


class BaseConfig:
    """Parameters container for params used in both **pages** and **ids** modes"""
    def __init__(self) -> None:
        self.dest_base = None  # type: Optional[str]
        self.proxy = None  # type: Optional[str]
        self.session_id = None  # type: Optional[str]
        self.min_rating = None  # type: Optional[int]
        self.min_score = None  # type: Optional[int]
        self.quality = None  # type: Optional[str]
        self.un_video_policy = None  # type: Optional[str]
        self.download_mode = None  # type: Optional[str]
        self.continue_mode = None  # type: Optional[bool]
        self.keep_unfinished = None  # type: Optional[bool]
        self.save_tags = None  # type: Optional[bool]
        self.save_descriptions = None  # type: Optional[bool]
        self.save_comments = None  # type: Optional[bool]
        self.save_screenshots = None  # type: Optional[bool]
        self.extra_tags = None  # type: Optional[List[str]]
        self.scenario = None  # type: Optional['DownloadScenario'] # noqa F821
        self.naming_flags = self.logging_flags = 0
        self.start = self.end = self.start_id = self.end_id = 0
        self.timeout = None  # type: Optional[ClientTimeout]
        # module-specific params (pages only or ids only)
        self.use_id_sequence = None  # type: Optional[bool]
        self.search = None  # type: Optional[str]
        self.search_tags, self.search_arts, self.search_cats = None, None, None  # type: Optional[str]
        self.search_rule_tag, self.search_rule_art, self.search_rule_cat = None, None, None  # type: Optional[str]
        self.playlist_id = None  # type: Optional[int]
        self.playlist_name = None  # type: Optional[str]
        self.uploader = None  # type: Optional[int]
        self.get_maxid = None  # type: Optional[bool]
        # extras (can't be set through cmdline arguments)
        self.nodelay = False

    def read(self, params: Namespace, pages: bool) -> None:
        self.dest_base = params.path
        self.proxy = params.proxy
        # session_id only exists in RV
        self.session_id = getattr(params, 'session_id') if hasattr(params, 'session_id') else self.session_id
        self.min_rating = params.minimum_rating
        self.min_score = params.minimum_score
        self.quality = params.quality
        self.un_video_policy = params.untag_video_policy
        self.download_mode = params.download_mode
        self.continue_mode = params.continue_mode
        self.keep_unfinished = params.keep_unfinished
        self.save_tags = params.dump_tags
        self.save_descriptions = params.dump_descriptions
        self.save_comments = params.dump_comments
        self.save_screenshots = params.dump_screenshots
        self.extra_tags = params.extra_tags
        self.scenario = params.download_scenario
        self.naming_flags = params.naming
        self.logging_flags = params.log_level
        self.start = params.start
        self.end = params.end
        self.start_id = params.stop_id if pages else self.start
        self.end_id = params.begin_id if pages else self.end
        self.timeout = ClientTimeout(total=None, connect=params.timeout or CONNECT_TIMEOUT_BASE)
        # module-specific params (pages only or ids only)
        self.use_id_sequence = getattr(params, 'use_id_sequence') if hasattr(params, 'use_id_sequence') else self.use_id_sequence
        self.search = getattr(params, 'search') if hasattr(params, 'search') else self.search
        self.search_tags = getattr(params, 'search_tag') if hasattr(params, 'search_tag') else ''
        self.search_arts = getattr(params, 'search_art') if hasattr(params, 'search_art') else ''
        self.search_cats = getattr(params, 'search_cat') if hasattr(params, 'search_cat') else ''
        self.search_rule_tag = getattr(params, 'search_rule_tag') if hasattr(params, 'search_rule_tag') else self.search_rule_tag
        self.search_rule_art = getattr(params, 'search_rule_art') if hasattr(params, 'search_rule_art') else self.search_rule_art
        self.search_rule_cat = getattr(params, 'search_rule_cat') if hasattr(params, 'search_rule_cat') else self.search_rule_cat
        self.playlist_id, self.playlist_name = (
            getattr(params, 'playlist_id') if getattr(params, 'playlist_id')[0] else getattr(params, 'playlist_name')
        ) if hasattr(params, 'playlist_id') or hasattr(params, 'playlist_name') else (self.playlist_id, self.playlist_name)
        self.uploader = getattr(params, 'uploader') if hasattr(params, 'uploader') else self.uploader
        self.get_maxid = getattr(params, 'get_maxid') if hasattr(params, 'get_maxid') else self.get_maxid

    @property
    def uvp(self) -> Optional[str]:
        return self.un_video_policy

    @uvp.setter
    def uvp(self, value: str) -> None:
        self.un_video_policy = value

    @property
    def dm(self) -> Optional[str]:
        return self.download_mode


Config = BaseConfig()

#
#
#########################################

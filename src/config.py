# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace
from typing import Optional, List, Union

from aiohttp import ClientTimeout

from defs import (
    Quality, Duration, CONNECT_TIMEOUT_BASE, LOGGING_FLAGS, DOWNLOAD_POLICY_DEFAULT, NAMING_FLAGS_DEFAULT, DOWNLOAD_MODE_DEFAULT,
    DEFAULT_QUALITY, MAX_DEST_SCAN_SUB_DEPTH_DEFAULT, MAX_DEST_SCAN_UPLEVELS_DEFAULT, CONNECT_RETRIES_BASE,
)

if False is True:
    from scenario import DownloadScenario  # for typing only

__all__ = ('Config',)


class BaseConfig:
    """Parameters container for params used in both **pages** and **ids** modules"""
    def __init__(self) -> None:
        self.is_pages = False
        self.dest_base: Optional[str] = None
        self.proxy: Optional[str] = None
        self.download_without_proxy: Optional[bool] = None
        self.session_id: Optional[str] = None
        self.min_rating: Optional[int] = None
        self.min_score: Optional[int] = None
        self.quality: Optional[Quality] = None
        self.duration: Optional[Duration] = None
        self.untagged_policy: Optional[str] = None
        self.folder_scan_depth = self.folder_scan_levelup = 0
        self.download_mode: Optional[str] = None
        self.continue_mode: Optional[bool] = None
        self.keep_unfinished: Optional[bool] = None
        self.no_rename_move: Optional[bool] = None
        self.save_tags: Optional[bool] = None
        self.save_descriptions: Optional[bool] = None
        self.save_comments: Optional[bool] = None
        self.merge_lists: Optional[bool] = None
        self.skip_empty_lists: Optional[bool] = None
        self.save_screenshots: Optional[bool] = None
        self.extra_tags: Optional[List[str]] = None
        self.id_sequence: Optional[List[int]] = None
        self.scenario: Optional[DownloadScenario] = None
        self.naming_flags = self.logging_flags = 0
        self.start = self.end = self.start_id = self.end_id = 0
        self.timeout: Optional[ClientTimeout] = None
        self.retries = 0
        self.throttle: Optional[int] = None
        self.throttle_auto: Optional[bool] = None
        self.store_continue_cmdfile: Optional[bool] = None
        self.report_duplicates: Optional[bool] = None
        self.check_uploader: Optional[bool] = None
        self.check_title_pos: Optional[bool] = None
        self.check_title_neg: Optional[bool] = None
        self.check_description_pos: Optional[bool] = None
        self.check_description_neg: Optional[bool] = None
        # module-specific params (pages only or ids only)
        self.scan_all_pages: Optional[bool] = None
        self.use_id_sequence: Optional[bool] = None
        self.lookahead: Optional[int] = None
        self.search: Optional[str] = None
        self.search_tags: Optional[str] = None
        self.search_arts: Optional[str] = None
        self.search_cats: Optional[str] = None
        self.search_rule_tag: Optional[str] = None
        self.search_rule_art: Optional[str] = None
        self.search_rule_cat: Optional[str] = None
        self.playlist_id: Optional[int] = None
        self.playlist_name: Optional[str] = None
        self.uploader: Optional[int] = None
        self.model: Optional[str] = None
        self.get_maxid: Optional[bool] = None
        # extras (can't be set through cmdline arguments)
        self.nodelay = False

    def read(self, params: Namespace, pages: bool) -> None:
        self.is_pages = pages
        self.dest_base = params.path
        self.proxy = params.proxy
        self.download_without_proxy = params.download_without_proxy
        # session_id only exists in RV and RC
        self.session_id = getattr(params, 'session_id', self.session_id)
        self.min_rating = params.minimum_rating
        self.min_score = params.minimum_score
        self.quality = Quality(params.quality)
        self.duration = params.duration
        self.untagged_policy = params.untagged_policy
        self.folder_scan_depth = params.fsdepth
        self.folder_scan_levelup = params.fslevelup
        self.download_mode = params.download_mode
        self.continue_mode = params.continue_mode
        self.keep_unfinished = params.keep_unfinished
        self.no_rename_move = params.no_rename_move
        self.save_tags = params.dump_tags
        self.save_descriptions = params.dump_descriptions
        self.save_comments = params.dump_comments
        self.merge_lists = params.merge_lists
        self.skip_empty_lists = params.skip_empty_lists
        self.save_screenshots = params.dump_screenshots
        self.extra_tags = params.extra_tags
        self.id_sequence = []
        self.scenario = params.download_scenario
        self.naming_flags = params.naming
        self.logging_flags = params.log_level
        self.start = params.start
        self.end = params.end
        self.start_id = params.stop_id if pages else self.start
        self.end_id = params.begin_id if pages else self.end
        self.timeout = ClientTimeout(total=None, connect=params.timeout or CONNECT_TIMEOUT_BASE)
        self.retries = getattr(params, 'retries', CONNECT_RETRIES_BASE)
        self.throttle = params.throttle
        self.throttle_auto = params.throttle_auto
        self.store_continue_cmdfile = params.store_continue_cmdfile
        self.report_duplicates = getattr(params, 'report_duplicates', self.report_duplicates)
        self.check_uploader = getattr(params, 'check_uploader', self.check_uploader)
        self.check_title_pos = getattr(params, 'check_title_pos', self.check_title_pos)
        self.check_title_neg = getattr(params, 'check_title_neg', self.check_title_neg)
        self.check_description_pos = getattr(params, 'check_description_pos', self.check_description_pos)
        self.check_description_neg = getattr(params, 'check_description_neg', self.check_description_neg)
        # module-specific params (pages only or ids only)
        self.scan_all_pages = getattr(params, 'scan_all_pages', self.scan_all_pages)
        self.use_id_sequence = getattr(params, 'use_id_sequence', self.use_id_sequence)
        self.lookahead = getattr(params, 'lookahead', self.lookahead)
        self.search = getattr(params, 'search', self.search)
        self.search_tags = getattr(params, 'search_tag', '')
        self.search_arts = getattr(params, 'search_art', '')
        self.search_cats = getattr(params, 'search_cat', '')
        self.search_rule_tag = getattr(params, 'search_rule_tag', self.search_rule_tag)
        self.search_rule_art = getattr(params, 'search_rule_art', self.search_rule_art)
        self.search_rule_cat = getattr(params, 'search_rule_cat', self.search_rule_cat)
        self.playlist_id, self.playlist_name = (
            getattr(params, 'playlist_id') if getattr(params, 'playlist_id', (0,))[0] else getattr(params, 'playlist_name')
        ) if hasattr(params, 'playlist_id') or hasattr(params, 'playlist_name') else (self.playlist_id, self.playlist_name)
        self.uploader = getattr(params, 'uploader', self.uploader)
        self.model = getattr(params, 'model', self.model)
        self.get_maxid = getattr(params, 'get_maxid', self.get_maxid)

    def make_continue_arguments(self) -> List[Union[None, str, int]]:
        arglist = [
            '-path', self.dest_base, '-continue', '--store-continue-cmdfile',
            '-log', next(filter(lambda x: int(LOGGING_FLAGS[x], 16) == self.logging_flags, LOGGING_FLAGS.keys())),
            *(('-quality', self.quality) if self.quality != DEFAULT_QUALITY and not self.scenario else ()),
            *(('-duration', str(self.duration)) if self.duration and not self.scenario else ()),
            *(('--report-duplicates',) if self.report_duplicates else ()),
            *(('--check-title-pos',) if self.check_title_pos else ()),
            *(('--check-title-neg',) if self.check_title_neg else ()),
            *(('--check-description-pos',) if self.check_description_pos else ()),
            *(('--check-description-neg',) if self.check_description_neg else ()),
            *(('-utp', self.utp) if self.utp != DOWNLOAD_POLICY_DEFAULT and not self.scenario else ()),
            *(('-minrating', self.min_rating) if self.min_rating else ()),
            *(('-minscore', self.min_score) if self.min_score else ()),
            *(('-naming', self.naming_flags) if self.naming_flags != NAMING_FLAGS_DEFAULT else ()),
            *(('-dmode', self.download_mode) if self.download_mode != DOWNLOAD_MODE_DEFAULT else ()),
            *(('-fsdepth', self.folder_scan_depth) if self.folder_scan_depth != MAX_DEST_SCAN_SUB_DEPTH_DEFAULT else ()),
            *(('-fslevel', self.folder_scan_levelup) if self.folder_scan_levelup != MAX_DEST_SCAN_UPLEVELS_DEFAULT else ()),
            *(('-proxy', self.proxy) if self.proxy else ()),
            *(('--download-without-proxy',) if self.download_without_proxy else ()),
            *(('-throttle', self.throttle) if self.throttle else ()),
            *(('-athrottle',) if self.throttle_auto else ()),
            *(('-timeout', int(self.timeout.connect)) if int(self.timeout.connect) != CONNECT_TIMEOUT_BASE else ()),
            *(('-retries', self.retries) if self.retries != CONNECT_RETRIES_BASE else ()),
            *(('-unfinish',) if self.keep_unfinished else ()),
            *(('-tdump',) if self.save_tags else ()),
            *(('-ddump',) if self.save_descriptions else ()),
            *(('-cdump',) if self.save_comments else ()),
            *(('-dmerge',) if self.merge_lists else ()),
            *(('-dnoempty',) if self.skip_empty_lists else ()),
            *(('-sdump',) if self.save_screenshots else ()),
            # *(('-previews',) if self.include_previews else ()),
            *(('-nomove',) if self.no_rename_move else ()),
            *(('-session_id', self.session_id) if self.session_id else ()),
            *self.extra_tags,
            *(('-script', self.scenario.fmt_str) if self.scenario else ())
        ]
        return arglist

    @property
    def utp(self) -> Optional[str]:
        return self.untagged_policy

    @utp.setter
    def utp(self, value: str) -> None:
        self.untagged_policy = value

    @property
    def dm(self) -> Optional[str]:
        return self.download_mode


Config = BaseConfig()

#
#
#########################################

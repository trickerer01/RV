# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace

from aiohttp import ClientTimeout

from defs import (
    CONNECT_RETRIES_BASE,
    CONNECT_TIMEOUT_BASE,
    DEFAULT_QUALITY,
    DOWNLOAD_MODE_DEFAULT,
    DOWNLOAD_POLICY_DEFAULT,
    LOGGING_FLAGS,
    MAX_DEST_SCAN_SUB_DEPTH_DEFAULT,
    MAX_DEST_SCAN_UPLEVELS_DEFAULT,
    NAMING_FLAGS_DEFAULT,
    Duration,
    Quality,
)

if False is True:
    from scenario import DownloadScenario  # for typing only

__all__ = ('Config',)


class BaseConfig:
    """Parameters container for params used in both **pages** and **ids** modules"""
    def __init__(self) -> None:
        # states
        self.is_pages: bool = False
        self.aborted: bool = False
        # common
        self.dest_base: str | None = None
        self.proxy: str | None = None
        self.download_without_proxy: bool | None = None
        self.session_id: str | None = None
        self.min_rating: int | None = None
        self.min_score: int | None = None
        self.quality: Quality | None = None
        self.duration: Duration | None = None
        self.untagged_policy: str | None = None
        self.folder_scan_depth: int = 0
        self.folder_scan_levelup: int = 0
        self.download_mode: str | None = None
        self.continue_mode: bool | None = None
        self.keep_unfinished: bool | None = None
        self.no_rename_move: bool | None = None
        self.save_tags: bool | None = None
        self.save_descriptions: bool | None = None
        self.save_comments: bool | None = None
        self.merge_lists: bool | None = None
        self.skip_empty_lists: bool | None = None
        self.save_screenshots: bool | None = None
        self.extra_tags: list[str] | None = None
        self.id_sequence: list[int] | None = None
        self.scenario: DownloadScenario | None = None
        self.naming_flags: int = 0
        self.logging_flags: int = 0
        self.nocolors: bool | None = None
        self.start: int = 0
        self.end: int = 0
        self.start_id: int = 0
        self.end_id: int = 0
        self._timeout: float | None = None
        self.timeout: ClientTimeout | None = None
        self.retries: int = 0
        self.throttle: int | None = None
        self.throttle_auto: bool | None = None
        self.store_continue_cmdfile: bool | None = None
        self.solve_tag_conflicts: bool | None = None
        self.report_duplicates: bool | None = None
        self.check_uploader: bool | None = None
        self.check_title_pos: bool | None = None
        self.check_title_neg: bool | None = None
        self.check_description_pos: bool | None = None
        self.check_description_neg: bool | None = None
        # module-specific params (pages only or ids only)
        self.scan_all_pages: bool | None = None
        self.use_id_sequence: bool | None = None
        self.use_link_sequence: bool | None = None
        self.lookahead: int | None = None
        self.predict_id_gaps: bool | None = None
        self.search: str | None = None
        self.search_tags: str | None = None
        self.search_arts: str | None = None
        self.search_cats: str | None = None
        self.search_rule_tag: str | None = None
        self.search_rule_art: str | None = None
        self.search_rule_cat: str | None = None
        self.blacklist: str | None = None
        self.playlist_id: int | None = None
        self.playlist_name: str | None = None
        self.favourites: int | None = None
        self.uploader: int | None = None
        self.model: str | None = None
        self.get_maxid: bool | None = None
        # extras (can't be set through cmdline arguments)
        self.nodelay: bool = False
        self.detect_id_gaps: bool = False

    def read(self, params: Namespace, pages: bool) -> None:
        # states
        self.is_pages = pages
        # common
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
        self.id_sequence = [0] * 0
        self.scenario = params.download_scenario
        self.naming_flags = params.naming
        self.logging_flags = params.log_level
        self.nocolors = params.disable_log_colors
        self.start = params.start
        self.end = params.end
        self.start_id = params.stop_id if self.is_pages else self.start
        self.end_id = params.begin_id if self.is_pages else self.end
        self._timeout = float(params.timeout or CONNECT_TIMEOUT_BASE)
        self.timeout = ClientTimeout(total=None, connect=self._timeout, sock_connect=self._timeout, sock_read=60.0)
        self.retries = getattr(params, 'retries', CONNECT_RETRIES_BASE)
        self.throttle = params.throttle
        self.throttle_auto = params.throttle_auto
        self.store_continue_cmdfile = params.store_continue_cmdfile
        self.solve_tag_conflicts = params.solve_tag_conflicts
        self.report_duplicates = getattr(params, 'report_duplicates', self.report_duplicates)
        self.check_uploader = getattr(params, 'check_uploader', self.check_uploader)
        self.check_title_pos = getattr(params, 'check_title_pos', self.check_title_pos)
        self.check_title_neg = getattr(params, 'check_title_neg', self.check_title_neg)
        self.check_description_pos = getattr(params, 'check_description_pos', self.check_description_pos)
        self.check_description_neg = getattr(params, 'check_description_neg', self.check_description_neg)
        # module-specific params (pages only or ids only)
        self.scan_all_pages = getattr(params, 'scan_all_pages', self.scan_all_pages)
        self.use_id_sequence = getattr(params, 'use_id_sequence', self.use_id_sequence)
        self.use_link_sequence = getattr(params, 'use_link_sequence', self.use_link_sequence)
        self.lookahead = getattr(params, 'lookahead', self.lookahead)
        self.predict_id_gaps = getattr(params, 'predict_id_gaps', self.predict_id_gaps)
        self.search = getattr(params, 'search', self.search)
        self.search_tags = getattr(params, 'search_tag', '')
        self.search_arts = getattr(params, 'search_art', '')
        self.search_cats = getattr(params, 'search_cat', '')
        self.search_rule_tag = getattr(params, 'search_rule_tag', self.search_rule_tag)
        self.search_rule_art = getattr(params, 'search_rule_art', self.search_rule_art)
        self.search_rule_cat = getattr(params, 'search_rule_cat', self.search_rule_cat)
        self.blacklist = getattr(params, 'blacklist', self.blacklist)
        self.playlist_id, self.playlist_name = (
            getattr(params, 'playlist_id') if getattr(params, 'playlist_id', (0,))[0] else getattr(params, 'playlist_name')
        ) if hasattr(params, 'playlist_id') or hasattr(params, 'playlist_name') else (self.playlist_id, self.playlist_name)
        self.favourites = getattr(params, 'favourites', self.favourites)
        self.uploader = getattr(params, 'uploader', self.uploader)
        self.model = getattr(params, 'model', self.model)
        self.get_maxid = getattr(params, 'get_maxid', self.get_maxid)

    def make_continue_arguments(self) -> list[None | str | int]:
        arglist = [
            '-path', self.dest_base, '-continue', '--store-continue-cmdfile',
            '-log', next(filter(lambda x: int(LOGGING_FLAGS[x], 16) == self.logging_flags, LOGGING_FLAGS.keys())),
            *(('-quality', self.quality) if self.quality != DEFAULT_QUALITY and not self.scenario else ()),
            *(('-duration', str(self.duration)) if self.duration and not self.scenario else ()),
            *(('--predict-id-gaps',) if self.predict_id_gaps else ()),
            *(('--solve-tag-conflicts',) if self.solve_tag_conflicts else ()),
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
            *(('-timeout', int(self._timeout)) if self._timeout != CONNECT_TIMEOUT_BASE else ()),
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
            *(('-script', self.scenario.fmt_str) if self.scenario else ()),
        ]
        return arglist

    def on_scan_abort(self) -> None:
        self.aborted = True

    @property
    def utp(self) -> str | None:
        return self.untagged_policy

    @utp.setter
    def utp(self, value: str) -> None:
        self.untagged_policy = value

    @property
    def dm(self) -> str | None:
        return self.download_mode

    @property
    def watcher_mode(self) -> bool:
        return self.lookahead and self.lookahead < 0


Config: BaseConfig = BaseConfig()

#
#
#########################################

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from defs import (
    CONNECT_RETRIES_BASE,
    DEFAULT_QUALITY,
    DOWNLOAD_MODE_DEFAULT,
    DOWNLOAD_POLICY_DEFAULT,
    IDGAP_PREDICTION_DEFAULT,
    LOGGING_FLAGS,
    MAX_DEST_SCAN_SUB_DEPTH_DEFAULT,
    MAX_DEST_SCAN_UPLEVELS_DEFAULT,
    NAMING_FLAGS_DEFAULT,
)

if False is True:  # for hinting only
    from aiohttp import ClientTimeout  # noqa: I001
    from defs import Duration, Quality
    from scenario import DownloadScenario

__all__ = ('Config',)


class BaseConfig:
    """Parameters container for params used in both **pages** and **ids** modules"""
    NAMESPACE_VARS_REMAP = {
        'path': 'dest_base',
        'minimum_rating': 'min_rating',
        'minimum_score': 'min_score',
        'fsdepth': 'folder_scan_depth',
        'fslevelup': 'folder_scan_levelup',
        'dump_tags': 'save_tags',
        'dump_descriptions': 'save_descriptions',
        'dump_comments': 'save_comments',
        'dump_screenshots': 'save_screenshots',
        'download_scenario': 'scenario',
        'naming': 'naming_flags',
        'log_level': 'logging_flags',
        'disable_log_colors': 'nocolors',
        'search_tag': 'search_tags',
        'search_art': 'search_arts',
        'search_cat': 'search_cats',
        'stop_id': 'start_id',
        'begin_id': 'end_id',
    }

    def __init__(self) -> None:
        # states
        self.is_pages: bool = False
        self.aborted: bool = False
        # common
        self.dest_base: str | None = None
        self.proxy: str | None = None
        self.download_without_proxy: bool | None = None
        self.html_without_proxy: bool | None = None
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
        self.predict_id_gaps: str | None = None
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

    def make_continue_arguments(self) -> list[None | str | int]:
        arglist = [
            '-path', self.dest_base, '-continue', '--store-continue-cmdfile',
            '-log', next(x for x in LOGGING_FLAGS if int(LOGGING_FLAGS[x], 16) == self.logging_flags),
            *(('-quality', self.quality) if self.quality != DEFAULT_QUALITY and not self.scenario else ()),
            *(('-duration', str(self.duration)) if self.duration and not self.scenario else ()),
            *(('--predict-id-gaps', str(self.predict_id_gaps)) if self.predict_id_gaps != IDGAP_PREDICTION_DEFAULT else ()),
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
            *(('--html-without-proxy',) if self.html_without_proxy else ()),
            *(('-throttle', self.throttle) if self.throttle else ()),
            *(('-athrottle',) if self.throttle_auto else ()),
            *(('-timeout', int(self.timeout.connect)) if self.timeout and self.timeout.connect else ()),
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

    def _reset(self) -> None:
        self.__init__()

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

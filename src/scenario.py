# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ZERO_OR_MORE, ArgumentParser
from collections.abc import Sequence

from defs import (
    ACTION_STORE_TRUE,
    DEFAULT_QUALITY,
    DOWNLOAD_POLICY_ALWAYS,
    DOWNLOAD_POLICY_DEFAULT,
    QUALITIES,
    UNTAGGED_POLICIES,
    Duration,
    Quality,
)
from iinfo import VideoInfo
from logger import Log
from tagger import extract_id_or_group, is_filtered_out_by_extra_tags, valid_extra_tag
from validators import valid_duration, valid_int, valid_rating

__all__ = ('DownloadScenario',)

UTP_DEFAULT = DOWNLOAD_POLICY_DEFAULT
"""'nofilters'"""
UTP_ALWAYS = DOWNLOAD_POLICY_ALWAYS
"""'always'"""


class SubQueryParams:
    def __init__(self, subfolder: str, extra_tags: list[str], quality: Quality, duration: Duration,
                 minscore: int | None, minrating: int, utp: str, id_sequence: list[int]) -> None:
        self.subfolder: str = subfolder or ''
        self.extra_tags: list[str] = extra_tags or []
        self.quality: Quality = quality or Quality()
        self.duration: Duration = duration
        self.minrating: int = minrating or 0
        self.minscore: int | None = minscore
        self.untagged_policy: str = utp or ''
        self.id_sequence: list[int] = id_sequence or []

    @property
    def utp(self) -> str:
        return self.untagged_policy

    def __repr__(self) -> str:
        return (
            f'sub: \'{self.subfolder}\', '
            f'quality: \'{self.quality}\', '
            f'duration: \'{self.duration}\', '
            f'minrating: \'{self.minrating:d}\', '
            f'minscore: \'{self.minscore!s}\', '
            f'utp: \'{self.utp}\', '
            f'tags: \'{self.extra_tags!s}\', '
            f'ids: \'{self.id_sequence!s}\''
        )


class DownloadScenario:
    def __init__(self, fmt_str: str) -> None:
        assert fmt_str

        self.fmt_str: str = fmt_str
        self.queries: list[SubQueryParams] = []

        parser = ArgumentParser(add_help=False)
        parser.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE)
        parser.add_argument('-quality', default=DEFAULT_QUALITY, choices=QUALITIES)
        parser.add_argument('-duration', default=None, type=valid_duration)
        parser.add_argument('-minrating', '--minimum-rating', default=0, type=valid_rating)
        parser.add_argument('-minscore', '--minimum-score', default=None, type=valid_int)
        parser.add_argument('-utp', '--untagged-policy', default=UTP_DEFAULT, choices=UNTAGGED_POLICIES)
        parser.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE)

        errors_to_print = []
        for query_raw in fmt_str.split('; '):
            try:
                subfolder, args = query_raw.split(': ')
                parsed, unks = parser.parse_known_args(args.split())
                taglist: Sequence[str]
                for i, taglist in enumerate((parsed.extra_tags, unks)):
                    for tag in taglist:
                        try:
                            valid_tag = valid_extra_tag(tag, False)
                            if i > 0:
                                parsed.extra_tags.append(valid_tag)
                        except (AssertionError, ValueError):
                            errors_to_print.append(f'Invalid extra tag: \'{tag}\'')
                if parsed.use_id_sequence is True:
                    id_sequence = extract_id_or_group(parsed.extra_tags)
                    if not id_sequence:
                        error_to_print = ('No ID \'or\' group provided!' if not parsed.extra_tags else
                                          f'No valid ID \'or\' group found in \'{parsed.extra_tags!s}\'!')
                        errors_to_print.append(error_to_print)
                else:
                    id_sequence = []
                if parsed.untagged_policy == UTP_ALWAYS and self.has_subquery(utp=UTP_ALWAYS):
                    errors_to_print.append(f'Scenario can only have one subquery with untagged video policy \'{UTP_ALWAYS}\'!')
                self._add_subquery(SubQueryParams(
                    subfolder, parsed.extra_tags, parsed.quality, parsed.duration,
                    parsed.minimum_score, parsed.minimum_rating, parsed.untagged_policy, id_sequence,
                ))
            except Exception:
                import traceback
                errors_to_print.append(traceback.format_exc().strip())
        if errors_to_print:
            Log.fatal('\n'.join(errors_to_print))
            raise ValueError

        assert len(self) > 0

    def __len__(self) -> int:
        return len(self.queries)

    def _add_subquery(self, subquery: SubQueryParams) -> None:
        self.queries.append(subquery)

    def has_subquery(self, **kwargs) -> bool:
        return any(all(getattr(sq, k, ...) == kwargs[k] for k in kwargs) for sq in self.queries)

    def get_matching_subquery(self, vi: VideoInfo, tags_raw: list[str], score: str, rating: str) -> SubQueryParams | None:
        for sq in self.queries:
            if not is_filtered_out_by_extra_tags(vi, tags_raw, sq.extra_tags, sq.id_sequence, sq.subfolder):
                sq_skip = False
                for vsrs, csri, srn, pc in zip((score, rating), (sq.minscore, sq.minrating), ('score', 'rating'), ('', '%'), strict=True):
                    if len(vsrs) > 0 and csri is not None and sq_skip is False:
                        try:
                            if int(vsrs) < csri:
                                Log.info(f'[{sq.subfolder}] Video {vi.sname} has low {srn} \'{vsrs}{pc}\' (required {csri:d})!')
                                sq_skip = True
                        except Exception:
                            pass
                if sq.duration and vi.duration and not (sq.duration.first <= vi.duration <= sq.duration.second):
                    Log.info(f'[{sq.subfolder}] video {vi.sname} duration \'{vi.duration:d}\' is out of bounds ({sq.duration!s})!')
                    sq_skip = True
                if sq_skip is False:
                    return sq
        return None

    def get_utp_always_subquery(self) -> SubQueryParams | None:
        return next(filter(lambda sq: sq.utp == UTP_ALWAYS, self.queries), None)

#
#
#########################################

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, ZERO_OR_MORE
from typing import List, Optional

from defs import (
    Log, DEFAULT_QUALITY, QUALITIES, UVIDEO_POLICIES, DOWNLOAD_POLICY_DEFAULT, DOWNLOAD_POLICY_ALWAYS, ACTION_STORE_TRUE, LoggingFlags,
    prefixp,
)
from tagger import valid_extra_tag, try_parse_id_or_group, is_filtered_out_by_extra_tags
from validators import valid_int, valid_rating

__all__ = ('DownloadScenario')

UVP_DEFAULT = DOWNLOAD_POLICY_DEFAULT
"""'nofilters'"""
UVP_ALWAYS = DOWNLOAD_POLICY_ALWAYS
"""'always'"""


class SubQueryParams(object):
    def __init__(self, subfolder: str, extra_tags: List[str], quality: str, minscore: Optional[int], minrating: int,
                 uvp: str, use_id_sequence: bool) -> None:
        self.subfolder = subfolder or ''  # type: str
        self.extra_tags = extra_tags or list()  # type: List[str]
        self.quality = quality or ''  # type: str
        self.minrating = minrating or 0  # type: int
        self.minscore = minscore  # type: Optional[int]
        self.untag_video_policy = uvp or ''  # type: str
        self.use_id_sequence = use_id_sequence or False  # type: bool

    @property
    def uvp(self) -> str:
        return self.untag_video_policy

    def __repr__(self) -> str:
        return (
            f'sub: \'{self.subfolder}\', '
            f'quality: \'{self.quality}\', '
            f'minrating: \'{self.minrating:d}\', '
            f'minscore: \'{str(self.minscore)}\', '
            f'uvp: \'{self.uvp}\', '
            f'use_id_sequence: \'{self.use_id_sequence}\', '
            f'tags: \'{str(self.extra_tags)}\''
        )


class DownloadScenario(object):
    def __init__(self, fmt_str: str) -> None:
        assert fmt_str

        self.queries = list()  # type: List[SubQueryParams]

        parser = ArgumentParser(add_help=False)
        parser.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE, help='')
        parser.add_argument('-quality', default=DEFAULT_QUALITY, help='', choices=QUALITIES)
        parser.add_argument('-minrating', '--minimum-rating', metavar='#0-100', default=0, help='', type=valid_rating)
        parser.add_argument('-minscore', '--minimum-score', metavar='#score', default=None, help='', type=valid_int)
        parser.add_argument('-uvp', '--untag-video-policy', default=UVP_DEFAULT, help='', choices=UVIDEO_POLICIES)
        parser.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help='', type=valid_extra_tag)

        for query_raw in fmt_str.split('; '):
            error_to_print = ''
            try:
                subfolder, args = query_raw.split(': ')
                parsed, unks = parser.parse_known_args(args.split())
                for tag in unks:
                    try:
                        assert valid_extra_tag(tag)
                        if parsed.use_id_sequence is True:
                            assert len(unks) == 1
                            assert try_parse_id_or_group([tag]) is not None
                    except Exception:
                        error_to_print = f'\nInvalid extra tag: \'{tag}\'\n'
                        raise
                parsed.extra_tags += [tag.lower().replace(' ', '_') for tag in unks]
                if parsed.untag_video_policy == UVP_ALWAYS and self.has_subquery(uvp=UVP_ALWAYS):
                    error_to_print = f'Scenario can only have one subquery with untagged video policy \'{UVP_ALWAYS}\'!'
                    raise ValueError
                self.add_subquery(SubQueryParams(
                    subfolder, parsed.extra_tags, parsed.quality, parsed.minimum_score, parsed.minimum_rating, parsed.untag_video_policy,
                    parsed.use_id_sequence
                ))
            except Exception:
                if error_to_print != '':
                    Log.error(error_to_print)
                raise

        assert len(self) > 0

    def __len__(self) -> int:
        return len(self.queries)

    def add_subquery(self, subquery: SubQueryParams) -> None:
        self.queries.append(subquery)

    def has_subquery(self, **kwargs) -> bool:
        for sq in self.queries:
            all_matched = True
            for k, v in kwargs.items():
                if not (hasattr(sq, k) and getattr(sq, k) == v):
                    all_matched = False
                    break
            if all_matched is True:
                return True
        return False

    def get_matching_subquery(self, idi: int, tags_raw: List[str], score: str, rating: str) -> Optional[SubQueryParams]:
        sname = f'{prefixp()}{idi:d}.mp4'
        for sq in self.queries:
            if not is_filtered_out_by_extra_tags(idi, tags_raw, sq.extra_tags, sq.use_id_sequence, sq.subfolder):
                sq_skip = False
                for vsrs, csri, srn, pc in zip((score, rating), (sq.minscore, sq.minrating), ('score', 'rating'), ('', '%')):
                    if len(vsrs) > 0 and csri is not None and sq_skip is False:
                        try:
                            if int(vsrs) < csri:
                                Log.info(f'[{sq.subfolder}] Video {sname} has low {srn} \'{vsrs}{pc}\' (required {csri:d})!',
                                         LoggingFlags.LOGGING_EX_LOW_SCORE)
                                sq_skip = True
                        except Exception:
                            pass
                if sq_skip is False:
                    return sq
        return None

    def get_uvp_always_subquery(self) -> Optional[SubQueryParams]:
        return next(filter(lambda sq: sq.uvp == UVP_ALWAYS, self.queries), None)

#
#
#########################################

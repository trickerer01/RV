# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from argparse import ArgumentParser, ZERO_OR_MORE, ArgumentError
from typing import List

from defs import (
    Log, DEFAULT_QUALITY, HELP_QUALITY, QUALITIES, HELP_ARG_UVPOLICY, UVIDEO_POLICIES, HELP_ARG_EXTRA_TAGS, DOWNLOAD_POLICY_DEFAULT,
    DOWNLOAD_POLICY_ALWAYS, HELP_ARG_MINSCORE
)
from tagger import extra_tag

UVP_DEFAULT = DOWNLOAD_POLICY_DEFAULT


# todo: create validators and move everything there
def valid_int(val: str) -> int:
    try:
        return int(val)
    except Exception:
        raise ArgumentError


class SubQueryParams(object):
    def __init__(self, subfolder: str, extra_tags: List[str], quality: str, minscore: int, uvp: str) -> None:
        self.subfolder = subfolder or ''  # type: str
        self.extra_tags = extra_tags or []  # type: List[str]
        self.quality = quality or ''  # type: str
        self.minscore = minscore or -999999  # type: int
        self.untag_video_policy = uvp or ''  # type: str

    @property
    def uvp(self) -> str:
        return self.untag_video_policy

    def __repr__(self) -> str:
        return (
            f'sub: \'{self.subfolder}\', '
            f'quality: \'{self.quality}\', '
            f'minscore: \'{self.minscore:d}\', '
            f'uvp: \'{self.uvp}\', '
            f'tags: \'{str(self.extra_tags)}\''
        )


class DownloadScenario(object):
    def __init__(self, fmt_str: str = None) -> None:
        self.queries = []  # type: List[SubQueryParams]
        if fmt_str is None:
            return

        parser = ArgumentParser(add_help=False)
        parser.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_QUALITY, choices=QUALITIES)
        parser.add_argument('-minscore', '--minimum-score', metavar='#score', default=None, help=HELP_ARG_MINSCORE, type=valid_int)
        parser.add_argument('-uvp', '--untag-video-policy', default=UVP_DEFAULT, help=HELP_ARG_UVPOLICY, choices=UVIDEO_POLICIES)
        parser.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help=HELP_ARG_EXTRA_TAGS, type=extra_tag)

        for query_raw in fmt_str.split('; '):
            error_to_print = ''
            try:
                subfolder, args = query_raw.split(': ')
                parsed, unks = parser.parse_known_args(args.split())
                parsed.extra_tags += [tag.lower().replace(' ', '_') for tag in unks]
                if parsed.untag_video_policy == DOWNLOAD_POLICY_ALWAYS and self.has_subquery(untag_video_policy=DOWNLOAD_POLICY_ALWAYS):
                    error_to_print = f'Scenario can only have one subquery with untagged video policy \'{DOWNLOAD_POLICY_ALWAYS}\'!'
                    raise ValueError
                self.add_subquery(SubQueryParams(
                    subfolder, parsed.extra_tags, parsed.quality, parsed.minimum_score, parsed.untag_video_policy
                ))
            except (ArgumentError, TypeError, Exception):
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
                if not (k in sq.__dict__.keys() and sq.__getattribute__(k) == v):
                    all_matched = False
                    break
            if all_matched is True:
                return True
        return False

#
#
#########################################

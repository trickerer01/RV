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
    DOWNLOAD_POLICY_ALWAYS
)
from tagger import assert_valid_or_group, validate_neg_and_group, is_non_wtag, assert_valid_tag

UVP_DEFAULT = DOWNLOAD_POLICY_DEFAULT


def extra_tag(tag: str) -> str:
    try:
        if tag[0] == '(':
            assert_valid_or_group(tag)
        elif tag.startswith('-('):
            validate_neg_and_group(tag)
        elif is_non_wtag(tag[1:]):
            assert_valid_tag(tag[1:])
    except Exception:
        raise ArgumentError

    return tag.lower().replace(' ', '_')


class SubQueryParams(object):
    def __init__(self, subfolder: str = None, extra_tags: List[str] = None, quality: str = None, uvp: str = None) -> None:
        self.subfolder = subfolder or ''  # type: str
        self.extra_tags = extra_tags or []  # type: List[str]
        self.quality = quality or ''  # type: str
        self.untag_video_policy = uvp or ''  # type: str

    @property
    def uvp(self) -> str:
        return self.untag_video_policy

    def __repr__(self) -> str:
        return f'sub: \'{self.subfolder}\', quality: \'{self.quality}\', uvp: \'{self.uvp}\', tags: \'{str(self.extra_tags)}\''


class DownloadScenario(object):
    def __init__(self) -> None:
        self.queries = []  # type: List[SubQueryParams]

    def __len__(self) -> int:
        return len(self.queries)

    def add_subquery(self, subquery: SubQueryParams) -> None:
        self.queries.append(subquery)

    def has_subquery(self, **kwargs) -> bool:
        for k, v in kwargs.items():
            for sq in self.queries:
                if k in sq.__dict__.keys() and sq.__getattribute__(k) == v:
                    return True
        return False

    @staticmethod
    def from_string(fmt_str: str) -> DownloadScenario:
        ds = DownloadScenario()

        parser = ArgumentParser(add_help=False)
        parser.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_QUALITY, choices=QUALITIES)
        parser.add_argument('-uvp', '--untag-video-policy', default=UVP_DEFAULT, help=HELP_ARG_UVPOLICY, choices=UVIDEO_POLICIES)
        parser.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help=HELP_ARG_EXTRA_TAGS, type=extra_tag)

        for query_raw in fmt_str.split('; '):
            error_to_print = ''
            try:
                subfolder, args = query_raw.split(': ')
                parsed, unks = parser.parse_known_args(args.split())
                if len(unks) > 0:
                    for tag in unks:
                        try:
                            assert extra_tag(tag)
                        except Exception:
                            error_to_print = f'\nInvalid tag: \'{tag}\'\n'
                            raise
                    parsed.extra_tags += [tag for tag in unks]
                if parsed.untag_video_policy == DOWNLOAD_POLICY_ALWAYS and ds.has_subquery(untag_video_policy=DOWNLOAD_POLICY_ALWAYS):
                    error_to_print = f'Scenario can only have one subquery with untagged video policy \'{DOWNLOAD_POLICY_ALWAYS}\'!'
                    raise ValueError
                ds.add_subquery(SubQueryParams(subfolder, parsed.extra_tags, parsed.quality, parsed.untag_video_policy))
            except (ArgumentError, TypeError, Exception):
                if error_to_print != '':
                    Log(error_to_print)
                raise

        return ds

#
#
#########################################

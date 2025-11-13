# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import json
import os
from collections.abc import Callable, Collection, Iterable, MutableSequence
from typing import TypeAlias

from config import Config
from defs import (
    FILE_LOC_ARTS,
    FILE_LOC_CATS,
    FILE_LOC_PLAS,
    FILE_LOC_TAG_ALIASES,
    FILE_LOC_TAG_CONFLICTS,
    FILE_LOC_TAGS,
    HTTPS_PREFIX,
    SITE,
    TAGS_CONCAT_CHAR,
    UTF8,
)
from iinfo import VideoInfo
from logger import Log
from rex import (
    prepare_regex_fullmatch,
    re_bracketed_tag,
    re_idval,
    re_neg_and_group,
    re_not_a_letter,
    re_numbered_or_counted_tag,
    re_or_group,
    re_replace_symbols,
    re_tags_exclude_major1,
    re_tags_exclude_major2,
    re_tags_to_not_exclude,
    re_tags_to_process,
    re_uscore_mult,
    re_wtag,
)
from util import assert_nonempty, normalize_path

__all__ = (
    'extract_id_or_group',
    'extract_ids_from_links',
    'filtered_tags',
    'get_matching_tag',
    'is_filtered_out_by_extra_tags',
    'solve_tag_conflicts',
    'valid_artists',
    'valid_blacklist',
    'valid_categories',
    'valid_extra_tag',
    'valid_playlist_id',
    'valid_playlist_name',
    'valid_tags',
)

TagConflictsDict: TypeAlias = dict[str, tuple[list[str], list[str]]]

TAG_NUMS: dict[str, str] = {}
ART_NUMS: dict[str, str] = {}
CAT_NUMS: dict[str, str] = {}
PLA_NUMS: dict[str, str] = {}
PLA_NUMS_REV: dict[str, str] = {}
TAG_ALIASES: dict[str, str] = {}
TAG_CONFLICTS: TagConflictsDict = {}


def valid_playlist_name(plist: str) -> tuple[int, str]:
    try:
        if not PLA_NUMS:
            load_playlist_nums()
        plist_v = PLA_NUMS[plist]
        plist_name, plist_numb = plist, int(plist_v)
        return plist_numb, plist_name
    except Exception:
        raise ValueError


def valid_playlist_id(plist: str) -> tuple[int, str]:
    try:
        assert plist.isnumeric()
        if not PLA_NUMS_REV:
            load_playlist_nums_rev()
        plist_v = PLA_NUMS_REV[plist]
        plist_name, plist_numb = plist_v, int(plist)
        return plist_numb, plist_name
    except Exception:
        raise ValueError


def valid_extra_tag(tag: str, log=True) -> str:
    try:
        if is_valid_link(tag):
            return normalize_link(tag)
        elif tag.startswith('('):
            assert is_valid_or_group(tag)
            all_valid = is_valid_id_or_group(tag) or all_extra_tags_valid(tag[1:-1].split('~'))
        elif tag.startswith('-('):
            assert is_valid_neg_and_group(tag)
            all_valid = all_extra_tags_valid(tag[2:-1].split(','))
        else:
            all_valid = is_valid_extra_tag(tag[1:] if tag.startswith('-') else tag)
        assert all_valid
        return tag.lower().replace(' ', '_')
    except Exception:
        if log:
            Log.fatal(f'Fatal: invalid extra tag or group: \'{tag}\'!')
        raise ValueError


def valid_tags(tags_str: str, *, report=True) -> str:
    all_valid = True
    tag_ids = set()
    if len(tags_str) > 0:
        for tag in tags_str.split(','):
            try:
                tag_ids.update(get_tag_num(tag_ex, True) for tag_ex in assert_nonempty(expand_tags(tag)))
            except Exception:
                if report:
                    Log.error(f'Error: invalid tag: \'{tag}\'!')
                all_valid = False
                continue
    if not all_valid:
        if report:
            Log.fatal('Fatal: Invalid tags found!')
        raise ValueError
    return ','.join(sorted(tag_ids))


def valid_artists(artists_str: str, *, report=True) -> str:
    all_valid = True
    artist_ids = set()
    if len(artists_str) > 0:
        for artist in artists_str.split(','):
            try:
                artist_ids.update(get_artist_num(artist_ex, True) for artist_ex in assert_nonempty(expand_artists(artist)))
            except Exception:
                if report:
                    Log.error(f'Error: invalid artist: \'{artist}\'!')
                all_valid = False
                continue
    if not all_valid:
        if report:
            Log.fatal('Fatal: Invalid artists found!')
        raise ValueError
    return ','.join(sorted(artist_ids))


def valid_categories(categories_str: str, *, report=True) -> str:
    all_valid = True
    category_ids = set()
    if len(categories_str) > 0:
        for category in categories_str.split(','):
            try:
                category_ids.update(get_category_num(category_ex, True) for category_ex in assert_nonempty(expand_categories(category)))
            except Exception:
                if report:
                    Log.error(f'Error: invalid category: \'{category}\'!')
                all_valid = False
                continue
    if not all_valid:
        if report:
            Log.fatal('Fatal: Invalid categories found!')
        raise ValueError
    return ','.join(sorted(category_ids))


def valid_blacklist(blacklist_str: str) -> str:
    bl_act_type_artist = 'model'
    bl_act_type_category = 'cat'
    bl_act_type_tag = 'tag'
    containers: dict[str, set[str]] = {bl_act_type_artist: set(), bl_act_type_category: set(), bl_act_type_tag: set()}
    errors = list[str]()

    if len(blacklist_str) > 0:
        checkers: dict[str, Callable[..., str]] = {
            bl_act_type_artist: valid_artists,
            bl_act_type_category: valid_categories,
            bl_act_type_tag: valid_tags,
        }

        try:
            for act_raw in blacklist_str.split(','):
                try:
                    if ':' in act_raw:
                        act_type, act_value = act_raw.split(':')
                        act_type_full = {'a': bl_act_type_artist, 'c': bl_act_type_category, 't': bl_act_type_tag}.get(act_type)
                        containers[act_type_full].update(checkers[act_type_full](act_value, report=False).split(','))
                    else:
                        containers_temp = {bl_act_type_artist: set(), bl_act_type_category: set(), bl_act_type_tag: set()}
                        for act_type_full, blacklist_set in containers_temp.items():
                            try:
                                values_to_push = checkers[act_type_full](act_raw, report=False)
                                blacklist_set.update(values_to_push.split(','))
                            except Exception:
                                continue
                        if all(not containers_temp[k] for k in containers_temp):
                            raise ValueError
                        for act_type_full, blacklist_set in containers_temp.items():
                            containers[act_type_full].update(blacklist_set)
                except Exception:
                    errors.append(f'Invalid blacklist partition \'{act_raw}\'')
        except ValueError:
            errors.append(f'Invalid blacklist string \'{blacklist_str}\'')

        if errors:
            Log.fatal('\n'.join(errors))
            raise ValueError

    return ','.join(','.join(f'{k}:{v}' for v in sorted(containers[k])) for k in containers if containers[k])


def is_utag(tag: str) -> bool:
    return tag.startswith('u:')


def is_wtag(tag: str) -> bool:
    return bool(re_wtag.fullmatch(tag))


def all_extra_tags_valid(tags: list[str]) -> bool:
    all_valid = True
    for t in tags:
        if not is_valid_extra_tag(t):
            all_valid = False
            Log.error(f'Error: invalid extra tag: \'{t}\'!')
    return all_valid


def is_valid_extra_tag(extag: str) -> bool:
    return is_utag(extag) or is_wtag(extag) or is_valid_tag(extag) or is_valid_artist(extag) or is_valid_category(extag)


def is_valid_link(extag: str) -> bool:
    return any((extag.startswith(SITE), f'{HTTPS_PREFIX}{extag}'.startswith(SITE)))


def normalize_link(link: str) -> str:
    return link if link.startswith(SITE) else f'{HTTPS_PREFIX}{link}'


def get_tag_num(tag: str, assert_=False) -> str | None:
    if not TAG_NUMS:
        load_tag_nums()
    return TAG_NUMS[tag] if assert_ else TAG_NUMS.get(tag)


def is_valid_tag(tag: str) -> bool:
    return bool(get_tag_num(tag))


def get_artist_num(artist: str, assert_=False) -> str | None:
    if not ART_NUMS:
        load_artist_nums()
    return ART_NUMS[artist] if assert_ else ART_NUMS.get(artist)


def is_valid_artist(artist: str) -> bool:
    return bool(get_artist_num(artist))


def get_category_num(category: str, assert_=False) -> str | None:
    if not CAT_NUMS:
        load_category_nums()
    return CAT_NUMS[category] if assert_ else CAT_NUMS.get(category)


def is_valid_category(category: str) -> bool:
    return bool(get_category_num(category))


def is_valid_neg_and_group(andgr: str) -> bool:
    return bool(re_neg_and_group.fullmatch(andgr))


def is_valid_or_group(orgr: str) -> bool:
    return bool(re_or_group.fullmatch(orgr))


def expand_tags(pwtag: str) -> Iterable[str]:
    expanded_tags = set()
    if not is_wtag(pwtag):
        expanded_tags.add(pwtag)
    else:
        if not TAG_NUMS:
            load_tag_nums()
        Log.debug(f'Expanding tags from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for tag in TAG_NUMS:
            if pat.fullmatch(tag):
                Log.debug(f' - \'{tag}\'')
                expanded_tags.add(tag)
    return expanded_tags


def expand_artists(pwtag: str) -> Iterable[str]:
    expanded_artists = set()
    if not is_wtag(pwtag):
        expanded_artists.add(pwtag)
    else:
        if not ART_NUMS:
            load_artist_nums()
        Log.debug(f'Expanding artists from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for artist in ART_NUMS:
            if pat.fullmatch(artist):
                Log.debug(f' - \'{artist}\'')
                expanded_artists.add(artist)
    return expanded_artists


def expand_categories(pwtag: str) -> Iterable[str]:
    expanded_categories = set()
    if not is_wtag(pwtag):
        expanded_categories.add(pwtag)
    else:
        if not CAT_NUMS:
            load_category_nums()
        Log.debug(f'Expanding categories from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for category in CAT_NUMS:
            if pat.fullmatch(category):
                Log.debug(f' - \'{category}\'')
                expanded_categories.add(category)
    return expanded_categories


def normalize_wtag(wtag: str) -> str:
    wtag_freplacements = {
        '(?:': '\u2044', '?': '\u203D', '*': '\u20F0', '(': '\u2039', ')': '\u203A',
        # '[': '\u2018', ']': '\u2019', '{': '\u201C', '}': '\u201D',
        '.': '\u1FBE', ',': '\u201A', '+': '\u2020', '-': '\u2012',
    }
    wtag_breplacements: dict[str, str] = {wtag_freplacements[k]: k for k in wtag_freplacements}
    wtag_breplacements[wtag_freplacements['(']] = '(?:'
    chars_need_escaping = list(wtag_freplacements.keys())
    del chars_need_escaping[1:3]
    escape_char = '`'
    escape = escape_char in wtag
    if escape:
        for fk, wtag_freplacement in wtag_freplacements.items():
            wtag = wtag.replace(f'{escape_char}{fk}', wtag_freplacement)
    for c in chars_need_escaping:
        wtag = wtag.replace(c, f'\\{c}')
    wtag = wtag.replace('*', '.*').replace('?', '.').replace(escape_char, '')
    if escape:
        for bk, wtag_breplacement in wtag_breplacements.items():
            wtag = wtag.replace(f'{bk}', wtag_breplacement)
    return wtag


def get_matching_tag(wtag: str, mtags: Iterable[str], *, force_regex=False) -> str | None:
    if not is_wtag(wtag) and not force_regex:
        return wtag if wtag in mtags else None
    pat = prepare_regex_fullmatch(normalize_wtag(wtag))
    for htag in mtags:
        if pat.fullmatch(htag):
            return htag
    return None


def get_or_group_matching_tag(orgr: str, mtags: Iterable[str]) -> str | None:
    for tag in orgr[1:-1].split('~'):
        mtag = get_matching_tag(tag, mtags)
        if mtag:
            return mtag
    return None


def get_neg_and_group_matches(andgr: str, mtags: Iterable[str]) -> list[str]:
    matched_tags = []
    for wtag in andgr[2:-1].split(','):
        mtag = get_matching_tag(wtag, mtags, force_regex=True)
        if not mtag:
            return []
        matched_tags.append(mtag)
    return matched_tags


def is_valid_id_or_group(orgr: str) -> bool:
    return is_valid_or_group(orgr) and all(re_idval.fullmatch(tag) for tag in orgr[1:-1].split('~'))


def extract_id_or_group(ex_tags: MutableSequence[str]) -> list[int]:
    """May alter the input container!"""
    for i in range(len(ex_tags)):
        orgr = ex_tags[i]
        if is_valid_id_or_group(orgr):
            del ex_tags[i]
            return list(set(int(tag.replace('id=', '')) for tag in orgr[1:-1].split('~')))
    return []


def extract_ids_from_links(ex_tags: MutableSequence[str]) -> list[int]:
    """May alter the input container!"""
    ids = []
    video_id_str = 'video/'
    for i in reversed(range(len(ex_tags))):
        link = ex_tags[i]
        if is_valid_link(link):
            del ex_tags[i]
            id_idx = (link.find(video_id_str) + len(video_id_str)) if video_id_str in link else -1
            end_idx = link.find('/', id_idx + 1)
            if 0 <= id_idx < end_idx:
                link_id = link[id_idx:link.find('/', id_idx + 1)]
                if link_id.isnumeric():
                    ids.append(int(link_id))
    return ids


def convert_extra_tag_for_text_matching(ex_tag: str) -> str:
    if ex_tag.startswith('-('):
        wtags, tagtype = ex_tag[2:-1].split(','), 1
    elif ex_tag.startswith('('):
        wtags, tagtype = ex_tag[1:-1].split('~'), 2
    elif ex_tag.startswith('-'):
        wtags, tagtype = [ex_tag[1:]], 3
    else:
        wtags, tagtype = [ex_tag], 4

    # language=PythonRegExp
    norm_str = r'`(?:^|$|`[ ()\[\]_\'"`]`)'
    for i, wtag in enumerate(wtags):
        wtag_begin = '' if wtag.startswith('*') else '*' if wtag.startswith(tuple(norm_str[1:-1].split())) else f'*{norm_str}'
        wtag_end = '' if wtag.endswith('*') else '*' if wtag.endswith(tuple(norm_str[1:-1].split())) else f'{norm_str}*'
        wtags[i] = f'{wtag_begin}{wtag.replace("_", " ")}{wtag_end}'

    conv_tag = (
        f'-({",".join(wtags)})' if tagtype == 1 else f'({"~".join(wtags)})' if tagtype == 2 else
        f'-{"".join(wtags)}' if tagtype == 3 else f'{"".join(wtags)}'
    )
    return conv_tag


def match_text(ex_tag: str, text: str, group_type='') -> str | list[str] | None:
    converted_tag = convert_extra_tag_for_text_matching(ex_tag)
    text = text.replace('\n', ' ').strip().lower()
    if group_type == 'or':
        return get_or_group_matching_tag(converted_tag, [text])
    elif group_type == 'and':
        return get_neg_and_group_matches(converted_tag, [text])
    else:
        return get_matching_tag(converted_tag, [text])


def trim_undersores(base_str: str) -> str:
    return re_uscore_mult.sub('_', base_str).strip('_')


def solve_tag_conflicts(vi: VideoInfo, tags_raw: list[str]) -> None:
    if not TAG_CONFLICTS:
        load_tag_conflicts()
    for ctag, clistpair in TAG_CONFLICTS.items():
        if ctag in tags_raw:
            cposlist, cneglist = clistpair
            if any(cp in tags_raw for cp in cposlist) and not any(cn in tags_raw for cn in cneglist):
                Log.info(f'{vi.sname} is tagged with both \'{ctag}\' and \'{"/".join(cposlist)}\'! Removing \'{ctag}\' tag!')
                tags_raw.remove(ctag)


def is_filtered_out_by_extra_tags(vi: VideoInfo, tags_raw: list[str], extra_tags: list[str],
                                  id_seq: list[int], subfolder: str, id_seq_ex: list[int] | None = None) -> bool:
    suc = True
    sname = f'{f"[{subfolder}] " if subfolder else ""}Video {vi.sname}'
    if id_seq and vi.id not in id_seq and not (id_seq_ex and vi.id in id_seq_ex):
        suc = False
        Log.trace(f'{sname} isn\'t contained in id list \'{id_seq!s}\'. Skipped!')

    for extag in extra_tags:
        if extag.startswith('('):
            or_match_base = get_or_group_matching_tag(extag, tags_raw)
            or_match_titl = match_text(extag, vi.title, 'or') if Config.check_title_pos and vi.title else None
            or_match_desc = match_text(extag, vi.description, 'or') if Config.check_description_pos and vi.description else None
            if or_match_base:
                Log.trace(f'{sname} has BASE POS match: \'{or_match_base!s}\'')
            if or_match_titl:
                Log.trace(f'{sname} has TITL POS match: \'{or_match_titl!s}\'')
            if or_match_desc:
                Log.trace(f'{sname} has DESC POS match: \'{or_match_desc!s}\'')
            if not bool(or_match_base or or_match_titl or or_match_desc):
                suc = False
                Log.trace(f'{sname} misses required tag matching \'{extag}\'. Skipped!')
        elif extag.startswith('-('):
            neg_matches = get_neg_and_group_matches(extag, tags_raw)
            for conf, cn, td in zip(
                (Config.check_title_neg, Config.check_description_neg),
                ('TITL', 'DESC'),
                (vi.title, vi.description),
                strict=True,
            ):
                if conf and td:
                    for tmatch in match_text(extag, td, 'and'):
                        tmatch_s = tmatch[:100]
                        Log.trace(f'{sname} has {cn} NEG match: \'{tmatch_s}\'')
                        if tmatch_s not in neg_matches:
                            neg_matches.append(f'{tmatch_s}...')
            if neg_matches:
                suc = False
                Log.info(f'{sname} contains excluded tags combination \'{extag}\': {",".join(neg_matches)}. Skipped!')
        else:
            negative = extag.startswith('-')
            my_extag = extag[1:] if negative else extag
            if is_utag(my_extag):
                my_utag = my_extag[2:]
                mtag = get_matching_tag(my_utag, (vi.uploader,))
                if negative is False and mtag:
                    Log.trace(f'{sname} has BASE POS match: \'{mtag}\' (from utag \'{my_extag}\')')
            else:
                mtag = get_matching_tag(my_extag, tags_raw)
                if negative is False and mtag:
                    Log.trace(f'{sname} has BASE POS match: \'{mtag}\'')
                for conf, cn, np, td in zip(
                    (Config.check_title_pos, Config.check_title_neg, Config.check_description_pos, Config.check_description_neg),
                    ('TITL', 'TITL', 'DESC', 'DESC'),
                    ('POS', 'NEG', 'POS', 'NEG'),
                    (vi.title, vi.title, vi.description, vi.description),
                    strict=True,
                ):
                    if conf and td and ((np == 'NEG') == negative) and not mtag:
                        mtag = match_text(my_extag, td)
                        if mtag:
                            mtag = f'{mtag[:100]}...'
                            if negative is False:
                                Log.trace(f'{sname} has {cn} {np} match: \'{mtag}\'')
            if mtag is not None and negative:
                suc = False
                Log.info(f'{sname} contains excluded tag \'{mtag}\' (\'{extag}\'). Skipped!')
            elif mtag is None and not negative:
                suc = False
                Log.trace(f'{sname} misses required tag matching \'{my_extag}\'. Skipped!')
    return not suc


def filtered_tags(tags_list: Collection[str]) -> str:
    if len(tags_list) == 0:
        return ''

    if not TAG_ALIASES:
        load_tag_aliases()

    tags_list_final: list[str] = []

    for tag in tags_list:
        tag = re_replace_symbols.sub('_', tag.replace('-', '').replace('\'', '').replace('.', ''))
        alias = TAG_ALIASES.get(tag)
        if alias is None and re_tags_to_process.match(tag) is None:
            continue

        tag = alias or tag

        # digital_media_(artwork)
        aser_match = re_bracketed_tag.match(tag)
        aser_valid = bool(aser_match)
        if aser_match:
            major_skip_match1 = re_tags_exclude_major1.match(aser_match.group(1))
            major_skip_match2 = re_tags_exclude_major2.match(aser_match.group(2))
            if major_skip_match1 or major_skip_match2:
                continue
            tag = trim_undersores(aser_match.group(1))
            if len(tag) >= 17:
                continue
        elif alias is None and re_tags_to_not_exclude.match(tag) is None:
            continue

        tag = trim_undersores(tag)

        do_add = True
        if len(tags_list_final) > 0:
            nutag = re_not_a_letter.sub('', re_numbered_or_counted_tag.sub(r'\1', tag))
            # try and see
            # 1) if this tag can be consumed by existing tags
            # 2) if this tag can consume existing tags
            for i in reversed(range(len(tags_list_final))):
                t = re_numbered_or_counted_tag.sub(r'\1', tags_list_final[i].lower())
                nut = re_not_a_letter.sub('', t)
                if len(nut) >= len(nutag) and (nutag in nut):
                    do_add = False
                    break
            if do_add:
                for i in reversed(range(len(tags_list_final))):
                    t = re_numbered_or_counted_tag.sub(r'\1', tags_list_final[i].lower())
                    nut = re_not_a_letter.sub('', t)
                    if len(nutag) >= len(nut) and (nut in nutag):
                        if aser_valid is False and tags_list_final[i][0].isupper():
                            aser_valid = True
                        del tags_list_final[i]
        if do_add:
            if aser_valid:
                i: int
                c: str
                for i, c in enumerate(tag):
                    if (i == 0 or tag[i - 1] == '_') and c.isalpha():
                        tag = f'{tag[:i]}{c.upper()}{tag[i + 1:]}'
            tags_list_final.append(tag)

    return trim_undersores(TAGS_CONCAT_CHAR.join(sorted(tags_list_final)))


def load_actpac_json(file_loc: str, dest_dict: dict[str, str] | TagConflictsDict, name: str, *, extract=True, reverse=False) -> None:
    try:
        Log.trace(f'Loading {name}...')
        with open(file_loc, 'rt', encoding=UTF8) as json_file:
            if extract:
                if reverse:
                    dest_dict.update({(v[:v.find(',')] if ',' in v else v): k for k, v in json.load(json_file).items()})
                else:
                    dest_dict.update({k: (v[:v.find(',')] if ',' in v else v) for k, v in json.load(json_file).items()})
            else:
                if reverse:
                    dest_dict.update({v: k for k, v in json.load(json_file).items()})
                else:
                    dest_dict.update(json.load(json_file))
    except Exception:
        Log.error(f'Failed to load {name} from {normalize_path(os.path.abspath(file_loc), False)}')
        dest_dict.update({'': ''})


def load_tag_nums() -> None:
    load_actpac_json(FILE_LOC_TAGS, TAG_NUMS, 'tag nums')


def load_artist_nums() -> None:
    load_actpac_json(FILE_LOC_ARTS, ART_NUMS, 'artist nums')


def load_category_nums() -> None:
    load_actpac_json(FILE_LOC_CATS, CAT_NUMS, 'category nums')


def load_playlist_nums() -> None:
    load_actpac_json(FILE_LOC_PLAS, PLA_NUMS, 'playlist nums')


def load_playlist_nums_rev() -> None:
    load_actpac_json(FILE_LOC_PLAS, PLA_NUMS_REV, 'playlist nums rev', reverse=True)


def load_tag_aliases() -> None:
    load_actpac_json(FILE_LOC_TAG_ALIASES, TAG_ALIASES, 'tag aliases', extract=False)


def load_tag_conflicts() -> None:
    load_actpac_json(FILE_LOC_TAG_CONFLICTS, TAG_CONFLICTS, 'tag conflicts', extract=False)

#
#
#########################################

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import List, Optional, Collection, Iterable, MutableSequence, Union, Dict, Tuple

from bigstrings import TAG_ALIASES, TAG_NUMS_DECODED, ART_NUMS_DECODED, CAT_NUMS_DECODED, PLA_NUMS_DECODED
from config import Config
from defs import TAGS_CONCAT_CHAR
from logger import Log
from rex import (
    re_replace_symbols, re_wtag, re_idval, re_uscore_mult, re_not_a_letter, re_numbered_or_counted_tag, re_or_group,
    re_neg_and_group, re_tags_to_process, re_bracketed_tag, re_tags_exclude_major1, re_tags_exclude_major2, re_tags_to_not_exclude,
    prepare_regex_fullmatch,
)
from util import assert_nonempty
from vinfo import VideoInfo

__all__ = (
    'filtered_tags', 'get_matching_tag', 'extract_id_or_group', 'valid_extra_tag', 'is_filtered_out_by_extra_tags',
    'valid_playlist_name', 'valid_playlist_id', 'valid_tags', 'valid_artists', 'valid_categories',
)


def valid_playlist_name(plist: str) -> Tuple[int, str]:
    try:
        plist_v = PLA_NUMS_DECODED[plist]
        plist_name, plist_numb = plist, int(plist_v)
        return (plist_numb, plist_name)
    except Exception:
        raise ValueError


def valid_playlist_id(plist: str) -> Tuple[int, str]:
    try:
        assert plist.isnumeric()
        for k, v in PLA_NUMS_DECODED.items():
            if v == plist:
                plist_name, plist_numb = k, int(plist)
                return (plist_numb, plist_name)
        assert False
    except Exception:
        raise ValueError


def valid_extra_tag(tag: str, log=True) -> str:
    try:
        all_valid = True
        if tag.startswith('('):
            assert is_valid_or_group(tag)
            all_valid &= is_valid_id_or_group(tag) or all_extra_tags_valid(tag[1:-1].split('~'))
        elif tag.startswith('-('):
            assert is_valid_neg_and_group(tag)
            all_valid &= all_extra_tags_valid(tag[2:-1].split(','))
        else:
            assert is_valid_extra_tag(tag[1:] if tag.startswith('-') else tag)
        assert all_valid
        return tag.lower().replace(' ', '_')
    except Exception:
        if log:
            Log.fatal(f'Fatal: invalid extra tag or group: \'{tag}\'!')
        raise ValueError


def valid_tags(tags_str: str) -> str:
    all_valid = True
    tag_ids = set()
    if len(tags_str) > 0:
        for tag in tags_str.split(','):
            try:
                tag_ids.update(get_tag_num(tag_ex, True) for tag_ex in assert_nonempty(expand_tags(tag)))
            except Exception:
                Log.error(f'Error: invalid tag: \'{tag}\'!')
                all_valid = False
                continue
    if not all_valid:
        Log.fatal('Fatal: Invalid tags found!')
        raise ValueError
    return ','.join(sorted(tag_ids))


def valid_artists(artists_str: str) -> str:
    all_valid = True
    artist_ids = set()
    if len(artists_str) > 0:
        for artist in artists_str.split(','):
            try:
                artist_ids.update(get_artist_num(artist_ex, True) for artist_ex in assert_nonempty(expand_artists(artist)))
            except Exception:
                Log.error(f'Error: invalid artist: \'{artist}\'!')
                all_valid = False
                continue
    if not all_valid:
        Log.fatal('Fatal: Invalid artists found!')
        raise ValueError
    return ','.join(sorted(artist_ids))


def valid_categories(categories_str: str) -> str:
    all_valid = True
    category_ids = set()
    if len(categories_str) > 0:
        for category in categories_str.split(','):
            try:
                category_ids.update(get_category_num(category_ex, True) for category_ex in assert_nonempty(expand_categories(category)))
            except Exception:
                Log.error(f'Error: invalid category: \'{category}\'!')
                all_valid = False
                continue
    if not all_valid:
        Log.fatal('Fatal: Invalid categories found!')
        raise ValueError
    return ','.join(sorted(category_ids))


def is_wtag(tag: str) -> bool:
    return not not re_wtag.fullmatch(tag)


def all_extra_tags_valid(tags: List[str]) -> bool:
    all_valid = True
    for t in tags:
        if not is_valid_extra_tag(t):
            all_valid = False
            Log.error(f'Error: invalid extra tag: \'{t}\'!')
    return all_valid


def is_valid_extra_tag(extag: str) -> bool:
    return is_wtag(extag) or is_valid_tag(extag) or is_valid_artist(extag) or is_valid_category(extag)


def get_tag_num(tag: str, assert_=False) -> Optional[str]:
    return TAG_NUMS_DECODED[tag] if assert_ else TAG_NUMS_DECODED.get(tag)


def is_valid_tag(tag: str) -> bool:
    return not not get_tag_num(tag)


def get_artist_num(artist: str, assert_=False) -> Optional[str]:
    return ART_NUMS_DECODED[artist] if assert_ else ART_NUMS_DECODED.get(artist)


def is_valid_artist(artist: str) -> bool:
    return not not get_artist_num(artist)


def get_category_num(category: str, assert_=False) -> Optional[str]:
    return CAT_NUMS_DECODED[category] if assert_ else CAT_NUMS_DECODED.get(category)


def is_valid_category(category: str) -> bool:
    return not not get_category_num(category)


def is_valid_neg_and_group(andgr: str) -> bool:
    return not not re_neg_and_group.fullmatch(andgr)


def is_valid_or_group(orgr: str) -> bool:
    return not not re_or_group.fullmatch(orgr)


def expand_tags(pwtag: str) -> Iterable[str]:
    expanded_tags = set()
    if not is_wtag(pwtag):
        expanded_tags.add(pwtag)
    else:
        Log.debug(f'Expanding tags from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for tag in TAG_NUMS_DECODED:
            if pat.fullmatch(tag):
                Log.debug(f' - \'{tag}\'')
                expanded_tags.add(tag)
    return expanded_tags


def expand_artists(pwtag: str) -> Iterable[str]:
    expanded_artists = set()
    if not is_wtag(pwtag):
        expanded_artists.add(pwtag)
    else:
        Log.debug(f'Expanding artists from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for artist in ART_NUMS_DECODED:
            if pat.fullmatch(artist):
                Log.debug(f' - \'{artist}\'')
                expanded_artists.add(artist)
    return expanded_artists


def expand_categories(pwtag: str) -> Iterable[str]:
    expanded_categories = set()
    if not is_wtag(pwtag):
        expanded_categories.add(pwtag)
    else:
        Log.debug(f'Expanding categories from wtag \'{pwtag}\'...')
        pat = prepare_regex_fullmatch(normalize_wtag(pwtag))
        for category in CAT_NUMS_DECODED:
            if pat.fullmatch(category):
                Log.debug(f' - \'{category}\'')
                expanded_categories.add(category)
    return expanded_categories


def normalize_wtag(wtag: str) -> str:
    wtag_freplacements = {
        '?': '\u203D', '*': '\u20F0', '(': '\u2039', ')': '\u203A',
        # '[': '\u2018', ']': '\u2019', '{': '\u201C', '}': '\u201D',
        '.': '\u1FBE', ',': '\u201A', '+': '\u2020', '-': '\u2012',
    }
    wtag_breplacements: Dict[str, str] = {wtag_freplacements[k]: k for k in wtag_freplacements}
    wtag_breplacements[wtag_freplacements['(']] = '(?:'
    chars_need_escaping = list(wtag_freplacements.keys())[2:]
    escape_char = '`'
    escape = escape_char in wtag
    if escape:
        for fk in wtag_freplacements:
            wtag = wtag.replace(f'{escape_char}{fk}', wtag_freplacements[fk])
    for c in chars_need_escaping:
        wtag = wtag.replace(c, f'\\{c}')
    wtag = wtag.replace('*', '.*').replace('?', '.').replace(escape_char, '')
    if escape:
        for bk in wtag_breplacements:
            wtag = wtag.replace(f'{bk}', wtag_breplacements[bk])
    return wtag


def get_matching_tag(wtag: str, mtags: Iterable[str], *, force_regex=False) -> Optional[str]:
    if not is_wtag(wtag) and not force_regex:
        return wtag if wtag in mtags else None
    pat = prepare_regex_fullmatch(normalize_wtag(wtag))
    for htag in mtags:
        if pat.fullmatch(htag):
            return htag
    return None


def get_or_group_matching_tag(orgr: str, mtags: Iterable[str]) -> Optional[str]:
    for tag in orgr[1:-1].split('~'):
        mtag = get_matching_tag(tag, mtags)
        if mtag:
            return mtag
    return None


def get_neg_and_group_matches(andgr: str, mtags: Iterable[str]) -> List[str]:
    matched_tags = list()
    for wtag in andgr[2:-1].split(','):
        mtag = get_matching_tag(wtag, mtags, force_regex=True)
        if not mtag:
            return []
        matched_tags.append(mtag)
    return matched_tags


def is_valid_id_or_group(orgr: str) -> bool:
    return is_valid_or_group(orgr) and all(re_idval.fullmatch(tag) for tag in orgr[1:-1].split('~'))


def extract_id_or_group(ex_tags: MutableSequence[str]) -> List[int]:
    """May alter the input container!"""
    for i in range(len(ex_tags)):
        orgr = ex_tags[i]
        if is_valid_id_or_group(orgr):
            del ex_tags[i]
            return [int(tag.replace('id=', '')) for tag in orgr[1:-1].split('~')]
    return []


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
    norm_str = r'[ ()\[\]_\'"]'
    for i, wtag in enumerate(wtags):
        wtag_begin = '' if wtag.startswith("*") else '*' if wtag.startswith(tuple(norm_str[1:-1].split())) else f'*{norm_str}'
        wtag_end = '' if wtag.endswith("*") else '*' if wtag.endswith(tuple(norm_str[1:-1].split())) else f'{norm_str}*'
        wtags[i] = f'{wtag_begin}{wtag.replace("_", " ")}{wtag_end}'

    conv_tag = (
        f'-({",".join(wtags)})' if tagtype == 1 else f'({"~".join(wtags)})' if tagtype == 2 else
        f'-{"".join(wtags)}' if tagtype == 3 else f'{"".join(wtags)}'
    )
    return conv_tag


def match_text(ex_tag: str, text: str, group_type='') -> Union[None, str, List[str]]:
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


def is_filtered_out_by_extra_tags(vi: VideoInfo, tags_raw: List[str], extra_tags: List[str],
                                  id_seq: List[int], subfolder: str, id_seq_ex: List[int] = None) -> bool:
    suc = True
    sname = f'{f"[{subfolder}] " if subfolder else ""}Video {vi.sname}'
    if id_seq and vi.id not in id_seq and not (id_seq_ex and vi.id in id_seq_ex):
        suc = False
        Log.trace(f'{sname} isn\'t contained in id list \'{str(id_seq)}\'. Skipped!')

    for extag in extra_tags:
        if extag.startswith('('):
            or_match_base = get_or_group_matching_tag(extag, tags_raw)
            or_match_titl = match_text(extag, vi.title, 'or') if Config.check_title_pos and vi.title else None
            or_match_desc = match_text(extag, vi.description, 'or') if Config.check_description_pos and vi.description else None
            if or_match_base:
                Log.trace(f'{sname} has BASE POS match: \'{str(or_match_base)}\'')
            if or_match_titl:
                Log.trace(f'{sname} has TITL POS match: \'{str(or_match_titl)}\'')
            if or_match_desc:
                Log.trace(f'{sname} has DESC POS match: \'{str(or_match_desc)}\'')
            if not bool(or_match_base or or_match_titl or or_match_desc):
                suc = False
                Log.trace(f'{sname} misses required tag matching \'{extag}\'. Skipped!')
        elif extag.startswith('-('):
            neg_matches = get_neg_and_group_matches(extag, tags_raw)
            for conf, cn, td in zip(
                (Config.check_title_neg, Config.check_description_neg),
                ('TITL', 'DESC'),
                (vi.title, vi.description)
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
            mtag = get_matching_tag(my_extag, tags_raw)
            if negative is False and mtag:
                Log.trace(f'{sname} has BASE POS match: \'{mtag}\'')
            for conf, cn, np, td in zip(
                (Config.check_title_pos, Config.check_title_neg, Config.check_description_pos, Config.check_description_neg),
                ('TITL', 'TITL', 'DESC', 'DESC'),
                ('POS', 'NEG', 'POS', 'NEG'),
                (vi.title, vi.title, vi.description, vi.description)
            ):
                if conf and td and ((np == 'NEG') == negative) and not mtag:
                    mtag = match_text(my_extag, td)
                    if mtag:
                        mtag = f'{mtag[:100]}...'
                        if negative is False:
                            Log.trace(f'{sname} has {cn} {np} match: \'{mtag}\'')
            if mtag is not None and negative:
                suc = False
                Log.info(f'{sname} contains excluded tag \'{mtag}\'. Skipped!')
            elif mtag is None and not negative:
                suc = False
                Log.trace(f'{sname} misses required tag matching \'{my_extag}\'. Skipped!')
    return not suc


def filtered_tags(tags_list: Collection[str]) -> str:
    if len(tags_list) == 0:
        return ''

    tags_list_final: List[str] = list()

    for tag in tags_list:
        tag = re_replace_symbols.sub('_', tag.replace('-', '').replace('\'', '').replace('.', ''))
        alias = TAG_ALIASES.get(tag)
        if alias is None and re_tags_to_process.match(tag) is None:
            continue

        tag = alias or tag

        # digital_media_(artwork)
        aser_match = re_bracketed_tag.match(tag)
        aser_valid = not not aser_match
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

#
#
#########################################

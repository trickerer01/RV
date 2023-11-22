# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import List, Optional, Collection, Iterable, Sequence, Tuple

from bigstrings import TAG_ALIASES, TAG_NUMS_DECODED, ART_NUMS_DECODED, CAT_NUMS_DECODED, PLA_NUMS_DECODED
from defs import TAGS_CONCAT_CHAR, LoggingFlags, PREFIX
from rex import (
    re_replace_symbols, re_wtag, re_idval, re_uscore_mult, re_not_a_letter, re_numbered_or_counted_tag, re_or_group,
    re_neg_and_group, re_tags_to_process, re_bracketed_tag, re_tags_exclude_major1, re_tags_exclude_major2, re_tags_to_not_exclude,
    prepare_regex_fullmatch,
)
from logger import Log

__all__ = (
    'filtered_tags', 'get_matching_tag', 'try_parse_id_or_group', 'valid_extra_tag', 'is_filtered_out_by_extra_tags',
    'valid_tags', 'valid_artists', 'valid_categories', 'valid_playlist_name', 'valid_playlist_id',
)


def valid_playlist_name(plist: str) -> Tuple[int, str]:
    try:
        plist_v = PLA_NUMS_DECODED.get(plist)
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


def valid_extra_tag(tag: str) -> str:
    try:
        if tag[0] == '(':
            assert is_valid_or_group(tag)
        elif tag.startswith('-('):
            assert is_valid_neg_and_group(tag)
        else:
            assert is_valid_extra_tag(tag[1:] if tag.startswith('-') else tag)
        return tag.lower().replace(' ', '_')
    except Exception:
        Log.fatal(f'Fatal: invalid extra tag or group: \'{tag}\'!')
        raise ValueError


def valid_tags(tags_str: str) -> str:
    all_valid = True
    tag_ids = set()
    if len(tags_str) > 0:
        for tag in tags_str.split(','):
            try:
                tag_ids.add(get_tag_num(tag))
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
                artist_ids.add(get_artist_num(artist))
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
                category_ids.add(get_category_num(category))
            except Exception:
                Log.error(f'Error: invalid category: \'{category}\'!')
                all_valid = False
                continue
    if not all_valid:
        Log.fatal('Fatal: Invalid categories found!')
        raise ValueError
    return ','.join(sorted(category_ids))


def is_non_wtag(tag: str) -> bool:
    return not re_wtag.fullmatch(tag)


def is_valid_extra_tag(extag: str) -> bool:
    return (not is_non_wtag(extag)) or is_valid_tag(extag) or is_valid_artist(extag) or is_valid_category(extag)


def get_tag_num(tag: str) -> Optional[str]:
    return TAG_NUMS_DECODED.get(tag)


def is_valid_tag(tag: str) -> bool:
    return (not not get_tag_num(tag))


def get_artist_num(artist: str) -> Optional[str]:
    return ART_NUMS_DECODED.get(artist)


def is_valid_artist(artist: str) -> bool:
    return (not not get_artist_num(artist))


def get_category_num(category: str) -> Optional[str]:
    return CAT_NUMS_DECODED.get(category)


def is_valid_category(category: str) -> bool:
    return (not not get_category_num(category))


def is_valid_neg_and_group(andgr: str) -> bool:
    return not not re_neg_and_group.fullmatch(andgr)


def is_valid_or_group(orgr: str) -> bool:
    return not not re_or_group.fullmatch(orgr)


def normalize_wtag(wtag: str) -> str:
    for c in '.[]()-+':
        wtag = wtag.replace(c, f'\\{c}')
    return wtag.replace('*', '.*').replace('?', '.')


def get_matching_tag(wtag: str, mtags: Iterable[str]) -> Optional[str]:
    if is_non_wtag(wtag):
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


def is_neg_and_group_matches(andgr: str, mtags: Iterable[str]) -> bool:
    return all(get_matching_tag(wtag, mtags) is not None for wtag in andgr[2:-1].split(','))


def is_valid_id_or_group(orgr: str) -> bool:
    return is_valid_or_group(orgr) and all(re_idval.fullmatch(tag) for tag in orgr[1:-1].split('~'))


def try_parse_id_or_group(ex_tags: Sequence[str]) -> List[int]:
    if len(ex_tags) == 1:
        orgr = ex_tags[0]
        if is_valid_id_or_group(orgr):
            return [int(tag.replace('id=', '')) for tag in orgr[1:-1].split('~')]
    return []


def trim_undersores(base_str: str) -> str:
    return re_uscore_mult.sub('_', base_str).strip('_')


def is_filtered_out_by_extra_tags(idi: int, tags_raw: Collection[str], extra_tags: List[str], is_extra_seq: bool, subfolder: str) -> bool:
    suc = True
    sname = f'{PREFIX}{idi:d}.mp4'
    sfol = f'[{subfolder}] ' if subfolder else ''
    if len(extra_tags) > 0:
        if is_extra_seq:
            assert len(extra_tags) == 1
            id_sequence = try_parse_id_or_group(extra_tags)
            assert id_sequence
            if idi not in id_sequence:
                suc = False
                Log.trace(f'{sfol}Video {sname} isn\'t contained in id list \'{str(id_sequence)}\'. Skipped!',
                          LoggingFlags.LOGGING_EX_MISSING_TAGS)
            return not suc

        for extag in extra_tags:
            if extag[0] == '(':
                if get_or_group_matching_tag(extag, tags_raw) is None:
                    suc = False
                    Log.trace(f'{sfol}Video {sname} misses required tag matching \'{extag}\'. Skipped!',
                              LoggingFlags.LOGGING_EX_MISSING_TAGS)
            elif extag.startswith('-('):
                if is_neg_and_group_matches(extag, tags_raw):
                    suc = False
                    Log.info(f'{sfol}Video {sname} contains excluded tags combination \'{extag[1:]}\'. Skipped!',
                             LoggingFlags.LOGGING_EX_EXCLUDED_TAGS)
            else:
                my_extag = extag[1:] if extag[0] == '-' else extag
                mtag = get_matching_tag(my_extag, tags_raw)
                if mtag is not None and extag[0] == '-':
                    suc = False
                    Log.info(f'{sfol}Video {sname} contains excluded tag \'{mtag}\'. Skipped!',
                             LoggingFlags.LOGGING_EX_EXCLUDED_TAGS)
                elif mtag is None and extag[0] != '-':
                    suc = False
                    Log.trace(f'{sfol}Video {sname} misses required tag matching \'{my_extag}\'. Skipped!',
                              LoggingFlags.LOGGING_EX_MISSING_TAGS)
    return not suc


def filtered_tags(tags_list: Collection[str]) -> str:
    if len(tags_list) == 0:
        return ''

    tags_list_final = list()  # type: List[str]

    for tag in tags_list:
        tag = re_replace_symbols.sub('_', tag.replace('-', '').replace('\'', '').replace('.', ''))
        if TAG_ALIASES.get(tag) is None and re_tags_to_process.match(tag) is None:
            continue

        alias = TAG_ALIASES.get(tag)
        if alias:
            tag = alias

        # digital_media_(artwork)
        aser_match = re_bracketed_tag.match(tag)
        aser_valid = False
        if aser_match:
            major_skip_match1 = re_tags_exclude_major1.match(aser_match.group(1))
            major_skip_match2 = re_tags_exclude_major2.match(aser_match.group(2))
            if major_skip_match1 or major_skip_match2:
                continue
            stag = trim_undersores(aser_match.group(1))
            if len(stag) >= 17:
                continue
            tag = stag
            aser_valid = True
        elif re_tags_to_not_exclude.match(tag) is None:
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
                for i, c in enumerate(tag):  # type: int, str
                    if (i == 0 or tag[i - 1] == '_') and c.isalpha():
                        tag = f'{tag[:i]}{c.upper()}{tag[i + 1:]}'
            tags_list_final.append(tag)

    return trim_undersores(TAGS_CONCAT_CHAR.join(sorted(tags_list_final)))

#
#
#########################################

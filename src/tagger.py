# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from base64 import b64decode
from json import loads
from re import compile as re_compile, fullmatch as re_fullmatch, match as re_match, sub as re_sub
from typing import List, Dict, Optional

from defs import TAG_NUMS_ENCODED


TAG_NUMS_DECODED = loads(b64decode(TAG_NUMS_ENCODED))  # type: Dict[str, str]

re_replace_symbols = re_compile(
    r'[^0-9a-zA-Z_+()\[\]]+'
)

# used with re.sub
# noinspection RegExpAnonymousGroup
re_numbered_or_counted_tag = re_compile(
    r'^(?!rule_?\d+)1?([^\d]+?)(?:_?\d+|s)?$'
)

re_tags_to_process = re_compile(
    r'^(?:.+?_warc.+?|(?:[a-z]+?_)?elf|drae.{3}|tent[a-z]{3}es|(?:bell[a-z]|sto[a-z]{4})_bul[a-z]{2,3}|inf[a-z]{5}n|egg(?:_[a-z]{3,9}|s)?|'
    r'[a-z]{4}hral_i.+?|(?:\d{1,2}\+?)?(?:boys?|girls?|fu[a-z]{2}(?:[a-z]{4}|s)?|in[d-v]{2}cts?|monsters?)|succ[a-z]{4}|'
    r'bbw|dog|f(?:acesitting|ur)|hmv|pmv|tar|c(?:\.c\.|um)|monster_girl|'
    r'[^(]+\([^)]+\).*?|[a-z_\-]+\d+?|\d{2,4}[a-z_\-]+?|[a-z_]{2,15}sfm|[^_]+_pov|fu[a-z]{2}(?:/|_(?:on|with)_)[a-z]{4}|'
    r'[a-z][a-z_]{3,9}|[a-g]ea?st[a-z]{6}|[lapymg]{3})$'
)

re_tags_exclude_major1 = re_compile(
    r'^(?:[234][dk]|h(?:d|ero_outfit)|level_up|p(?:ainting|rotagonist)|tagme|'
    r'war(?:rior|lock)|paladin|hunt(?:er|ress)|rogue|priest(?:ess)?|d(?:e(?:ath_?knight|mon_?hunt(?:er|ress))|ruid(?:ess)?)|'  # wow
    r'shaman|m(?:age|onk)|alliance|horde|'  # wow
    r'[a-z]pose|[\da-z_\-]{16,}).*?$'
)
re_tags_exclude_major2 = re_compile(
    r'^(?:a(?:r(?:mor|twork)|udio)|cosplay|m(?:ap|eme|odel)|object|rwby|software)$'
)

re_tags_to_not_exclude = re_compile(
    r'^(?:'
    r'a(?:lien(?:_.+?|s)?|m(?:azonium|b(?:er|rosine))|n(?:al|gel|imopron|thro)|r(?:achnid|iel)|yasz)|'  # a
    r'b(?:a(?:ndoned|ronstrap|tesz)|dsm|e(?:a(?:st|r)|n_10|wyx)|i(?:gjohnson|mbo|oshock|r(?:dway|th))|'  # b
    r'l(?:ack(?:ed|j.+?)?|o(?:od|wjob))|o(?:dysuit|ndage|vine))|'  # b
    r'c(?:a(?:ge|nine|t(?:_girl|woman))|entaur|hained|lass_sweeb|o(?:lonelyobo|ot27|rset)|reampie|u(?:ckold|m))|'  # c
    r'd(?:ark_elf|e(?:a(?:dpool|ath)|er|mons?|ntol|rpixon|zmall)|i(?:ablo|gimon|ldo)|mitrys|o(?:cking|gs?|nkey|om)|ragon(?:ess)?|va)|'  # d
    r'e(?:ggs|lves|nema|quine|xtreme|zria)|'  # e
    r'f(?:a(?:cesitting|rt(?:ing)?)|e(?:m(?:boy|dom|shep)|ral)|isting|o(?:rtnite|x_girl)|rozen|u(?:rry|ta(?:holic|nari)))|'  # f
    r'g(?:a(?:ngbang|p(?:e|ing))|craw|i(?:ant(?:ess)?|fdoozer)|o(?:blins?|o_girl|re|th)|r(?:an(?:d.+?|ny)|eatb8)|'  # g
    r'u(?:il(?:mon|tyk)|robase))|'  # g
    r'h(?:a(?:iry|l(?:f_elf|o)|ndjob)|e(?:lena|tero)|i(?:gh_elf|nca_p|ve)|mv|'  # h
    r'o(?:ovesart|r(?:ror|se(?:_?(?:cock|girl|s(?:ex)?))?)|usewife)|rfidy|ulk|v54rdsl|ydrafxx)|'  # h
    r'i(?:cedev|demi|n(?:c(?:est|ubus)|justice|sect(?:oid|s)?)|tsmort.+?)|'  # i
    r'j(?:a(?:ckerman|il)|uicyneko)|'  # j
    r'k(?:a(?:isa|m(?:adeva|inak.+?)|sdaq|kami)|eycock|hajiit|idnapped|not(?:t(?:ed|ing))?|o(?:opa|rra)|reamu|udoart)|'  # k
    r'l(?:a(?:osduude|tex)|e(?:ather|eterr|s(?:bian|dias))|ikkezg|o(?:op|punny))|'  # l
    r'm(?:a(?:chine|g(?:ic|mallow)|id|jora|le(?:_(?:male|only)|sub)?)|ccree|e(?:klab|ltrib|ru|troid)|'  # m
    r'i(?:dget|driff|ku|lf|n(?:ecraft|otaur|us8)|ruko|s(?:syb|tress))|o(?:nster(?:_.+?|s)?|rty|xxy))|'  # m
    r'n(?:a(?:g(?:a|oonimation)|vi)|o(?:ih(?:_2)|name.+?)|ualia|yl.+?)|'  # n
    r'o(?:gre|ne_piece|p(?:helia|iumud)|r(?:al|cs|gy)|verwatch)|'  # o
    r'p(?:a(?:inful|ladins|ragon|uline)|ersona(?:_\d)?|i(?:kachu|ssing)|mv|o(?:kemon|ny|wergirl)|'  # p
    r'r(?:e(?:dator|gnant)|ison(?:er)?|olapse))|'  # p
    r'r(?:a(?:d(?:eong3d|roachhd)|p(?:e|unzel)|tchet)|e(?:becca|dapple2|ey.+?)|i(?:eklig|kolo)|opeboundart|u(?:bber|kia)|yona)|'  # r
    r's(?:a(?:dako|itou|mira|ntalol|yuri)|ca(?:lie|t)|e(?:cazz?|lf_fuck)|hackles|i(?:lkymilk|ms(?:_\d)?|th_jedi)|k(?:arlet|yrim)|'  # s
    r'l(?:ave|eepy_b|yxxx24)|mell|o(?:ft_vore|lo(?:_.+?)?|phi[ae]|r(?:aka|idormi))|'  # s
    r'p(?:i(?:der|troast|zzy)|l(?:atoon|ucky.+?)|o(?:ks|nty))|t(?:a(?:lkek|r(?:_.+?|craft|fox))|ra(?:ight|pon)|udio34)|'
    r'uccubus|ylveon)|'  # s
    r't(?:a(?:ga|ker_pov)|e(?:k(?:ken|tah.+?)|ntacles?|xelnaut)|he(?:_sims|count|hoaxxx)|ied|o(?:gruta|rture|uhou)|'  # t
    r'r(?:a(?:ns|ps?)|inity)|soni|y(?:viania))|'  # t
    r'u(?:g(?:ly(?:_man)?|oira)|n(?:birth|de(?:ad|rtale))|r(?:ethral|iel))|'  # u
    r'v(?:a(?:lorant|mpire)|i(?:cer34|olence|rgin)|o(?:mit|re))|'  # v
    r'w(?:ar(?:craft|frame|hammer)|eebuv.+?|hip|orld_of_warcraft)|'  # w
    r'x(?:_(?:com(?:_\d)?|ray)|enomorph)|'  # x
    r'z(?:o(?:mbies?|otopia))|'  # z
    r'\d{1,2}\+?_?(?:animal|boy|futa|girl|monster)s?.*?'  # 0-9
    r')$'
)

TAG_ALIASES = {
    'aela_the_huntress_(world_of_warcraft)': 'world_of_warcraft',
    'darnassus_(world_of_warcraft)': 'world_of_warcraft',
    'deathwing_(world_of_warcraft)': 'world_of_warcraft',
    'demon_hunter_(world_of_warcraft)': 'world_of_warcraft',
    'eredar_(world_of_warcraft)': 'world_of_warcraft',
    'felhunter_(world_of_warcraft)': 'world_of_warcraft',
    'felina_(world_of_warcraft)': 'world_of_warcraft',
    'felstalker_(world_of_warcraft)': 'world_of_warcraft',
    'garrosh_hellscream__(world_of_warcraft)': 'world_of_warcraft',
    'gnome_(world_of_warcraft)': 'world_of_warcraft',
    'goblin_(world_of_warcraft)': 'world_of_warcraft',
    'human_(world_of_warcraft)': 'world_of_warcraft',
    'illidan_(world_of_warcraft)': 'world_of_warcraft',
    'jaina_proudmoore_(world_of_warcraft)': 'world_of_warcraft',
    'lylly_(world_of_warcraft)': 'world_of_warcraft',
    'sally_whitemane_(world_of_warcraft)': 'world_of_warcraft',
    'sylvanas_windrunner_(world_of_warcraft)': 'world_of_warcraft',
    'tess_(world_of_warcraft)': 'world_of_warcraft',
    'tyrande_whisperwind_(world_of_warcraft)': 'world_of_warcraft',
    'thrall_(world_of_warcraft)': 'world_of_warcraft',
    'valeera_(world_of_warcraft)': 'world_of_warcraft',
    'vulpera_(world_of_warcraft)': 'world_of_warcraft',
    'worgen_(world_of_warcraft)': 'world_of_warcraft',
    'wrathion_(world_of_warcraft)': 'world_of_warcraft',
    'pmv': 'PMV',
    'hmv': 'HMV',
    'sfmpmv': 'PMV',
    'sfmhmv': 'HMV',
}


def is_non_wtag(tag: str) -> bool:
    return not re_fullmatch(r'^[^?*]*[?*].*?$', tag)


def is_non_idtag(tag: str) -> bool:
    return not re_fullmatch(r'^id=\d+?$', tag)


def is_valid_tag(tag: str) -> bool:
    return not not TAG_NUMS_DECODED.get(tag)


def assert_valid_tag(tag: str) -> None:
    assert is_valid_tag(tag)


def is_valid_neg_and_group(andgr: str) -> bool:
    return (len(andgr) >= len('-(.,.)') and andgr.startswith('-(') and andgr.endswith(')') and
            andgr.find(',') != -1 and len(andgr[2:-1].split(',', 1)) == 2)


def validate_neg_and_group(andgr: str) -> None:
    assert is_valid_neg_and_group(andgr)


def is_valid_or_group(orgr: str) -> bool:
    if len(orgr) >= len('(.~.)') and orgr[0] == '(' and orgr[-1] == ')' and orgr.find('~') != -1 and len(orgr[1:-1].split('~', 1)) == 2:
        return all(is_valid_tag(tag) for tag in orgr[1:-1].split('~') if is_non_wtag(tag) and is_non_idtag(tag))
    return False


def assert_valid_or_group(orgr: str) -> None:
    assert is_valid_or_group(orgr)


def get_matching_tag(wtag: str, mtags: List[str]) -> Optional[str]:
    if not is_non_wtag(wtag):
        escaped_tag = (
            wtag.replace('.', '\\.').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('-', '\\-')
            .replace('*', '.*').replace('?', '.')
        )
        pat = re_compile(rf'^{escaped_tag}$')
        for htag in mtags:
            if re_fullmatch(pat, htag):
                return htag
        return None
    else:
        return wtag if wtag in mtags else None


def get_or_group_matching_tag(orgr: str, mtags: List[str]) -> Optional[str]:
    assert len(orgr) >= len('(.~.)')
    assert orgr[0] == '('
    for tag in orgr[1:-1].split('~'):
        mtag = get_matching_tag(tag, mtags)
        if mtag:
            return mtag
    return None


def is_neg_and_group_matches(andgr: str, mtags: List[str]) -> bool:
    validate_neg_and_group(andgr)
    return all(get_matching_tag(wtag, mtags) is not None for wtag in andgr[2:-1].split(','))


def is_valid_id_or_group(orgr: str) -> bool:
    if is_valid_or_group(orgr):
        return all(re_fullmatch(r'^id=\d+?$', tag) for tag in orgr[1:-1].split('~'))
    return False


def try_parse_id_or_group(ex_tags: List[str]) -> Optional[List[int]]:
    if len(ex_tags) == 1:
        orgr = ex_tags[0]
        if is_valid_id_or_group(orgr):
            return [int(tag.replace('id=', '')) for tag in orgr[1:-1].split('~')]
    return None


def trim_undersores(base_str: str) -> str:
    ret_str = re_sub(r'_{2,}', '_', base_str)
    if len(ret_str) != 0:
        if len(ret_str) >= 2 and ret_str[0] == '_' and ret_str[-1] == '_':
            ret_str = ret_str[1:-1]
        elif ret_str[-1] == '_':
            ret_str = ret_str[:-1]
        elif ret_str[0] == '_':
            ret_str = ret_str[1:]
    return ret_str


def filtered_tags(tags_list: List[str]) -> str:
    if len(tags_list) == 0:
        return ''

    tags_list_final = []  # type: List[str]

    for tag in tags_list:
        tag = re_sub(re_replace_symbols, '_', tag.replace('-', '').replace('\'', '').replace('.', ''))
        if TAG_ALIASES.get(tag) is None and re_match(re_tags_to_process, tag) is None:
            continue

        alias = TAG_ALIASES.get(tag)
        if alias:
            tag = alias

        # digital_media_(artwork)
        aser_match = re_match(r'^([^(]+)\(([^)]+)\).*$', tag)
        aser_valid = False
        if aser_match:
            major_skip_match1 = re_match(re_tags_exclude_major1, aser_match.group(1))
            major_skip_match2 = re_match(re_tags_exclude_major2, aser_match.group(2))
            if major_skip_match1 or major_skip_match2:
                continue
            stag = trim_undersores(aser_match.group(1))
            if len(stag) >= 17:
                continue
            tag = stag
            aser_valid = True
        elif re_match(re_tags_to_not_exclude, tag) is None:
            continue

        tag = trim_undersores(tag)

        do_add = True
        if len(tags_list_final) > 0:
            nutag = re_sub(r'[^a-z]+', '', re_sub(re_numbered_or_counted_tag, r'\1', tag))
            # try and see
            # 1) if this tag can be consumed by existing tags
            # 2) if this tag can consume existing tags
            for i in reversed(range(len(tags_list_final))):
                t = re_sub(re_numbered_or_counted_tag, r'\1', tags_list_final[i].lower())
                nut = re_sub(r'[^a-z]+', '', t)
                if len(nut) >= len(nutag) and (nutag in nut):
                    do_add = False
                    break
            if do_add:
                for i in reversed(range(len(tags_list_final))):
                    t = re_sub(re_numbered_or_counted_tag, r'\1', tags_list_final[i].lower())
                    nut = re_sub(r'[^a-z]+', '', t)
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

    # tags_list_final = []
    # [tags_list_final.extend(tag_list) for tag_list in tags_dict.values() if len(tag_list) != 0]

    return trim_undersores('_'.join(sorted(tags_list_final)))

#
#
#########################################

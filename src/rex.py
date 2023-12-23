# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile
from typing import Pattern

from defs import QUALITIES, EXTENSIONS_V

# common
re_media_filename = re_compile(fr'^(?:rv_)?(\d+).*?(?:_({"|".join(QUALITIES)}))?(?:_py(?:dw|pv))?\.(?:{"|".join(EXTENSIONS_V)})$')
re_replace_symbols = re_compile(r'[^0-9a-zA-Z.,_+%\-()\[\] ]+')
re_ext = re_compile(r'(\.[^&]{3,5})&')
# re_private_video = re_compile(r'^This is a private video\..*?$')
# pages
re_page_entry = re_compile(r'videos/(\d+)/')
re_preview_entry = re_compile(r'/(\d+)_preview[^.]*?\.([^/]+)/')
re_paginator = re_compile(r'from(?:_(?:albums|videos))?:(\d+)')
# validators
re_non_search_symbols = re_compile(r'[^\da-zA-Z._+\-\[\]]')
re_session_id = re_compile(r'[a-z0-9]{26}')
# tagger
re_wtag = re_compile(r'^[^?*]*[?*].*?$')
re_idval = re_compile(r'^id=\d+?$')
re_uscore_mult = re_compile(r'_{2,}')
re_not_a_letter = re_compile(r'[^a-z]+')
re_bracketed_tag = re_compile(r'^([^(]+)\(([^)]+)\).*?$')
re_numbered_or_counted_tag = re_compile(r'^(?!rule_?\d+)1?([^\d]+?)(?:_?\d+|s)?$')
re_or_group = re_compile(r'^\([^~]+(?:~[^~]+)+\)$')
re_neg_and_group = re_compile(r'^-\([^,]+(?:,[^,]+)+\)$')

re_tags_to_process = re_compile(
    r'^(?:.+?_warc.+?|(?:[a-z]+?_)?elf|drae.{3}|tent[a-z]{3}es|(?:bell[a-z]|sto[a-z]{4})_bul[a-z]{2,3}|inf[a-z]{5}n|egg(?:_[a-z]{3,9}|s)?|'
    r'[a-z]{4}hral_i.+?|(?:\d{1,2}\+?)?(?:boys?|girls?|fu[a-z]{2}(?:[a-z]{4}|s)?|in[d-v]{2}cts?|monsters?)|succ[a-z]{4}|'
    r'bbw|dog|eel|f(?:acesitting|ur)|orc|hmv|pmv|tar|c(?:\.c\.|um)|d\.va|na\'vi|kai\'sa|gender.+?|'
    r'[^(]+\([^)]+\).*?|[a-z_\-]+\d+?|\d{2,4}[a-z_\-]+?|[a-z_]{2,15}sfm|[^_]+_pov|(?:fu|s)[a-z]{6}(?:/|_(?:on|with)_)[a-z]{4}(?:oy)?|'
    r'[a-z][a-z_]{3,12}|[a-g]ea?st[a-z]{6}|[lapymg]{3})$'
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
    r'a(?:i_content|lien(?:_.+?|s)?|m(?:azonium|b(?:er|rosine))|n(?:al|gel|imopron|thro)|r(?:achnid|iel)|yasz)|'  # a
    r'b(?:a(?:ndoned|ronstrap|tesz)|dsm|e(?:a(?:st|r)|lly_?b.+?|n_10|wyx)|i(?:gjohnson|mbo|oshock|r(?:dway|th))|'  # b
    r'l(?:ack(?:ed|j.+?)?|o(?:od|wjob))|o(?:dysuit|ndage|vine))|'  # b
    r'c(?:a(?:ge|nine|t(?:_girl|woman))|entaur|hained|lass_sweeb|o(?:lonelyobo|mic|ot27|rset)|reampie|u(?:ckold|m))|'  # c
    r'd(?:ark_elf|e(?:a(?:dpool|ath)|er|mons?|ntol|rpixon|zmall)|i(?:ablo|gimon|ldo)|mitrys|o(?:cking|gs?|nkey|om)|ragon(?:ess)?|va)|'  # d
    r'e(?:gg(?:_.+?|s)|lves|nema|quine|xtreme|zria)|'  # e
    r'f(?:a(?:cesitting|rt(?:ing)?)|e(?:m(?:boy|dom|shep)|ral)|isting|o(?:rtnite|x_girl)|rozen|'  # f
    r'u(?:rry|ta(?:_on_[a-p]{4}|holic|nari(?:_on_[a-p]{4})?)))|'  # f
    r'g(?:a(?:ngbang|p(?:e|ing))|craw|en(?:der.+|nariel)|i(?:ant(?:ess)?|fdoozer)|o(?:blins?|o_girl|re|th)|r(?:an(?:d.+?|ny)|eatb8)|'  # g
    r'u(?:il(?:mon|tyk)|robase))|'  # g
    r'h(?:a(?:iry|l(?:f_elf|o)|ndjob)|e(?:lena|tero)|i(?:gh_elf|nca_p|ve)|mv|'  # h
    r'o(?:ovesart|r(?:ror|se(?:_?(?:cock|girl|s(?:ex)?))?)|usewife)|rfidy|ulk|v54rdsl|ydrafxx)|'  # h
    r'i(?:cedev|demi|n(?:c(?:est|ubus)|justice|sect(?:oids?|s)?)|tsmort.+?)|'  # i
    r'j(?:a(?:ckerman|il)|uicyneko)|'  # j
    r'k(?:a(?:isa|m(?:adeva|inak.+?)|sdaq|kami)|eycock|hajiit|idnapped|not(?:t(?:ed|ing))?|o(?:opa|rra)|reamu|udoart)|'  # k
    r'l(?:a(?:osduude|tex(?:_.+?)?)|e(?:ather|eterr|s(?:bian|dias))|ikkezg|o(?:op|punny))|'  # l
    r'm(?:a(?:chine|g(?:gots?|ic|mallow)|id|jora|le(?:_(?:male|only)|sub)?)|ccree|e(?:klab|ltrib|ru|troid)|'  # m
    r'i(?:dget|driff|ku|lf|n(?:ecraft|otaur|us8)|ruko|s(?:syb|tress))|o(?:nster(?:_.+?|s)?|rty|xxy))|'  # m
    r'n(?:a(?:g(?:a|oonimation)|vi)|o(?:ih(?:_2)|name.+?)|ualia|yl.*?)|'  # n
    r'o(?:gre|mitome|ne_piece|p(?:helia|iumud)|r(?:al|cs|gy)|verwatch)|'  # o
    r'p(?:a(?:inful|ladins|ragon|uline)|ersona(?:_\d)?|i(?:kachu|ssing)|mv|o(?:kemon|ny|wergirl)|'  # p
    r'r(?:e(?:dator|gnant)|ison(?:er)?|olapse))|'  # p
    r'r(?:a(?:d(?:eong3d|roachhd)|p(?:e|unzel)|tchet)|e(?:becca|dapple2|ey.+?)|i(?:eklig|kolo)|opeboundart|u(?:bber|kia)|yona)|'  # r
    r's(?:a(?:dako|itou|mira|ntalol|yuri)|ca(?:lie|t)|e(?:cazz?|lf_fuck)|h(?:ackles|emale.+?)|i(?:lkymilk|ms(?:_\d)?|th_jedi)|'  # s
    r'k(?:arlet|yrim)|l(?:ave|eepy_b|yxxx24)|mell|o(?:ft_vore|lo(?:_.+?)?|phi[ae]|r(?:aka|idormi))|'  # s
    r'p(?:i(?:der|troast|zzy)|l(?:atoon|ucky.*?)|o(?:ks|nty))|t(?:a(?:lkek|r(?:_.+?|craft|fox))|ra(?:ight|pon)|udio34)|'  # s
    r'uccubus|ylveon)|'  # s
    r't(?:a(?:ga|ker_pov)|e(?:k(?:ken|tah.+?)|ntacles?|xelnaut)|he(?:_sims|count|hoaxxx)|ied|o(?:gruta|rture|uhou)|'  # t
    r'r(?:a(?:ns|ps?)|inity)|soni|utorial|y(?:viania))|'  # t
    r'u(?:g(?:ly(?:_man)?|oira)|n(?:birth|de(?:ad|rtale))|r(?:ethral|iel))|'  # u
    r'v(?:a(?:lorant|mpire)|i(?:cer34|olence|rgin)|o(?:mit|re))|'  # v
    r'w(?:ar(?:craft|frame|hammer)|eebu.*?|hip|or(?:ld_of_warcraft|ms?))|'  # w
    r'x(?:_(?:com(?:_\d)?|ray)|enomorph)|'  # x
    r'z(?:o(?:mbies?|otopia))|'  # z
    r'\d{1,2}\+?_?(?:animal|boy|futa|girl|monster)s?.*?'  # 0-9
    r')$'
)


# in-place
def prepare_regex_fullmatch(raw_string: str) -> Pattern[str]:
    return re_compile(rf'^{raw_string}$')

#
#
#########################################

# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile
from typing import Pattern

from defs import QUALITIES, EXTENSIONS_V, PREFIX

# common
re_media_filename = re_compile(fr'^(?:{PREFIX})?(\d+).*?(?:_({"|".join(QUALITIES)}))?\.(?:{"|".join(EXTENSIONS_V)})$')
re_infolist_filename = re_compile(fr'{PREFIX}!(?:tag|description|comment)s_\d+-\d+\.txt')
re_replace_symbols = re_compile(r'[^0-9a-zA-Z.,_+%!\-()\[\] ]+')
re_ext = re_compile(r'(\.[^&]{3,5})&')
re_time = re_compile(r'\d+(?::\d+){1,2}')
# re_private_video = re_compile(r'^This is a private video\..*?$')
# pages
re_page_entry = re_compile(r'video/(\d+)/')
re_preview_entry = re_compile(r'/(\d+)_preview[^.]*?\.([^/]+)/')
re_paginator = re_compile(r'from(?:_(?:albums|videos))?:(\d+)')
# validators
re_non_search_symbols = re_compile(r'[^\da-zA-Z._+\-\[\]]')
re_session_id = re_compile(r'[a-z0-9]{26}')
# tagger
re_wtag = re_compile(r'^(?:(?:[^?*|]*[?*|])|(?:[^`]*[`][()\[\]{}?*.,\-+])).*?$')
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
    r'bbw|dog|eel|f(?:acesitting|ur)|orc|hmv|pmv|tar|c(?:\.c\.|um)|d\.va|na\'vi|kai\'sa|monster_girl|gender.+?|'
    r'[^(]+\([^)]+\).*?|[a-z_\-]+\d+?|\d{2,4}[a-z_\-]+?|[a-z_]{2,15}sfm|[^_]+_pov|(?:fu|s)[a-z]{6}(?:/|_(?:on|with)_)[a-z]{4}(?:oy)?|'
    r'[a-z][a-z_]{2,10}|[a-g]ea?st[a-z]{6}|[lapymg]{3})$'
)
re_tags_exclude_major1 = re_compile(
    r'^(?:[234][dk]|h(?:d|ero_outfit)|level_up|p(?:ainting|rotagonist)|tagme|'
    r'war(?:rior|lock)|paladin|hunt(?:er|ress)|rogue|priest(?:ess)?|d(?:e(?:ath_?knight|mon_?hunt(?:er|ress))|ruid(?:ess)?)|'  # wow
    r'shaman|m(?:age|onk)|alliance|horde|'  # wow
    r'[a-z]pose|[\da-z_\-]{16,}).*?$'
)
re_tags_exclude_major2 = re_compile(
    r'^(?:a(?:r(?:mor|twork)|udio)|cosplay|m(?:ap|eme|odel)|object|rwby|software|va)$'
)
re_tags_to_not_exclude = re_compile(
    r'^(?:'
    r'a(?:i_content|lien(?:_.+?|s)?|m(?:azonium|b(?:er|rosine)|putee)|n(?:al(?:_beads)?|driod|gel|imopron|thro)|'  # a
    r'r(?:achnid|iel)|utofacial|yasz)|'  # a
    r'b(?:a(?:d_end|ndoned|ronstrap|t(?:_girl|esz))|b[mw]|dsm|e(?:a(?:st|r(?:_girl)?)|lly_?b.+?|n_10|stiality|wyx)|'  # b
    r'i(?:g(?:green|johnson)|mbo|oshock|r(?:dway|th))|l(?:ack(?:ed|j.+?)?|blind(?:fold)?|o(?:od|wjob))|'  # b
    r'o(?:dysuit|ndage|vine)|u(?:nny_?girl|tt_?plug))|'  # b
    r'c(?:a(?:ge|n(?:astus|i(?:d|ne|s))|ptured|t(?:_girl|woman)|ught)|entaur|hain(?:ed|s)|lass_sweeb|'  # c
    r'o(?:lonelyobo|m(?:ic|pilation)|ot27|rset)|reampie|u(?:ckold|m|ntboy))|'  # c
    r'd(?:ark_elf|e(?:a(?:dpool|ath)|e(?:r(?:_girl)?|vil_girl)|mons?|ntol|rpixon|zmall)|i(?:a(?:blo|per)|gimon|l(?:do|f))|'  # d
    r'm(?:itrys)|o(?:cking|gs?|nkey|om)|r(?:agon(?:ball|ess)?|unk)|va)|'  # d
    r'e(?:gg(?:_.+?|s)|l(?:f|ves)|nema|qui(?:d|ne)|xtreme|zria)|'  # e
    r'f(?:a(?:c(?:esitting|ial)|iry|rt(?:ing)?)|e(?:m(?:boy|dom|shep)|ral|tish)|isting|o(?:ot_?job|rtnite|x_girl)|'  # f
    r'r(?:o(?:g_girl|zen))|u(?:ck(?:_?(?:meat|train))|r(?:ry)?|ta(?:_on_[a-p]{4}|holic|nari(?:_on_[a-p]{4})?)))|'  # f
    r'g(?:a(?:g|ngbang|p(?:e|ing)|y)|craw|en(?:der.+|ie|nariel)|i(?:ant(?:ess)?|fdoozer)|o(?:blins?|o(?:_girl)?|re|th)|'  # g
    r'r(?:an(?:d.+?|ny)|eatb8)|u(?:il(?:mon|tyk)|ro))|'  # g
    r'h(?:a(?:iry(?:_.*?)?|l(?:f_elf|o)|ndjob)|e(?:l(?:ena|pless)|tero)|i(?:gh_elf|nca_p|tman|ve)|mv|'  # h
    r'o(?:ovesart|r(?:ror|se(?:_?(?:cock|fuck|girl|s(?:ex)?))?)|usewife)|rfidy|ulk|v54rdsl|ydrafxx)|'  # h
    r'i(?:cedev|demi|n(?:c(?:est|ubus)|flation|justice|sect(?:oids?|s)?)|tsmort.+?|wara)|'  # i
    r'j(?:a(?:ckerman|il)|uicyneko)|'  # j
    r'k(?:a(?:isa|m(?:adeva|inak.+?)|sdaq|kami)|eycock|hajiit|idnapped|not(?:t(?:ed|ing))?|o(?:opa|rra)|reamu|udoart)|'  # k
    r'l(?:a(?:osduude|tex(?:_.+?)?)|e(?:ather|eterr|s(?:bian|dias))|i(?:kkezg|zard_girl)|o(?:op|punny))|'  # l
    r'm(?:a(?:chine|g(?:gots?|ic|mallow)|id|jora|le(?:_(?:male|only)|sub)?|scara)|ccree|e(?:klab|ltrib|ru|troid)|'  # m
    r'i(?:dget|driff|ku|lf|n(?:ecraft|otaur|us8)|ruko|s(?:syb|tress))|lp|md|o(?:ana|nster(?:_.+?|s)?|rty|use_girl|xxy))|'  # m
    r'n(?:a(?:g(?:a|oonimation)|vi)|e(?:torare)|o(?:ih(?:_2)|name.+?|t_furry)|u(?:alia|n)|yl.*?)|'  # n
    r'o(?:gre|mitome|ne_piece|p(?:helia|iumud)|r(?:al|cs?|g(?:asms?|y))|tter_girl|v(?:erwatch|iposit.+?))|'  # o
    r'p(?:a(?:in(?:ful)?|ladins|ragon|uline)|e(?:rsona(?:_\d)?|t(?:_?play)?)|i(?:kachu|ssing)|lant_girl|mv|'  # p
    r'o(?:kemon|ny(?:_?girl)?|wergirl)|r(?:e(?:dator|gnant)|ison(?:er)?|olapse))|'  # p
    r'r(?:a(?:d(?:eong3d|roachhd)|p(?:e|unzel)|tchet)|e(?:becca|dapple2|ey.+?)|i(?:eklig|kolo)|opeboundart|'  # r
    r'u(?:bber|kia)|yona)|'  # r
    r's(?:a(?:dako|itou|mira|ntalol|yuri)|ca(?:lie|t)|e(?:cazz?|lf.*)|h(?:a(?:ckles|rk_girl)|e(?:ep_girl|male.+?))|'  # s
    r'i(?:lkymilk|ms(?:_\d)?|th_jedi)|k(?:arlet|unk_girl|yrim)|l(?:ave|eepy_b|yxxx24)|mell|nake_girl|'  # s
    r'o(?:ft_vore|lo(?:_.+?)?|phi[ae]|r(?:aka|idormi))|p(?:i(?:der|troast|zzy)|l(?:atoon|ucky.*?)|o(?:ks|nty))|'  # s
    r'q(?:ui(?:d_girl|rt))|t(?:a(?:lkek|r(?:_.+?|craft|fox))|ink|ra(?:ight|pon)|udio34)|u(?:ccubus)|y(?:lveon))|'  # s
    r't(?:a(?:ga|il_plug|ker_pov)|e(?:k(?:ken|tah.+?)|ntacles?|xelnaut)|he(?:_sims|count|hoaxxx)|ied(?:_up)?|'  # t
    r'o(?:gruta|rture|uhou)|r(?:a(?:ns|ps?)|inity)|soni|u(?:be|torial)|y(?:viania))|'  # t
    r'u(?:g(?:ly(?:_man)?|oira)|n(?:birth|de(?:ad|rtale))|pscaled|r(?:ethral?|iel))|'  # u
    r'v(?:a(?:lorant|mpire)|i(?:cer34|olence|rgin(?:ity)?)|o(?:caloid|mit|re))|'  # v
    r'w(?:ar(?:craft|frame|hammer)|e(?:ebu.*?|rewolf)|hip(?:_marks?|p(?:ed|ing))?|o(?:lf_girl|r(?:kout|ld_of_warcraft|ms?)))|'  # w
    r'x(?:_(?:com(?:_\d)?|ray)|enomorph)|'  # x
    r'z(?:o(?:mbies?|otopia))|'  # z
    r'\d{1,5}\+?_?(?:animal|(?:fem)?boy|futa|girl|monster)s?.*?'  # 0-9
    r')$'
)


# in-place
def prepare_regex_fullmatch(raw_string: str) -> Pattern[str]:
    return re_compile(rf'^{raw_string}$')

#
#
#########################################

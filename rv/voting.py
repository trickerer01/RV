# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import json
from collections.abc import MutableSequence
from contextlib import suppress
from typing import Literal, TypedDict

from rv.defs import SITE_AJAX_REQUEST_VIDEO_VOTING
from rv.fetch_html import fetch_html_raw
from rv.logger import Log
from rv.tagger import get_artist_num, get_category_num, get_tag_num


class ACTVoting(TypedDict):
    status: Literal['normal', 'hardened', 'unk_pending', 'unk_removed']
    up_score: int
    down_score: int
    up_users: int
    down_users: int
    user_vote: int  # bool?


class TagVoting(ACTVoting):
    tag_id: int


class ArtCatVoting(ACTVoting):
    item_type: Literal['category', 'model']
    item_id: int


class PostVotings(TypedDict):
    status: Literal['success', 'unk_failure']
    video_id: int
    logged_in: int  # bool
    can_vote: int  # bool
    tags: list[TagVoting]
    items: list[ArtCatVoting]
    pending_tags: list
    pending_items: list


async def filter_act_by_votes_count(vi, sname, ars: MutableSequence[str], cas: MutableSequence[str], tas: MutableSequence[str]) -> None:
    nameids_arts, nameids_cats, nameids_tags = {}, {}, {}
    for c, m, d in zip(
        (ars, cas, tas),
        (get_artist_num, get_category_num, get_tag_num),
        (nameids_arts, nameids_cats, nameids_tags),
        strict=False,
    ):
        for act in c:
            if act_id := m(act):
                d[act_id] = act
    tids, cids, aids = tuple(','.join(_.keys()) for _ in (nameids_tags, nameids_cats, nameids_arts))
    v_bytes = await fetch_html_raw(SITE_AJAX_REQUEST_VIDEO_VOTING % (vi.id, tids, cids, aids))
    if v_bytes is None:
        Log.error(f'Error: failed to fetch votings html for {sname}! Votings check skipped!')
        return
    votings_json: PostVotings = json.loads(v_bytes)
    voting_status = votings_json['status']
    if voting_status != 'success':
        Log.error(f'Error: votings status is \'{voting_status}\' for {sname}! Votings check skipped!')
        return
    for tv in votings_json['tags']:
        tid = str(tv['tag_id'])
        tstatus = tv['status']
        tscore = tv['up_score'] - tv['down_score']
        if tstatus not in ('normal', 'hardened') or tscore < 0:
            tname = nameids_tags.get(tid, 'Unknown')
            Log.warn(f'{sname}: tag \'{tname}\' ({tid}) vote score is \'{tscore}\' with status \'{tstatus}\'! Removing!')
            with suppress(KeyError):
                tas.remove(tname)
    for acv in votings_json['items']:
        acid = str(acv['item_id'])
        acstatus = acv['status']
        acscore = acv['up_score'] - acv['down_score']
        if acstatus not in ('normal', 'hardened') or acscore < 0:
            actype = acv['item_type']
            acname = {'category': nameids_cats, 'model': nameids_arts}.get(actype, {}).get(acid, 'Unknown')
            acs = {'category': cas, 'model': ars}.get(actype, [])
            Log.warn(f'{sname}: {actype} \'{acname}\' ({acid}) vote score is \'{acscore}\' with status \'{acstatus}\'! Removing!')
            with suppress(KeyError):
                acs.remove(acname)

#
#
#########################################

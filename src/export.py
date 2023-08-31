# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Dict, Optional, Callable

from defs import Config, normalize_path, prefixp, UTF8

__all__ = ('register_item_tags', 'register_item_description', 'register_item_comments', 'export_item_info')

saved_tags_dict = dict()  # type: Dict[str, Dict[int, str]]
saved_descs_dict = dict()  # type: Dict[str, Dict[int, str]]
saved_comms_dict = dict()  # type: Dict[str, Dict[int, str]]


def register_item_info(sdict: Dict[str, Dict[int, str]], item_id: int, info_str: str, subfolder: str) -> None:
    if subfolder not in sdict:
        sdict[subfolder] = dict()
    sdict[subfolder][item_id] = info_str


def register_item_tags(item_id: int, tags_str: str, subfolder: str) -> None:
    register_item_info(saved_tags_dict, item_id, tags_str, subfolder)


def register_item_description(item_id: int, desc_str: str, subfolder: str) -> None:
    register_item_info(saved_descs_dict, item_id, desc_str, subfolder)


def register_item_comments(item_id: int, coms_str: str, subfolder: str) -> None:
    register_item_info(saved_comms_dict, item_id, coms_str, subfolder)


def export_item_info() -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on registered item info"""
    for conf, sdict, name, proc_cb in (
        (Config.save_tags, saved_tags_dict, 'tags', lambda tags: f' {tags.strip()}\n'),
        (Config.save_descriptions, saved_descs_dict, 'descriptions', lambda description: f'{description}\n'),
        (Config.save_comments, saved_comms_dict, 'comments', lambda comment: f'{comment}\n')
    ):  # type: Optional[bool], Dict[str, Dict[int, str]], str, Callable[[str], str]
        if conf is True:
            for subfolder, subdict in sdict.items():
                if len(subdict) == 0:
                    continue
                min_id, max_id = min(subdict.keys()), max(subdict.keys())
                fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{prefixp()}!{name}_{min_id:d}-{max_id:d}.txt'
                with open(fullpath, 'wt', encoding=UTF8) as sfile:
                    sfile.writelines(f'{prefixp()}{idi:d}:{proc_cb(elem)}' for idi, elem in sorted(subdict.items(), key=lambda t: t[0]))

#
#
#########################################

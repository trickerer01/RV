# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Dict

from defs import Config, normalize_path, prefixp, UTF8

__all__ = ('register_item_tags', 'register_item_description', 'register_item_comments', 'export_item_info')

saved_tags_dict = dict()  # type: Dict[str, Dict[int, str]]
saved_descs_dict = dict()  # type: Dict[str, Dict[int, str]]
saved_comms_dict = dict()  # type: Dict[str, Dict[int, str]]


def register_item_tags(item_id: int, tags_str: str, subfolder: str) -> None:
    if subfolder not in saved_tags_dict:
        saved_tags_dict[subfolder] = dict()
    saved_tags_dict[subfolder][item_id] = tags_str


def register_item_description(item_id: int, desc_str: str, subfolder: str) -> None:
    if subfolder not in saved_descs_dict:
        saved_descs_dict[subfolder] = dict()
    saved_descs_dict[subfolder][item_id] = desc_str


def register_item_comments(item_id: int, coms_str: str, subfolder: str) -> None:
    if subfolder not in saved_comms_dict:
        saved_comms_dict[subfolder] = dict()
    saved_comms_dict[subfolder][item_id] = coms_str


def export_item_info() -> None:
    """Saves tags, descriptions and comments for each subfolder in scenario and base dest folder based on registered item info"""
    if Config.save_tags is True:
        for subfolder, tags_dict in saved_tags_dict.items():
            if len(tags_dict) == 0:
                continue
            min_id, max_id = min(tags_dict.keys()), max(tags_dict.keys())
            fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{prefixp()}!tags_{min_id:d}-{max_id:d}.txt'
            with open(fullpath, 'wt', encoding=UTF8) as sfile:
                sfile.writelines(f'{prefixp()}{idi:d}: {tags.strip()}\n' for idi, tags in sorted(tags_dict.items(), key=lambda t: t[0]))
    if Config.save_descriptions is True:
        for subfolder, descs_dict in saved_descs_dict.items():
            if len(descs_dict) == 0:
                continue
            min_id, max_id = min(descs_dict.keys()), max(descs_dict.keys())
            fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{prefixp()}!descriptions_{min_id:d}-{max_id:d}.txt'
            with open(fullpath, 'wt', encoding=UTF8) as sfile:
                sfile.writelines(f'{prefixp()}{idi:d}:{desc}\n' for idi, desc in sorted(descs_dict.items(), key=lambda t: t[0]))
    if Config.save_comments is True:
        for subfolder, comms_dict in saved_comms_dict.items():
            if len(comms_dict) == 0:
                continue
            min_id, max_id = min(comms_dict.keys()), max(comms_dict.keys())
            fullpath = f'{normalize_path(f"{Config.dest_base}{subfolder}")}{prefixp()}!comments_{min_id:d}-{max_id:d}.txt'
            with open(fullpath, 'wt', encoding=UTF8) as sfile:
                sfile.writelines(f'{prefixp()}{idi:d}:{coms}\n' for idi, coms in sorted(comms_dict.items(), key=lambda t: t[0]))

#
#
#########################################

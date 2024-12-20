# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import run as run_async
from io import StringIO
from os import path, stat
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from cmdargs import prepare_arglist
# noinspection PyProtectedMember
from config import BaseConfig
from defs import Duration, DOWNLOAD_MODE_TOUCH, SEARCH_RULE_DEFAULT, QUALITIES, QUALITY_480P
# noinspection PyProtectedMember
from ids import main as ids_main, main_sync as ids_main_sync
from logger import Log
# noinspection PyProtectedMember
from pages import main as pages_main, main_sync as pages_main_sync
# noinspection PyProtectedMember
from path_util import found_filenames_dict
from rex import prepare_regex_fullmatch
# noinspection PyProtectedMember
from tagger import (
    extract_id_or_group, normalize_wtag, match_text, load_tag_nums, load_artist_nums, load_category_nums, load_playlist_nums,
    load_tag_aliases, load_tag_conflicts, TAG_NUMS, ART_NUMS, CAT_NUMS, PLA_NUMS, TAG_ALIASES, TAG_CONFLICTS
)
from util import normalize_path
from version import APP_NAME, APP_VERSION

RUN_CONN_TESTS = 0


def set_up_test(log=False) -> None:
    found_filenames_dict.clear()
    Log._disabled = not log


class FileCheckTests(TestCase):
    def test_filecheck01_tags(self) -> None:
        set_up_test()
        load_tag_nums()
        self.assertIsNone(TAG_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    def test_filecheck02_arts(self) -> None:
        set_up_test()
        load_artist_nums()
        self.assertIsNone(ART_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    def test_filecheck03_cats(self) -> None:
        set_up_test()
        load_category_nums()
        self.assertIsNone(CAT_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    def test_filecheck04_plas(self) -> None:
        set_up_test()
        load_playlist_nums()
        self.assertIsNone(PLA_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    def test_filecheck05_tag_aliases(self) -> None:
        set_up_test()
        load_tag_aliases()
        self.assertIsNone(TAG_ALIASES.get(''))
        print(f'{self._testMethodName} passed')

    def test_filecheck06_tag_conflicts(self) -> None:
        set_up_test()
        load_tag_conflicts()
        self.assertIsNone(TAG_CONFLICTS.get(''))
        print(f'{self._testMethodName} passed')


class CmdTests(TestCase):
    def test_output_version_pages(self):
        set_up_test()
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(pages_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    def test_output_version_ids(self):
        set_up_test()
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(ids_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    # @mock_stderr
    # def test_cmd_base(self, stderr: StringIO):
    #     set_up_test()
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '--help'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1', '-pages'], True)
    #     self.assertNotEqual('', stderr.getvalue().strip('\n'))

    def test_cmd_pages(self):
        set_up_test()
        parsed1 = prepare_arglist(['cmd', '-get_maxid'], True)
        c1 = BaseConfig()
        c1.read(parsed1, True)
        self.assertTrue(c1.get_maxid)
        parsed2 = prepare_arglist(['-start', '2', '-pages', '1', '-uploader', '1234', '(2d~vr)', '--skip-empty-lists', '-script',
                                   'a: 2d; b: 3d; c: a2 -2d; d: * -utp always', '-naming', 'prefix|quality', '-log', 'warn'], True)
        c2 = BaseConfig()
        c2.read(parsed2, True)
        self.assertEqual(17, c2.naming_flags)
        self.assertEqual(8, c2.logging_flags)
        self.assertEqual(1, len(c2.extra_tags))
        self.assertEqual(4, len(c2.scenario))
        self.assertEqual(1234, c2.uploader)
        self.assertEqual('', c2.search)
        self.assertEqual(SEARCH_RULE_DEFAULT, c2.search_rule_art)
        self.assertIsNone(c2.use_id_sequence)
        self.assertTrue(c2.skip_empty_lists)
        parsed3 = prepare_arglist(['-playlist_name', 'commodified', '-start', '3', '-pages', '2', '-quality', '480p', '-dnoempty',
                                   '-minscore', '12', '-continue', '-unfinish', '-tdump', '-ddump', '-cdump', '-sdump'], True)
        c3 = BaseConfig()
        c3.read(parsed3, True)
        self.assertEqual('commodified', c3.playlist_name)
        self.assertEqual(3, c3.start)
        self.assertEqual(4, c3.end)
        self.assertEqual(QUALITIES[3], c3.quality)
        self.assertEqual(QUALITY_480P, c3.quality)
        self.assertEqual('480p', c3.quality)
        self.assertEqual(12, c3.min_score)
        self.assertTrue(c3.continue_mode)
        self.assertTrue(c3.keep_unfinished)
        self.assertTrue(c3.save_tags)
        self.assertTrue(c3.save_descriptions)
        self.assertTrue(c3.save_comments)
        self.assertTrue(c3.save_screenshots)
        self.assertTrue(c3.skip_empty_lists)
        parsed4 = prepare_arglist(['-model', 'gret', '-start', '3', '-pages', '2', '-quality', '480p', '-duration', '15-360',
                                   '-minscore', '12', '-continue', '-unfinish', '-tdump', '-ddump', '-cdump', '-sdump'], True)
        c4 = BaseConfig()
        c4.read(parsed4, True)
        self.assertEqual('gret', c4.model)
        self.assertEqual(3, c4.start)
        self.assertEqual(4, c4.end)
        self.assertEqual(QUALITIES[3], c4.quality)
        self.assertEqual('480p', c4.quality)
        self.assertEqual(Duration((15, 360)), c4.duration)
        self.assertEqual((15, 360), c4.duration)
        self.assertEqual(12, c4.min_score)
        self.assertTrue(c4.continue_mode)
        self.assertTrue(c4.keep_unfinished)
        self.assertTrue(c4.save_tags)
        self.assertTrue(c4.save_descriptions)
        self.assertTrue(c4.save_comments)
        self.assertTrue(c4.save_screenshots)
        parsed5 = prepare_arglist(['-search_tag', '6*,5????', '-search_rule_tag', 'any',
                                   '-search_art', '*nan', '-search_rule_art', 'any',
                                   '-search_cat', 'ali??_*', '-search_rule_cat', 'any',
                                   '-start', '3', '-pages', '2', '-quality', '720p'], True)
        c5 = BaseConfig()
        c5.read(parsed5, True)
        self.assertEqual('164,3966,5157,5261,5570,5934', c5.search_tags)
        self.assertEqual('22565,27156,8822', c5.search_arts)
        self.assertEqual('1433,1970,345,57,73', c5.search_cats)
        self.assertEqual('any', c5.search_rule_tag)
        self.assertEqual('any', c5.search_rule_art)
        self.assertEqual('any', c5.search_rule_cat)
        self.assertEqual(3, c5.start)
        self.assertEqual(4, c5.end)
        self.assertEqual(QUALITIES[2], c5.quality)
        self.assertEqual('720p', c5.quality)
        print(f'{self._testMethodName} passed')

    def test_cmd_ids(self):
        set_up_test()
        parsed1 = prepare_arglist(['cmd', '-seq', '(id=23~id=982)'], False)
        c1 = BaseConfig()
        c1.read(parsed1, False)
        self.assertEqual(1, len(c1.extra_tags))
        c1.id_sequence = extract_id_or_group(c1.extra_tags)
        self.assertTrue(c1.use_id_sequence)
        self.assertEqual(0, len(c1.extra_tags))
        self.assertEqual(2, len(c1.id_sequence))
        parsed2 = prepare_arglist(['-start', '1000', '-end', '999', '(a2~4k)', '(2d~vr)', '-dmode', 'touch', '--store-continue-cmdfile',
                                   '-lookahead', '100', '-proxynodown', '-proxy', 'socks4://u1:p2@9.123.15.67:3128',
                                   '-script', 'a: 2d; b: 3d -duration 10-200; c: a2 -2d -duration 0-9; d: * -utp always',
                                   '-naming', '0x8', '-log', 'trace'], False)
        c2 = BaseConfig()
        c2.read(parsed2, False)
        self.assertEqual(8, c2.naming_flags)
        self.assertEqual(1, c2.logging_flags)
        self.assertEqual(2, len(c2.extra_tags))
        self.assertEqual(4, len(c2.scenario))
        self.assertEqual(100, c2.lookahead)
        self.assertEqual(DOWNLOAD_MODE_TOUCH, c2.download_mode)
        self.assertTrue(c2.store_continue_cmdfile)
        self.assertTrue(c2.download_without_proxy)
        self.assertEqual(c2.proxy, 'socks4://u1:p2@9.123.15.67:3128')
        self.assertEqual(Duration((10, 200)), c2.scenario.queries[1].duration)
        self.assertEqual(Duration((0, 9)), c2.scenario.queries[2].duration)
        print(f'{self._testMethodName} passed')

    def test_cmd_wtags(self):
        set_up_test()
        parsed1 = prepare_arglist(['-start', '1', '-pages', '5',
                                   '-*[1`-5]`+`(finger{1`,3}|girl`)s`?`.`*',
                                   '-*`[1`-5`]`+`(finger`{1`,3`}`|`girl`)s`?`.`*``'], True)
        c1 = BaseConfig()
        c1.read(parsed1, True)
        self.assertEqual(r'^\-.*[1-5]+(?:finger{1,3}|girl)s?.*$', prepare_regex_fullmatch(normalize_wtag(c1.extra_tags[0])).pattern)
        self.assertEqual(r'^\-.*[1-5]+(?:finger{1,3}|girl)s?.*$', prepare_regex_fullmatch(normalize_wtag(c1.extra_tags[1])).pattern)
        parsed2 = prepare_arglist(['-start', '1', '-pages', '5', 'trigger`(s|ed|ing`)*'], True)
        c2 = BaseConfig()
        c2.read(parsed2, True)
        self.assertIsNotNone(match_text(c2.extra_tags[0], 'a triggered bluff'))
        print(f'{self._testMethodName} passed')


class DownloadTests(TestCase):
    def test_ids_touch(self):
        if not RUN_CONN_TESTS:
            return
        set_up_test()
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3146165'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-start', tempfile_id, '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace']
        ids_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    def test_pages_touch(self):
        if not RUN_CONN_TESTS:
            return
        set_up_test()
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3119234'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-pages', '999', '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace',
                    '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', 'fangs', '-search_art', 'ayasz']
        pages_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    def test_ids_full(self):
        if not RUN_CONN_TESTS:
            return
        set_up_test()
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3055235'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-start', tempfile_id, '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace']
        ids_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    def test_pages_full(self):
        if not RUN_CONN_TESTS:
            return
        set_up_test()
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3144801'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-pages', '999', '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace',
                    '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', '4k', '-search_art', 'mikeymack']
        pages_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

#
#
#########################################

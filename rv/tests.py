# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import functools
import os
from asyncio import run as run_async
from collections.abc import Callable
from io import StringIO
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rv.cmdargs import prepare_arglist
from rv.config import Config
from rv.defs import DOWNLOAD_MODE_TOUCH, QUALITIES, QUALITY_480P, SEARCH_RULE_DEFAULT, SITE, Duration
from rv.fetch_html import RequestQueue
from rv.logger import Log
from rv.main import main as ids_main
from rv.main import main as pages_main
from rv.main import main_sync as ids_main_sync
from rv.main import main_sync as pages_main_sync
from rv.path_util import found_filenames_dict
from rv.rex import prepare_regex_fullmatch
from rv.tagger import (
    ART_NUMS,
    CAT_NUMS,
    PLA_NUMS,
    TAG_ALIASES,
    TAG_CONFLICTS,
    TAG_NUMS,
    extract_id_or_group,
    extract_ids_from_links,
    load_artist_nums,
    load_category_nums,
    load_playlist_nums,
    load_tag_aliases,
    load_tag_conflicts,
    load_tag_nums,
    match_text,
    normalize_wtag,
)
from rv.util import normalize_path
from rv.version import APP_NAME, APP_VERSION

RUN_CONN_TESTS = 0


def test_prepare(log=False) -> Callable[[], Callable[[], None]]:
    def invoke1(test_func: Callable[[...], None]) -> Callable[[], None]:
        @functools.wraps(test_func)
        def invoke_test(*args, **kwargs) -> None:
            def set_up_test() -> None:
                found_filenames_dict.clear()
                Log._disabled = not log
                Config._reset()
                RequestQueue._reset()
            set_up_test()
            test_func(*args, **kwargs)
        return invoke_test
    return invoke1


class FileCheckTests(TestCase):
    @test_prepare(log=False)
    def test_filecheck01_tags(self) -> None:
        load_tag_nums()
        self.assertIsNone(TAG_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_filecheck02_arts(self) -> None:
        load_artist_nums()
        self.assertIsNone(ART_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_filecheck03_cats(self) -> None:
        load_category_nums()
        self.assertIsNone(CAT_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_filecheck04_plas(self) -> None:
        load_playlist_nums()
        self.assertIsNone(PLA_NUMS.get(''))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_filecheck05_tag_aliases(self) -> None:
        load_tag_aliases()
        self.assertIsNone(TAG_ALIASES.get(''))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_filecheck06_tag_conflicts(self) -> None:
        load_tag_conflicts()
        self.assertIsNone(TAG_CONFLICTS.get(''))
        print(f'{self._testMethodName} passed')


class CmdTests(TestCase):
    @test_prepare()
    def test_config_integrity(self):
        assert all(hasattr(Config, _) for _ in Config.NAMESPACE_VARS_REMAP.values())
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_output_version_pages(self):
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(pages_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_output_version_ids(self):
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(ids_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    # @test_prepare()
    # @mock_stderr
    # def test_cmd_base(self, stderr: StringIO):
    #     set_up_test()
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '--help'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1', '-pages'], True)
    #     self.assertNotEqual('', stderr.getvalue().strip('\n'))
    #     print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_pages01(self):
        prepare_arglist(['pages', '-get_maxid'])
        self.assertTrue(Config.get_maxid)
        self.assertEqual(0, Config.playlist_id)
        self.assertEqual('', Config.playlist_name)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_pages02(self):
        prepare_arglist(['pages', '-start', '2', '-pages', '1', '-uploader', '1234', '(2d~vr)', '--skip-empty-lists', '-script',
                         'a: 2d; b: 3d; c: a2 -2d; d: * -utp always', '-naming', 'prefix|quality', '-log', 'warn'])
        self.assertEqual(17, Config.naming_flags)
        self.assertEqual(8, Config.logging_flags)
        self.assertEqual(1, len(Config.extra_tags))
        self.assertEqual(4, len(Config.scenario))
        self.assertEqual(1234, Config.uploader)
        self.assertEqual('', Config.search)
        self.assertEqual(SEARCH_RULE_DEFAULT, Config.search_rule_art)
        self.assertIsNone(Config.use_id_sequence)
        self.assertTrue(Config.skip_empty_lists)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_pages03(self):
        prepare_arglist(['pages', '-playlist_name', 'commodified', '-start', '3', '-pages', '2', '-quality', '480p', '-dnoempty',
                         '-minscore', '12', '-continue', '-unfinish', '-tdump', '-ddump', '-cdump', '-sdump'])
        self.assertEqual('commodified', Config.playlist_name)
        self.assertEqual(3, Config.start)
        self.assertEqual(4, Config.end)
        self.assertEqual(QUALITIES[3], Config.quality)
        self.assertEqual(QUALITY_480P, Config.quality)
        self.assertEqual('480p', Config.quality)
        self.assertEqual(12, Config.min_score)
        self.assertTrue(Config.continue_mode)
        self.assertTrue(Config.keep_unfinished)
        self.assertTrue(Config.save_tags)
        self.assertTrue(Config.save_descriptions)
        self.assertTrue(Config.save_comments)
        self.assertTrue(Config.save_screenshots)
        self.assertTrue(Config.skip_empty_lists)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_pages04(self):
        prepare_arglist(['pages', '-model', 'gret', '-start', '3', '-pages', '2', '-quality', '480p', '-duration', '15-360',
                         '-minscore', '12', '-continue', '-unfinish', '-tdump', '-ddump', '-cdump', '-sdump'])
        self.assertEqual('gret', Config.model)
        self.assertEqual(3, Config.start)
        self.assertEqual(4, Config.end)
        self.assertEqual(QUALITIES[3], Config.quality)
        self.assertEqual('480p', Config.quality)
        self.assertEqual(Duration(15, 360), Config.duration)
        self.assertEqual((15, 360), Config.duration)
        self.assertEqual(12, Config.min_score)
        self.assertTrue(Config.continue_mode)
        self.assertTrue(Config.keep_unfinished)
        self.assertTrue(Config.save_tags)
        self.assertTrue(Config.save_descriptions)
        self.assertTrue(Config.save_comments)
        self.assertTrue(Config.save_screenshots)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_pages05(self):
        prepare_arglist(['pages',
                         '-search_tag', '6*,5????', '-search_rule_tag', 'any',
                         '-search_art', '*nan', '-search_rule_art', 'any',
                         '-search_cat', 'ali??_*', '-search_rule_cat', 'any',
                         '-blacklist', 'a:6*9,c:*z,t:6g*,t:8*',
                         '-start', '3', '-pages', '2', '-quality', '720p'])
        self.assertEqual('164,3966,5157,5261,5570,5934', Config.search_tags)
        self.assertEqual('22565,27156,34669,41543,8822', Config.search_arts)
        self.assertEqual('1433,1970,345,57,73', Config.search_cats)
        self.assertEqual('model:25905,model:34361,cat:1277,cat:315,cat:3315,cat:557,tag:38580,tag:3966', Config.blacklist)
        self.assertEqual('any', Config.search_rule_tag)
        self.assertEqual('any', Config.search_rule_art)
        self.assertEqual('any', Config.search_rule_cat)
        self.assertEqual(3, Config.start)
        self.assertEqual(4, Config.end)
        self.assertEqual(QUALITIES[2], Config.quality)
        self.assertEqual('720p', Config.quality)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_ids01(self):
        prepare_arglist(['ids', '-seq', '(id=23~id=982)'])
        self.assertEqual(1, len(Config.extra_tags))
        Config.id_sequence = extract_id_or_group(Config.extra_tags)
        self.assertTrue(Config.use_id_sequence)
        self.assertEqual(0, len(Config.extra_tags))
        self.assertEqual(2, len(Config.id_sequence))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_ids02(self):
        prepare_arglist(['ids', '-start', '1000', '-end', '999', '(a2~4k)', '(2d~vr)', '-dmode', 'touch', '--store-continue-cmdfile',
                         '-lookahead', '100', '-proxynodown', '-proxy', 'socks4://u1:p2@9.123.15.67:3128',
                         '-script', 'a: 2d; b: 3d -duration 10-200; c: a2 -2d -duration 0-9; d: * -utp always',
                         '-naming', '0x8', '-log', 'trace'])
        self.assertEqual(8, Config.naming_flags)
        self.assertEqual(1, Config.logging_flags)
        self.assertEqual(2, len(Config.extra_tags))
        self.assertEqual(4, len(Config.scenario))
        self.assertEqual(100, Config.lookahead)
        self.assertEqual(DOWNLOAD_MODE_TOUCH, Config.download_mode)
        self.assertTrue(Config.store_continue_cmdfile)
        self.assertTrue(Config.download_without_proxy)
        self.assertEqual(Config.proxy, 'socks4://u1:p2@9.123.15.67:3128')
        self.assertEqual(Duration(10, 200), Config.scenario.queries[1].duration)
        self.assertEqual(Duration(0, 9), Config.scenario.queries[2].duration)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_ids03(self):
        prepare_arglist(['ids', '-links', f'{SITE}video/1230567/wtf', '-u:araraw'])
        self.assertTrue(Config.use_link_sequence)
        self.assertEqual(2, len(Config.extra_tags))
        Config.id_sequence = extract_ids_from_links(Config.extra_tags)
        self.assertEqual(1, len(Config.extra_tags))
        self.assertListEqual(['-u:araraw'], Config.extra_tags)
        self.assertEqual(1, len(Config.id_sequence))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_wtags01(self):
        prepare_arglist(['pages', '-start', '1', '-pages', '5',
                         '-*[1`-5]`+`(finger{1`,3}|girl`)s`?`.`*',
                         '-*`[1`-5`]`+`(finger`{1`,3`}`|`girl`)s`?`.`*``'])
        self.assertEqual(r'^\-.*[1-5]+(?:finger{1,3}|girl)s?.*$', prepare_regex_fullmatch(normalize_wtag(Config.extra_tags[0])).pattern)
        self.assertEqual(r'^\-.*[1-5]+(?:finger{1,3}|girl)s?.*$', prepare_regex_fullmatch(normalize_wtag(Config.extra_tags[1])).pattern)
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_wtags02(self):
        prepare_arglist(['pages', '-start', '1', '-pages', '5', 'trigger`(s|ed|ing`)*'])
        self.assertIsNotNone(match_text(Config.extra_tags[0], 'a triggered bluff'))
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_cmd_extra_h_c01(self):
        prepare_arglist(['pages', '-start', '10', '-pages', '11',
                         '-header', 'shm_user=user812',
                         '-cookie', 'cf_clearance=clear120825'])
        self.assertListEqual([('shm_user', 'user812')], Config.extra_headers)
        self.assertListEqual([('cf_clearance', 'clear120825')], Config.extra_cookies)
        print(f'{self._testMethodName} passed')


class DownloadTests(TestCase):
    @test_prepare()
    def test_ids_touch(self):
        if not RUN_CONN_TESTS:
            return
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3146165'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = [
            'ids', '-path', tempdir, '-start', tempfile_id, '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace',
        ]
        ids_main_sync(arglist1)
        self.assertTrue(os.path.isfile(tempfile_fullpath))
        st = os.stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_pages_touch(self):
        if not RUN_CONN_TESTS:
            return
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3119234'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = [
            'pages', '-path', tempdir, '-pages', '999', '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace',
            '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', 'fangs', '-search_art', 'ayasz',
        ]
        pages_main_sync(arglist1)
        self.assertTrue(os.path.isfile(tempfile_fullpath))
        st = os.stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_ids_full(self):
        if not RUN_CONN_TESTS:
            return
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3055235'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = [
            'ids', '-path', tempdir, '-start', tempfile_id, '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace',
        ]
        ids_main_sync(arglist1)
        self.assertTrue(os.path.isfile(tempfile_fullpath))
        st = os.stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

    @test_prepare()
    def test_pages_full(self):
        if not RUN_CONN_TESTS:
            return
        tdir = TemporaryDirectory(prefix=f'{APP_NAME}_{self._testMethodName}_')
        tempdir = normalize_path(tdir.name)
        tempfile_id = '3144801'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = [
            'pages', '-path', tempdir, '-pages', '999', '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace',
            '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', '4k', '-search_art', 'mikeymack',
        ]
        pages_main_sync(arglist1)
        self.assertTrue(os.path.isfile(tempfile_fullpath))
        st = os.stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        tdir.cleanup()
        print(f'{self._testMethodName} passed')

#
#
#########################################

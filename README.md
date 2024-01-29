# RV

### Huh?
RV is a video downloader with a lot of features, most of which are filters for fine tuning your search

### How to use
##### Python 3.7 or greater required
- RV is a cmdline tool, no GUI
- It consists of 2 main download modules: `pages.py` for pages scanning, `ids.py` ‒ for video ids traversal
- See `requirements.txt` for additional dependencies. Install with:
  - `python -m pip install -r requirements.txt`
- Invoke `python pages.py --help` or `python ids.py --help` to list possible arguments for each module (the differences are minimal)
- For bug reports, questions and feature requests use our [issue tracker](https://github.com/trickerer01/RV/issues)

#### Search & filters
- RV provides advanced searching and filtering functionality
- Search (`pages.py` module only) is performed using extended website native API (see help for possible search args)
- Initial search results / ids list can be then filtered further using `extra tags` (see help for additional info)

#### Tags
- `rv_tags.list` file contains all existing tags for current version, same with `rv_cats.list` (categories) and `rv_arts.list` (artists) files. Any tag / category / artist you use is required to be valid and every `extra tag` needs to be a valid tag, category or artist. That is, unless you also utilize...
- Wildcards. In any `extra tag` you can use symbols `?` and `*` for `any symbol` and `any number of any symbols` repectively
- `extra tags` containing wildcards aren't validated, they can be anything
- What makes `extra tags` different from tags / categories / artists is `tags` or `-tags` are being used as filters instead of search params, normal tags / categories / artists are passed using their own search argument (see full help) and all unknown arguments are automatically considered `extra tags`
- All spaces **must_be_replaced_with_underscores** ‒ all tag / category / artist names are unified this way for convenience

#### Additional info
1. `OR` / `AND` groups:
  - `OR` group is a parenthesized tilda (**\~**) -separated group of tags
    - **(\<tag1>\~\<tag2>\~...\~\<tagN>)**
    - video matching **any** of the tags in `OR` group is considered matching that group
  - `AND` group is a parenthesized comma (**,**) -separated group of tags. Only negative `AND` group is possible ‒ to filter out videos having this unwanted **tags combination**
    - **-(\<tag1>,\<tag2>,...,\<tagN>)**
    - video matching **all** tags in `AND` group is considered matching that group

2. `--download-scenario` explained in detail:
  - Syntax: `--download-scenario SCRIPT` / `-script SCRIPT`
  - Scenario (script) is used to separate videos matching different sets of tags into different folders in a single pass
  - *SCRIPT* is a semicolon-separated sequence of '*\<subfolder>*<NOTHING>**:** *\<args...>*' groups (subqueries)
  - *SCRIPT* always contains spaces hence has to be escaped by quotes:
    - python ids.py \<args>... -script ***"***<NOTHING>sub1: tags1; sub2: tags2 ...***"***
  - Typically each next subquery is better exclude all required tags from previous one and retain excluded tags, so you know exactly what file goes where. But excluding previous required tags is optional ‒ first matching subquery is used and if some item didn't match previous sub there is no point checking those tags again. **Subquery order matters**. Also, `-tags` contained in every subquery can be safely moved outside of script
    - ... -script "s1: *a b (c\~d)* **-e**; s2: **-a -b -c -d -e** *f g (h\~i)*; s3: **-a -b -c -d -e -f -g -h -i** *k*" `<< full script`
    - ... -script "s1: *a b (c\~d)* **-e**; s2: *f g (h\~i)* **-e**; s3: *k* **-e**" `<< no redundant excludes`
    - ... -script "s1: *a b (c\~d)*; s2: *f g (h\~i)*; s3: *k*" **-e** `<< "-e" moved outside of script`
  - Besides tags each subquery can also have `-quality` set ‒ videos matching that subquery will be downloaded in this quality
  - Subquery can also have `--use-id-sequence` flag set (see below) and match video ids
  - You can also set `--untagged-policy always` for **one** subquery

3. Downloading a set of video ids
  - Syntax: `--use-id-sequence` / `-seq`, `ids.py` module only (or download scenario subquery)
  - Id sequence is used to download set of ids instead of id range
  - The sequence itself is an `extra tag` in a form of `OR` group of ids:
    - `(id=<id1>~id=<id2>~...~id=<idN>)`
  - Id sequence is used **instead** of id range, you can't use both
    - `python ids.py <args>... -seq (id=1337~id=9999~id=1001)`

4. File naming
  - File names are generated based on video *title* and *tags*:
  - Base template: ***\<prefix>\_\<id>\_(\<score>)_\<title>\_(\<tags>).\<ext>***. It can be adjusted via `-naming` argument
  - Non-descriptive or way-too-long tags will be dropped
  - If resulting file full path is too long to fit into 240 symbols, first the tags will be gradually dropped; if not enough title will be shrunk to fit; general advice is to not download to folders way too deep down the folder tree

5. Using 'file' mode
  - Although not required as cmdline argument, there is a default mode app runs in which is a `cmd` mode
  - `File` mode becomes useful when your cmdline string becomes **really long**. For example: Windows string buffer for console input is about 32767 characters long but standard `cmd.exe` buffer can only fit about 8192 characters, powershell ‒ about 16384. File mode is avalible for both `pages.py` and `ids.py` modules, of course, and can be used with shorter cmdline string as well
  - `File` mode is activated by providing 'file' as first argument and has a single option which is `-path` to a text file containing actual cmdline arguments for used module's `cmd` mode:
    - `python pages.py file -path <FILEPATH>`
  - Target file has to be structured as follows:
    - all arguments and values must be separated: one argument *or* value per line
    - quotes you would normally use in console window to escape argument value must be removed
    - only current module arguments needed, no python executable or module name needed, `cmd` mode can be omitted
      ```
      -start
      1
      -end
      20
      -path
      H:/long/folder name/with spaces (no quotes)/
      --log-level
      trace
      -script
      s1: (script~is~a~single~value); s2: -no_quotes_here_either
      ```

6. Unfinished files policy
  - Unexpected fatal errors, Ctrl-C and other mishaps will cause download(s) to end abruptly
  - By default when app manages to exit gracefully all unfinished files get deleted, at the same time all existing files are automatically considered completed
  - To check and resume existing unfinished files use `--continue-mode` (or `-continue`) option. This may be slower for non-empty folders due to additional network requests but safer in case of complex queries
  - To keep unfinished files use `--keep-unfinished` (or `-unfinish`) option. It acts as `--continue-mode` helper so it's recommended to use either both or none at all

7. Interrupt & resume
  - When downloading at large sometimes resulting download queue is so big it's impossible to process within reasonable time period and the process will be inevitably interrupted
  - To be able to resume without running the whole search process again use `--store-continue-cmdfile` option. Once initial video queue is formed a special 'continue' file will be stored and periodically updated in base download destination folder
  - Continue file contains cmdline arguments required to resume download, all provided parameters / options / download scenario / extra tags are preserved
  - It is strongly recommended to also include `--continue-mode` and `--keep-unfinished` options when using continue file
  - If download actually finishes without interruption stored continue file is automatically deleted
  - Continue file has to be used with `ids.py` module, `file` mode (see `using 'file' mode` above)

#### Examples
1. Pages
  - All videos by a single tag:
    - `python pages.py -pages 9999 -search_tag TAG1`
  - Up to 48 videos with both tags present from a single author in 1080p, save to a custom location:
    - `python pages.py -pages 2 -path PATH -quality 1080p -search_art ARTIST -search_tag TAG1,TAG2`
  - Up to 24 videos on page 3 with any of 3 tags from any of 2 authors under any of 2 categories, exclude any kind of `vore` or `fart`, in best quality, with minimum score of 100 and minimum rating of 90%, use proxy, save to a custom location, save tags, log everything, use shortest names for files:
    - `python pages.py -log trace -start 3 -pages 1 -path PATH -proxy https://127.0.0.1:222 -tdump -quality 2160p -minscore 100 -minrating 90 -search_cat CATEGORY1,CAT_EGORY2 -search_art ART_IST1,ARTIST2 -search_tag TAG1,TAG2,TAG3 -search_rule_cat any -search_rule_art any -search_rule_tag any -naming 0 -*vore -fart*`
  - All videos uploaded by a user, if tagged with either of 2 desired tags, in best quality, sorted into subfolders by several desired (known) authors, putting remaining videos into a separate folder, setup for interrupt & continue:
    - `python pages.py -pages 9999 -path PATH --store-continue-cmdfile -quality 2160p -uploader USER_ID (TAG1~TAG2) -script "name1: AUTHOR1; name2: AUTHOR2; name3: AUTHOR3; rest: * -utp always"`

2. Ids
  - All existing videos in range:
    - `python ids.py -start 3200000 -count 100`
    - `python ids.py -start 3200000 -end 3200099`
  - You can use the majority of arguments from `pages` examples. The only argument that is unique to `ids.py` module is `--use-id-sequence` (`-seq`), see above where it's explained in detail

#### Common mistakes
There are several ways you can select videos to download and some of them, despite being seemingly logical, are terribly ineffective:

1. Using `ids.py` module to process greater id range
- `python ids.py <args...> -start 1 -end 3500000`
  - approximate time such query takes is 40+ days
  - videos `236` - `3,045,049` don't exist

**Solution 1**: split your query into smaller ones:
- `python ids.py <args...> -start 1 -end 235`
- `python ids.py <args...> -start 3045050 -end 3100000`
- `etc.`

**Solution 2**: use `pages.py` module (listed videos):
- `python pages.py <args...> -start 1 -pages 9999`

2. Using `extra tags` to download only certain tag / category / artist / uploader
- `python pages.py <args...> -start 1 -pages 9999 ARTIST`
- `python ids.py <args...> -start ... -end ... (TAG1~TAG2)`
- `etc.`
  - you may end up having to check every video
  - there is no way to filter by uploader's username using `extra tags` (see below)

**Solution 1**: use native search functionality instead (search result pages):
- `python pages.py <args...> -start 1 -pages 99 -search_art ARTIST`
- `python pages.py <args...> -start 1 -pages 99 -search_tag TAG1,TAG2 -search_rule_tag any`

**Solution 2**: to search by uploader use `-uploader` argument (user video pages):
- `python pages.py <args...> -start 1 -pages 99 -uploader USER_ID`
  - `USER_ID` ‒ integer, can be found in member's profile page address

# RV

### Huh?
RV is a video downloader with a lot of features, most of which are filters for fine tuning your search

### How to use
##### Python 3.7 or later required
- RV is a cmdline tool, no GUI
- It consists of 2 main download modules: `pages.py` for pages scanning, `ids.py` - for video ids traversal
- Invoke `python pages.py --help` or `python ids.py --help` for possible arguments for each module (the differences are minimal)
- See `requirements.txt` for additional module dependencies

#### Search & filters
- RV provides advanced searching and filtering functionality
- Search (pages only) is performed using extended website native API (see help for possible search args)
- Initial search results / ids list can be then filtered further by using *extra tags* (see help for additional info)

#### Tags
- Refer to `rv_tags.list` file for list of existing tags. Any tag you use must be a valid tag. That is, unless you also utilize...
- Wildcards. In any kind of tag you can use symbols `?` and `*` for 'any symbol' and 'any number of any symbols' repectively. Tags containing wildcards are not being validated, they can be anything
- Keep in mind that in tags all spaces must be **replaced_with_underscores** - tag names are all unified this way for convenience

#### Additional info
1. `OR` / `AND` groups:
  - `OR` group is a parenthesized tilda (**\~**) -separated group of tags:
    - **(\<tag1>\~\<tag2>\~...\~\<tagN>)**
    - video containing **any** of the tags in `OR` group is considered matching said group
  - `AND` group is a parenthesized comma (**,**) -separated group of tags. It is only used for exclusion:
    - **-(\<tag1>,\<tag2>,...,\<tagN>)**
    - video containing **all** of the tags in `AND` group is considered matching said group
    - negative `AND` group are for filtering out videos having this undesired **tags combination**

2. `--download-scenario` explained in detail:
   - Syntax: `--download-scenario SCRIPT` / `-script SCRIPT`
   - Scenario (script) is used to separate videos matching different sets of tags into different folders in a single pass
   - *SCRIPT* is a semicolon-separated sequence of '*\<subfolder>*<NOTHING>**:** *\<args...>*' groups (subqueries)
   - *SCRIPT* always contains spaces hence has to be escaped by quotes:
     - python ids.py \<args>... -script ***"***<NOTHING>sub1: tags1; sub2: tags2 ...***"***
   - Typically each next subquery is better exclude all required tags from previous one and retain excluded tags, so you know exactly what file goes where. But excluding previous required tags is optional - first matching subquery is used and if some item didn't match previous sub there is no point checking those tags again. **Subquery order matters**. Also, `-tags` contained in each subquery can be safely moved outside of script. Example:
     - ... -script "s1: a b (c\~d) **-e**; s2: **-a -b -c -d -e** f g (h\~i); s3: **-a -b -c -d -e -f -g -h -i** k" `<< full script`
     - ... -script "s1: a b (c\~d) **-e**; s2: **f g (h\~i) -e**; s3: **k -e**" `<< no redundant excludes`
     - ... **-e** -script "s1: **a b (c\~d)**; s2: **f g (h\~i)**; s3: **k**" `<< "-e" moved outside of script`
   - Besides tags, each subquery can also have `-quality` set, which will be used to download files matching that subquery. You can also set `-uvp` for **one** subquery
   - Instead of pure tags subquery can also use `--use-id-sequence:` / `-seq` (see below) so instead of checking tags subquery will match ids. Such a subquery is better be first in script

3. `--use-id-sequence`:
  - Syntax: `--use-id-sequence SEQUENCE` / `-seq SEQUENCE`, ***ids.py*** only
  - Id sequence is used to download set of ids instead of id range
  - *SEQUENCE* is an `OR` group of ids:
    - **(id=\<id1>\~id=\<id2>\~...\~id=\<idN>)**
  - Id sequence is used **INSTEAD** of id range, you can't use both
    - python ids.py \<args>... -seq (id=1337\~id=9999\~id=1001)

4. File naming
  - File names are generated based on video *title* and *tags*:
  - Base template: ***rv\_\<video_id>\_\<title>\_(\<tag1,tag2,...,tagN>).\<ext>***
  - Non-descriptive or way-too-long tags will be dropped
  - If resulting file total path is too long to fit into 240 symbols, first the tags will be gradually dropped; if not enough, title will be shrunk to fit; general advice: do not download to folders way too deep down the folder tree

  5. Using 'file' mode
  - Although not required as cmdline argument, there is a default mode app runs in which is a `cmd` mode
  - `File` mode becomes useful when your cmdline string becomes **really long**. For example: Windows string buffer for console input is about 32767 characters long but standard `cmd.exe` buffer can only fit about 8192 characters, powershell - about 16384. File mode is avalible for both `pages` and `ids` modules, of course, and can be used with shorter cmdline string as well
  - `File` mode is activated by providing 'file' as first argument and has a single option which is `-path` to a text file containing actual cmdline arguments for used module's cmd mode:
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

#### Examples
1. Pages
  - Minimal example - all videos by a single tag:
    - `python pages.py -pages 9999 -search_tag TAG1`
  - Up to 48 videos with both tags present from a single author in 1080p, save to a custom location:
    - `python pages.py -pages 2 -path PATH -quality 1080p -search_art ARTIST -search_tag TAG1,TAG2`
  - Up to 24 videos on page 3 with any of 3 tags from any of 2 authors under any of 2 categories, no `gore` or `guro`, in best quality, with minimum score of 100 and minimum rating of 90%, use proxy, save to a custom location, save tags, log everything, use shortest names for files:
    - `python pages.py -log trace -start 3 -pages 1 -path PATH -proxy https://127.0.0.1:222 -tdump -quality 2160p -minscore 100 -minrating 90 -search_cat CATEGORY1,CAT_EGORY2 -search_art ART_IST1,ARTIST2 -search_tag TAG1,TAG2,TAG3 -search_rule_cat any -search_rule_art any -search_rule_tag any -naming 0 -gore -guro`

2. Ids
  - Minimal example - all existing videos in range:
    - `python ids.py -start 300000 -count 100`
    - `python ids.py -start 300000 -end 300099`
  - You can use the majority of arguments from `pages` examples. The only argument that is unique to `ids` is `--use-id-sequence` (`-seq`), see above where it's explained in detail

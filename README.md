# RV

### Huh?
RV is a video downloader with a lot of features, most of which are filters for fine tuning your search

### How to use
##### Python 3.7 or later required
- RV is a cmdline tool, no GUI
- It consists of 2 main download modules: `pages.py` for pages scanning, `ids.py` - for video ids traverse
- Invoke `python pages.py --help` or `python ids.py --help` for possible arguments for each module (the differences are minimal)
- See `requirements.txt` for additional module dependencies

#### Tags
- Refer to `rv_tags.list` file for list of existing tags. Any tag you use must be a valid tag. That is, unless you also utilize...
- Wildcards. In any kind of tag you can use symbols `?` and `*` for 'any symbol' and 'any number of any symbols' repectively. Tags containing wildcards are not being validated, they can be anything
- Keep in mind that in tags all spaces must be replaced with underscores - tag names are all unified this way for convenience

#### Additional info
1. `OR` / `AND` groups:
  - `OR` group is a parenthesized tilda (**~**) -separated group of tags:
    - **(\<tag1>~\<tag2>~...~\<tagN>)**
    - video containing **any** of the tags in `OR` group is considered matching said group
  - `AND` group is a parenthesized comma (**,**) -separated group of tags. It is only used for exclusion:
    - **-(\<tag1>,\<tag2>,...,\<tagN>)**
    - video containing **all** of the tags in `AND` group is considered matching said group
    - negative `AND` group are for filtering out videos having this undesired **tags combination**

2. `--download-scenario` explained in detail:
   - Syntax: `--download-scenario SCRIPT` / `-script SCRIPT`
   - Scenario (script) is used to separate videos matching different sets of tags into different folders in a single pass
   - *SCRIPT* is a semicolon-separated sequence of '*\<subfolder>*<NOTHING>**:** *\<args...>*' groups
   - *SCRIPT* always contains spaces hence has to be escaped by quotes:
     - python ids.py \<args>... -script ***"***<NOTHING>sub1: tags1; sub2: tags2 ...***"***
   - Typically each next group is better exclude all required tags in a previous group and retain excluded tags, so you know exactly what file goes where:
     - ... -script "s1: a b (c~d) **-e**; s2: **-a -b -c -d -e** f g (h~i); s3:..."
   - Besides just tags, each group can also have `-quality` set, which will be used to download files matching tags in that group. You can also set `-uvp` for **one** group

3. `--use-id-sequence`:
  - Syntax: `--use-id-sequence SEQUENCE` / `-seq SEQUENCE`, ***ids.py*** only
  - Id sequence is used to download set of ids instead of id range
  - *SEQUENCE* is an `OR` group of ids:
    - **(id=\<id1>~id=\<id2>~...~id=\<idN>)**
  - Id sequence is used **INSTEAD** of id range, you can't use both
    - python ids.py \<args>... -seq (id=1337~id=9999~id=1001)

4. File Naming
  - File names are generated based on video *title* and *tags*:
  - Base template: ***rv\_\<video_id>\_\<title>\_(\<tag1,tag2,...,tagN>).\<ext>***
  - Non-descriptive or way-too-long tags will be dropped
  - If resulting file total path is too long to fit into 240 symbols, first the tags will be gradually dropped; if not enough, title will be shrunk to fit; general advice: do not download to folders way too deep down the folder tree

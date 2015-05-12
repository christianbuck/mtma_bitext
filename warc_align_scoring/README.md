## Preparing data

```console
$ wget http://statmt.org/~buck/mtma/sites-en-fr/ted.com_ENGLISH.xz
$ wget http://statmt.org/~buck/mtma/sites-en-fr/ted.com_FRENCH.xz
$ unxz ted.com_ENGLISH.xz
$ unxz ted.com_FRENCH.xz
```

## Install dependencies

```console
$ pip3 install -r requirements
```

## Build shelve database from WARC file

- extract data from WARC file
- clean HTML and translate

```console
$ python3 warc_to_shelve.py -h
usage: warc_to_shelve.py [-h] [-t LANG] [-v] SHELVE [FILE [FILE ...]]

positional arguments:
  SHELVE                Output shelve database file
  FILE                  Input WARC file. (default: stdin)

optional arguments:
  -h, --help            show this help message and exit
  -t LANG, --translate-from LANG
  -v, --verbose         Produce verbose message

$ python3 warc_to_shelve.py ted_en.shelve ../../ted.com_ENGLISH.six
$ python3 warc_to_shelve.py -t fr ted_fr.shelve ../../ted.com_FRENCH.six
```

## Do line alignment and scoring


```console
$ python3 align_and_score.py -h
usage: align_similarity.py [-h] [-p] [-v] SRC_SHELVE TGT_SHELVE

positional arguments:
  SRC_SHELVE            Source shelve database file
  TGT_SHELVE            Target shelve database file

optional arguments:
  -h, --help            show this help message and exit
  -p, --print-sentences
                        Print aliged sentences
  -v, --verbose         Produce verbose message
  
$ python3 align_similarity.py ted_en.shelve ted_fr.shelve
 * http://www.ted.com/talks/lang/en/robin_chase_on_zipcar_and_her_next_big_idea.html
   --> http://www.ted.com/talks/lang/fr/robin_chase_on_zipcar_and_her_next_big_idea.html
   line equality ratio: 0.26681614349775784	 jaccard sim: 0.41129831516352827
 * http://www.ted.com/talks/lang/en/amory_lovins_a_50_year_plan_for_energy.html
   --> http://www.ted.com/talks/lang/fr/amory_lovins_a_50_year_plan_for_energy.html
   line equality ratio: 0.21196358907672302	 jaccard sim: 0.5028224055579679
 * http://www.ted.com/talks/lang/en/howard_rheingold_on_collaboration.html
   --> http://www.ted.com/talks/lang/fr/howard_rheingold_on_collaboration.html
   line equality ratio: 0.2939914163090129	 jaccard sim: 0.5625231910946197
```





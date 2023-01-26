# Bibtex_to_ORKG.py

This pipeline is used to sort entries in a BibTeX file according to their relevancy for a given set of keywords.

## Requirements

- Python 3.x
- bibtexparser library

## Usage

1. Install the required libraries by running `pip install bibtexparser`
2. Export your Zotero libraries (including files). It should look like this:
`path/to/sample_library/`
We recommend to place your export inside an Obsidian vault:
`path/to/vault_name/Zotero/sample_library/`
Inside it should look like this:
```
sample_library.bib
files/
    2/
        something.pdf
    5/
        else.pdf
```
3. Open the `tools/` directory in your favourite IDE (e.g. [VSC](https://code.visualstudio.com/))
4. Setup the a `config.yml` in `tools/pipelines/k_score_Zotero/runs/` like this:

```
# keywords
#   groups
#     keywords: weight (0 to 10)
keywords:
  fruits:
    ananás: 6
    ananas: 1
    pineapple: 2

  holding:
    basket: 1
    bowl: 1

  taste:
    funny: 5
    very tasty: 10

# Punish if only "very" and "tasty" are matched, not "very tasty"
PUNISH_SEMIMATCH: 0.2

# Punish if a group isn't matched at all
PUNISH_NOMATCH: 0.1

# Expected frequency of keywords per word
# 1 = every word should be a keyword
# 0.01 = one in every 100 words should be a keyword
WEAKEN_WORDCOUNT: 0.01

# Bump up the score after calculation
FLAT_SCORE_BOOST: 10

# What to run. Just comment out what you don't need
DO_SCORE: TRUE
DO_OBSIDIAN: TRUE
DO_SCORE: TRUE
```
5. run `Bibtex_to_ORKG.py`
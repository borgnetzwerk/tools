"""
Goal:
Calculate the "k_score" for a given set of keywords

Setup:
1: Run and document your search query.
2: Store your results in Zotero (or similar)
3: Export your results (incl. files) to Obsidian (or anywhere, really)
4: Setup the config
"""
import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())
from publish.Obsidian import bibtex_to_notes

mypath = os.getcwd()
runpath = os.path.join(os.path.dirname(__file__), "runs")
runs = [f for f in os.listdir(
    runpath) if f.endswith(".yml")]
for run in runs:
    with open(os.path.join(runpath, run), "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    bibtex_to_notes.main(cfg)

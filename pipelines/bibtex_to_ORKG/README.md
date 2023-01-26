# Bibtex_to_ORKG.py

This pipeline is used to convert BibTeX files to a csv readable by the [ORKG](https://orkg.org/csv-import).

## Requirements

- Python 3.x
- bibtexparser library

## Usage

1. Install the required libraries by running `pip install bibtexparser`
2. Open the `tools/` directory in your favourite IDE (e.g. [VSC](https://code.visualstudio.com/))
3. Setup the a `config.yml` in `tools/pipelines/bibtex_to_ORKG/runs/` like this:

```
# Path to where your input.bib is
path: path/to/my/sample_input.bib
```
4. run `Bibtex_to_ORKG.py`

### with k_score:
If you have used the k_score before, you can use the results here:

3. Setup the a `config.yml` in `tools/pipelines/bibtex_to_ORKG/runs/` like this:
```
# Path to where your input.bib is
path: path/to/my/sample_input.bib

# OPTIONAL:
# cutoff threshold for k_score, if you have that calculated already 
threshold: 5
```
4. run `Bibtex_to_ORKG.py`

See also "Call directly" (WIP)
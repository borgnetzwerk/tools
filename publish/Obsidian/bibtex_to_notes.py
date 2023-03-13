import core.helper as helper
import config.personal as personal
import ORKG.bibtex_to_csv as ORKG_csv
import review.k_score as k_score
import extract.util_bibtex as util_bibtex

import re
import os
from typing import List
from typing import Dict
from os import listdir
from os.path import isfile, join
import markdown

LITERATURE = "Reading notes"


def extract_field_values(input_string: str) -> dict:
    """Extract values of fields from input string using regular expressions."""
    date = re.search(r'(?<=year: ).*?(?=\n)', input_string).group()
    title = re.search(r'(?<=title: ).*?(?=\n)', input_string).group()
    authors = re.search(r'(?<=authors: ).*?(?=\n)', input_string).group()
    in_ = re.search(r'(?<=in: ).*?(?=\n)', input_string).group()
    page = re.search(r'(?<=page: ).*?(?=\n)', input_string).group()
    cite_title = re.search(
        r'(?<=citeTitle:[\n ]).*?(?=\n)', input_string).group()
    cite_id = re.search(r'(?<=citeID:[\n ]).*?(?=\n)', input_string).group()
    url = re.search(r'(?<=url: ).*?(?=\n)', input_string).group()
    zotero = re.search(r'(?<=zotero: ).*?(?=\n)', input_string).group()
    tags = re.search(r'(?<=tags:: ).*?(?=\n)', input_string).group()
    read = re.search(r'(?<=read\?:: ).*?(?=\n)', input_string).group()
    comment = re.search(r'(?<=comment:: ).*?(?=\n)', input_string).group()
    return {
        "date": date,
        "title": title,
        "authors": authors,
        "in_": in_,
        "page": page,
        "cite_title": cite_title,
        "cite_id": cite_id,
        "url": url,
        "zotero": zotero,
        "tags": tags,
        "read": read,
        "comment": comment
    }


def extract_pdfs(outer_path, files):
    pdfs = []
    if files:
        for file_i in files.values():
            if file_i.endswith(".pdf"):
                # to remove \ in filenames
                file_i = file_i.replace("\\", "")
                pdfs.append(os.path.join(
                    outer_path, file_i).replace("/", "\\"))
    return pdfs


def build_literature_note(field_values: dict, rest: str, lib_path: str, cfg) -> str:
    """Build output string using string formatting method and join()."""
    # YAML
    date = field_values.get('date', '')
    title = field_values.get('title', '')
    author = field_values.get('author', '')
    in_ = field_values.get('in_', '')
    in_abrev = field_values.get('in_', '')
    pages = field_values.get('pages', '')
    cite_title = field_values.get('cite_title', '')
    cite_id = field_values.get('cite_id', '')
    url = field_values.get('url', '')
    zotero = field_values.get('zotero', '')
    tags = field_values.get('tags', '')
    read = field_values.get('read', '')
    comment = field_values.get('comment', '')

    learning = field_values.get('learning', '')
    keyword_links = field_values.get('keyword_links', '')
    key_notes = field_values.get('key_notes', '')
    quotes = field_values.get('quotes', '')

    editorbtype = field_values.get('editorbtype', '')
    editorb = field_values.get('editorb', '')
    eventtitle = field_values.get('eventtitle', '')
    pagetotal = field_values.get('pagetotal', '')
    pmcid = field_values.get('pmcid', '')

    langid = field_values.get('langid', '')
    editor = field_values.get('editor', '')
    publisher = field_values.get('publisher', '')
    booktitle = field_values.get('booktitle', '')
    journaltitle = field_values.get('journaltitle', '')
    shortjournal = field_values.get('shortjournal', '')
    url = field_values.get('url', '')
    urldate = field_values.get('urldate', '')
    abstract = field_values.get('abstract', '')
    series = field_values.get('series', '')
    volume = field_values.get('volume', '')
    doi = field_values.get('doi', '')
    isbn = field_values.get('isbn', '')
    issn = field_values.get('issn', '')
    number = field_values.get('number', '')
    rights = field_values.get('rights', '')
    keywords = field_values.get('keywords', '')
    location = field_values.get('location', '')
    ENTRYTYPE = field_values.get('ENTRYTYPE', '')
    ID = field_values.get('ID', '')
    file = field_values.get('file', '')
    shorttitle = field_values.get('shorttitle', '')
    pmid = field_values.get('pmid', '')
    note = field_values.get('note', '')
    eprint = field_values.get('eprint', '')
    eprinttype = field_values.get('eprinttype', '')
    issue = field_values.get('issue', '')

    if not in_:
        if booktitle:
            in_ = booktitle
        elif journaltitle:
            in_ = journaltitle
    if not in_abrev:
        if shortjournal:
            in_abrev: shortjournal

    if not cite_title:
        cite_title = f"[[note_path/@{ID}|{title}]]"
    if not cite_id:
        cite_id = f"\[[[note_path/@{ID}|00]]\]"
    if not zotero:
        temp_zot = "zotero://select/items/@" + ID
        zotero = f"[{temp_zot}]({temp_zot})"
    temp_tags = ["#science ", "#literature "]
    if tags:
        if not tags.endswith(" "):
            tags += " "
    for temp_tag in temp_tags:
        if temp_tag not in tags:
            tags += temp_tag
    bib_path = os.path.join(cfg['vault_path'], lib_path).replace("\\", "/")
    pdf = ""
    pdfs = extract_pdfs(bib_path, file)
    for pdf_ in pdfs:
        pdf += f'[Acrobat]({pdf_.replace(" ", "%20")})\n'
    lib_path = lib_path.replace("\\", "/")
    if not pdf:
        temp_tags = ["#missingPDF "]
        for temp_tag in temp_tags:
            if temp_tag not in tags:
                tags += temp_tag
    if not read:
        read = "#read/false "

    # todo: make all lower case
    if keywords:
        temp = re.split(", *", keywords)
        if keyword_links:
            keyword_links += " "
        missing = []
        for key in temp:
            search = "[[" + key + "]]"
            if search not in temp:
                missing.append(search)
        keyword_links = " ".join(missing)

    yaml = f"""---
date: {date}
title: \"{title}\"
author: \"{author}\"
editor: \"{editor}\"
publisher: \"{publisher}\"
pages: \"{pages}\"
language: \"{langid}\"
location: \"{location}\"
ENTRYTYPE: \"{ENTRYTYPE}\"
in: \"{in_}\"
short: \"{in_abrev}\"
series: \"{series}\"
volume: {volume}
doi: {doi}
isbn: {isbn}
url: \"{url}\"
ID: \"{ID}\"
issn: {issn}
number: {number}
rights: \"{rights}\"
keywords: \"{keywords}\"
urldate: {urldate}
shorttitle: \"{shorttitle}\"
pmid: {pmid}
note: \"{note}\"
eprint: \"{eprint}\"
eprinttype: \"{eprinttype}\"
issue: \"{issue}\"
editorbtype: \"{editorbtype}\"
editorb: \"{editorb}\"
eventtitle: \"{eventtitle}\"
pagetotal: {pagetotal}
pmcid: {pmcid}
---
""".replace(': ""', ": ")

    infos = f"""```citeTitle:
{cite_title}
```
```citeID:
{cite_id}
```
---
url: {url}
zotero: {zotero}
{pdf}
---
tags:: {tags}
read:: {read}
comment:: {comment}

---
"""
    text = f"""# Learning
{learning}

## Keywords
{keyword_links}

## Key notes
{key_notes}

## Quotes
{quotes}

# Abstract
{abstract}
"""
    for name, path in dict(file).items():
        path = path.replace("\\", "")
        # if include files to yaml
        # if name.startswith("path_"):
        #     name = name.replace("path_", "", 1)
        #     name = name.replace("_", " ")
        text += f"""
# {name}
[Acrobat]({os.path.join(bib_path, path).replace(" ", "%20")})
[[{lib_path}/{path}|{path.split("/", 2)[2]}]]
![[{lib_path}/{path}]]
"""

    # todo: make sure rest is never needed anymore
    return yaml + infos + text + rest


def reformat(input_string: str, splitter: str = "\n# Learning\n") -> tuple:
    pieces = input_string.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]

    field_values = extract_field_values(work)
    output_string = build_literature_note(field_values, splitter + rest)
    return output_string, field_values


def categorize_files(data_files: List[str], cfg: Dict) -> Dict[str, List[str]]:
    """Sorts files into notes, zotero, literature_notes and others"""
    files = {
        "notes": [],
        "zotero": [],
        "literature_notes": [],
        "others": [],
    }
    for file in data_files:
        if file.endswith('.md'):
            if file.startswith(cfg["literature_notes_folder_name"] + '\\'):
                files["literature_notes"].append(file)
            else:
                files["notes"].append(file)
        elif file.startswith(cfg["zotero_folder_name"] + '\\'):
            files["zotero"].append(file)
        else:
            files["others"].append(file)
    return files


def reformat_literature_files(cfg, files: Dict) -> Dict[str, str]:
    bib = {}
    for lit in files["literature_notes"]:
        filepath = os.path.join(cfg['vault_path'], lit)
        with open(filepath, 'r', encoding='UTF8') as f:
            text = f.read()
        text, var_dict = reformat(text)
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(text)
        pieces = var_dict["cite_title"].split('|', 1)
        uid = pieces[0]
        title = pieces[1]
        bib.update({uid: title})
    return bib


def format_title(title: str) -> List[str]:
    """Format title for matching by replacing '?', ':', and '–' with alternate characters."""
    check = [title]
    if "?" in title:
        temp = [token.replace("?", "❓") for token in check]
        check += temp
    if ":" in title:
        temp = [token.replace(":", ";") for token in check]
        check += temp
    if "–" in title:
        temp = [token.replace("–", "-") for token in check]
        check += temp
    return check


def reformat_note_files(cfg, notes: List[str], bib: Dict[str, str]) -> None:
    for note in notes:
        filepath = cfg['vault_path'] + '\\' + note
        with open(filepath, 'r', encoding='UTF8') as f:
            text = f.read()
        text_in = text
        for uid, title in bib.items():
            check = format_title(title)
            for token in check:
                text = re.sub(re.escape("[[{}]]".format(token)),
                              "[[{}|{}]]".format(uid, title), text, flags=re.I)
                text = re.sub(re.escape("[[{}".format(token)),
                              "[[{}".format(uid), text, flags=re.I)
        if text != text_in:
            with open(filepath, 'w', encoding='UTF8') as f:
                f.write(text)


def read_from_note(var_dict, note):
    patterns = [
        (r'(?<=\ntags:: ).*(?=\nread:: )', 'tags'),
        (r'(?<=\nread:: ).*(?=\ncomment:: )', 'read'),
        (r'(?<=\ncomment:: ).*(?=\n---\n)', 'comment'),
        (r'(?<=\n# Learning\n).*(?=\n## Keywords\n)', 'learning'),
        (r'(?<=\n## Keywords\n).*(?=\n## Key notes\n)', 'keyword_links'),
        (r'(?<=\n## Key notes\n).*(?=\n## Quotes\n)', 'key_notes'),
        (r'(?<=\n## Quotes\n).*(?=\n# Abstract\n)', 'quotes')
    ]
    for pattern, key in patterns:
        m = re.search(pattern, note, flags=re.DOTALL)
        if m:
            var_dict[key] = m.group().rstrip()
    return var_dict


def create_zotero_notes(files, cfg):
    # import bib
    libname = "Meine Bibliothek"
    lib_path = f"{cfg['zotero_folder_name']}\\{libname}"
    bib_name = f"{cfg['vault_path']}\\{cfg['zotero_folder_name']}\\{libname}\\{libname}.bib"
    bib_db_clean = util_bibtex.clean(bib_name)

    if cfg['DO_SCORE']:
        k_score_dict = {}
    for ID, entry_dict in bib_db_clean.items():
        rest = ""
        if cfg['DO_OBSIDIAN']:
            filepath = os.path.join(
                cfg['vault_path'], cfg['literature_notes_folder_name'] + "\\@" + ID + ".md")
            # todo: handle if ReadNotes does exist (somewhat handled)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='UTF8') as f:
                    temp_note = f.read()
                    entry_dict = read_from_note(entry_dict, temp_note)

        if 'file' in entry_dict:
            pdfs = extract_pdfs(lib_path, entry_dict['file'])
            if pdfs:
                print("Working on " + ID)

                for file in pdfs:
                    entry_dict = k_score.read_pdf(
                        os.path.join(cfg['vault_path'], file), entry_dict, cfg)
        note = build_literature_note(
            entry_dict, rest, lib_path, cfg)
        if cfg['DO_OBSIDIAN'] and temp_note != note:
            with open(filepath, 'w', encoding='UTF8') as f:
                f.write(note)
    # TODO: Check if exists and needs to be reformated:
    # for now: just overwrite
    # bib = reformat_literature_files(cfg['vault_path'], files)

    # for file in cfg['literature_notes_folder_name']:
    # file_prefix = f"{cfg["zotero_folder_name"]}\\{libname}\\files"
    # for filename in files["zotero"]:
    #     if filename.startswith(file_prefix):
    #         pass
        #         # here lies the attatchment
        if pdfs:
            csv_path = os.path.join(cfg['vault_path'], lib_path)
            if "k_score" in entry_dict:
                k_score_dict[entry_dict['ID']] = entry_dict['k_score']
                k_score.write_to_file(k_score_dict, csv_path, cfg)

    return files


def check_cfg(cfg):
    def merge(cfg):
        return os.path.join(cfg["obsidian_path"], cfg["vault_name"])
    assume = {
        "obsidian_path": personal.OBSIDIAN_PATH,
        "vault_name": "TIB_Obsidian",
        "vault_path": merge,
        "zotero_folder_name": "Zotero",
        "literature_notes_folder_name": "Reading notes",
        "DO_OBSIDIAN": False,
        "DO_SCORE": False,
    }
    for key, value in assume.items():
        if key not in cfg:
            if callable(value):
                cfg[key] = value(cfg)
            else:
                cfg[key] = value
    return cfg

def worth_it(cfg):
    worth_it = False
    for key, value in cfg.items():
        if key.startswith("DO_") and value:
            worth_it = True
    return worth_it

def main(cfg={}):
    # todo: have an option to make this work without obsidian
    cfg = check_cfg(cfg)
    if not worth_it(cfg):
        print("Please select at least one DO_X: TRUE in your config")
        return
    vault_files, vault_folders = helper.extract_file_folder(cfg['vault_path'])
    vault_files += helper.concatenate_nested_files(vault_folders, cfg['vault_path'])
    files = categorize_files(
        vault_files, cfg)
    files = create_zotero_notes(
        files, cfg)

if __name__ == "__main__":
    main()

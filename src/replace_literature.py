import helper
import personalInfos

import re
import os
from typing import List
from typing import Dict
from os import listdir
from os.path import isfile, join
import markdown
import bibtexparser

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


def build_literature_note(field_values: dict, rest: str) -> str:
    """Build output string using string formatting method and join()."""
    # YAML
    date = field_values.get('date', '')
    title = field_values.get('title', '')
    author = field_values.get('author', '')
    in_ = field_values.get('in_', '')
    pages = field_values.get('pages', '')
    cite_title = field_values.get('cite_title', '')
    cite_id = field_values.get('cite_id', '')
    url = field_values.get('url', '')
    zotero = field_values.get('zotero', '')
    tags = field_values.get('tags', '')
    read = field_values.get('read', '')
    comment = field_values.get('comment', '')

    # Rest
    
    langid = field_values.get('langid', '')
    editor = field_values.get('editor', '')
    publisher = field_values.get('publisher', '')
    booktitle = field_values.get('booktitle', '')
    abstract = field_values.get('abstract', '')
    series = field_values.get('series', '')
    doi = field_values.get('doi', '')
    isbn = field_values.get('isbn', '')
    location = field_values.get('location', '')
    ENTRYTYPE = field_values.get('ENTRYTYPE', '')
    isbn = field_values.get('isbn', '')
    ID = field_values.get('ID', '')
    file = field_values.get('file', '')

    if not cite_title:
        cite_title = f"[[@{ID}|{title}]]"
    if not cite_id:
        cite_id = f"\[[[@{ID}|00]]\]"
    if not zotero:
        temp_zot = "zotero://select/items/@" + ID
        zotero = f"[{temp_zot}]({temp_zot})" 
    if not tags:
        tags = "#science #literature "
    if not read:
        tags = "#read/false "


    lines = [
        "---",
        f"date: {date}",
        f"title: {title}",
        f"author: {author}",
        f"in: {in_}",
        f"pages: {pages}",
        "---",
        f"```citeTitle:\n{cite_title}\n```",
        f"```citeID:\n{cite_id}\n```",
        "---",
        f"url: {url}",
        f"zotero: {zotero}",
        "---",
        f"tags:: {tags}",
        f"read?:: {read}",
        f"comment:: {comment}",
        "---\n",
    ]
    yaml = "\n".join(lines)

    lines = [
        "# Learning\n",
        "\n",
        "## Key notes\n",
        "\n",
        "\n",
        "## Quotes\n",
        "\n",
        "\n",
        f"# Abstract\n{abstract}\n",
        "\n",
    ]
    # todo:consider this option for multi-lines:
    """ChatGPT:
    Both of the options you provided are equivalent. They both define the same string with line breaks.

    The first option defines the string as a list of lines and uses the join function to combine the lines into a single string. This can be more readable when the string contains many lines and/or the lines are long. It can also make it easier to modify specific lines, as you can access them using list indexing.

    The second option uses a f-string to insert the value of the abstract variable into the string. The f-string is a feature of Python that allows you to embed expressions inside string literals, using {expression}. The expression is evaluated at runtime and its value is formatted and inserted into the string.

    In general, you can use whichever option you find more readable and maintainable.
    """
    lines = [
        f"""# Learning\n
        \n
        ## Key notes\n
        \n
        \n
        ## Quotes\n
        \n
        \n
        # Abstract\n{abstract}\n
        \n"""
    ]
    return yaml + rest


def reformat(input_string: str, splitter: str = "\n# Learning\n") -> tuple:
    pieces = input_string.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]

    field_values = extract_field_values(work)
    output_string = build_literature_note(field_values, splitter + rest)
    return output_string, field_values


def extract_file_folder(path: str) -> tuple:
    """Return a tuple containing two lists: one for the file names and one for the folder names in the path."""
    file_names = [f for f in listdir(path) if isfile(join(path, f))]
    folder_names = [f for f in listdir(path) if not isfile(join(path, f))]
    return (file_names, folder_names)


def concatenate_files(data_folders_in, input_path):
    files = []
    for folder in data_folders_in:
        if folder[0] == '.':
            continue
        new_path = input_path + "\\" + folder
        data_files, data_folders = extract_file_folder(new_path)
        data_files += concatenate_files(data_folders, new_path)
        for file in data_files:
            files.append(folder + "\\" + file)
    return files


def categorize_files(data_files: List[str], literature_notes_folder_name: str, zotero_folder_name: str) -> Dict[str, List[str]]:
    files = {
        "notes": [],
        "zotero": [],
        "literature_notes": [],
        "others": [],
    }
    for file in data_files:
        if file.endswith('.md'):
            if file.startswith(literature_notes_folder_name + '\\'):
                files["literature_notes"].append(file)
            else:
                files["notes"].append(file)
        elif file.startswith(zotero_folder_name + '\\'):
            files["zotero"].append(file)
        else:
            files["others"].append(file)
    return files


def reformat_literature_files(input_path: str, files: Dict) -> Dict[str, str]:
    bib = {}
    for lit in files["literature_notes"]:
        filepath = os.path.join(input_path, lit)
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


def reformat_note_files(input_path: str, notes: List[str], bib: Dict[str, str]) -> None:
    for note in notes:
        filepath = input_path + '\\' + note
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


def create_zotero_notes(files, input_path, zotero_folder_name, literature_notes_folder_name):
    libname = "Meine Bibliothek"
    bib_name = f"{input_path}\\{zotero_folder_name}\\{libname}\\{libname}.bib"
    bib_path = os.path.join(input_path, bib_name)
    with open(bib_path, encoding='UTF8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    """
    Errors:
    Entry type report not standard. Not considered.
    Entry type online not standard. Not considered.
    Entry type thesis not standard. Not considered.
    """

    def handle_int(key, value):
        value = int(value)
        return {key: value}

    def handle_file(key, value):
        result = {}
        'Full Text PDF:files/4/Sicklinger et al. - 2014 - Interface Jacobian-based Co-Simulation.pdf:application/pdf;Snapshot:files/5/nme.html:text/html'
        files = value.split(';')
        for file in files:
            pieces = file.split(":")
            k = "path_" + pieces[0].replace(" ", "_")
            v = pieces[1]
            result[k] = v
        return {key: result}

    def handle_langid(key, value):
        # might unify landid later
        'english'
        return {key: value}

    def handle_editor(key, value):
        'van Beurden, Martijn and Budko, Neil and Schilders, Wil'
        return {key: value}

    def handle_author(key, value):
        'Georg, Niklas and Lehmann, Christian and Römer, Ulrich and Schuhmann, Rolf'
        return {key: value}

    def handle_publisher(key, value):
        'Springer International Publishing'
        return {key: value}

    def handle_booktitle(key, value):
        'Scientific Computing in Electrical Engineering'
        return {key: value}

    def handle_pages(key, value):
        '127--135'
        return {key: value}

    def handle_abstract(key, value):
        'This work addresses uncertainty quantification for optical structures. We decouple the propagation of uncertainties by combining local surrogate models with a scattering matrix approach, which is then embedded into a multifidelity Monte Carlo framework. The so obtained multifidelity method provides highly efficient estimators of statistical quantities jointly using different models of different fidelity and can handle many uncertain input parameters as well as large uncertainties. We address quasi-periodic optical structures and propose the efficient construction of low-fidelity models by polynomial surrogate modeling applied to unit cells. We recall the main notions of the multifidelity algorithm and illustrate it with a split ring resonator array simulation, serving as a benchmark for the study of optical structures. The numerical tests show speedups by orders of magnitude with respect to the standard Monte Carlo method.'
        return {key: value}

    def handle_series(key, value):
        'Mathematics in Industry'
        return {key: value}

    def handle_doi(key, value):
        '10.1007/978-3-030-84238-3_13'
        return {key: value}

    def handle_isbn(key, value):
        '978-3-030-84238-3'
        return {key: value}

    def handle_title(key, value):
        'Multifidelity Uncertainty Quantification for Optical Structures'
        return {key: value}

    def handle_location(key, value):
        'Cham'
        return {key: value}

    def handle_ENTRYTYPE(key, value):
        'inproceedings'
        return {key: value}

    def handle_ID(key, value):
        'georg_multifidelity_2021'
        return {key: value}

    def default_handler(key, value):
        print(f"No handler found for key '{key}' with value '{value}'")
        return {key: value}

    handlers = {
        'file': handle_file,
        'langid': handle_langid,
        'date': handle_int,
        'editor': handle_editor,
        'author': handle_author,
        'publisher': handle_publisher,
        'booktitle': handle_booktitle,
        'pages': handle_pages,
        'abstract': handle_abstract,
        'series': handle_series,
        'doi': handle_doi,
        'isbn': handle_isbn,
        'title': handle_title,
        'location': handle_location,
        'ENTRYTYPE': handle_ENTRYTYPE,
        'ID': handle_ID
    }

    for entry in bib_database.entries:
        entry_dict = {}
        for key, value in entry.items():
            handler = handlers.get(key, default_handler)
            result = handler(key, value)
            for k, v in result.items():
                entry_dict[k] = v

        rest = ""
        for k, v in entry_dict.items():
            rest += f"{k}: \"{v}\"\n"
        note = build_literature_note(entry_dict, rest)
        filepath = os.path.join(input_path, literature_notes_folder_name+ "\\@" + entry['ID'] + ".md")
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(note)
    # TODO: Check if exists and needs to be reformated:
    # for now: just overwrite
    # bib = reformat_literature_files(input_path, files)

    # for file in literature_notes_folder_name:
    # file_prefix = f"{zotero_folder_name}\\{libname}\\files"
    # for filename in files["zotero"]:
    #     if filename.startswith(file_prefix):
    #         pass
    #         # here lies the attatchment
    return files


def main():
    my_path = os.getcwd()
    obsidian_path = personalInfos.OBSIDIAN_PATH
    TIB_path = obsidian_path + "\\TIB"
    input_path = TIB_path
    zotero_folder_name = "Zotero"
    literature_notes_folder_name = "Reading notes"
    data_files, data_folders = extract_file_folder(input_path)
    data_files += concatenate_files(data_folders, input_path)
    files = categorize_files(
        data_files, literature_notes_folder_name, zotero_folder_name)
    files = create_zotero_notes(
        files, input_path, zotero_folder_name, literature_notes_folder_name)
    reformat_note_files(input_path, files['notes'], bib)


if __name__ == "__main__":
    main()

import re
import os
from os import listdir
from os.path import isfile, join
import markdown

LITERATURE = "Reading notes"

def extract_field_values(input_string: str) -> dict:
    """Extract values of fields from input string using regular expressions."""
    year_published = re.search(r'(?<=year: ).*?(?=\n)', input_string).group()
    title = re.search(r'(?<=title: ).*?(?=\n)', input_string).group()
    authors = re.search(r'(?<=authors: ).*?(?=\n)', input_string).group()
    in_ = re.search(r'(?<=in: ).*?(?=\n)', input_string).group()
    page_range = re.search(r'(?<=page: ).*?(?=\n)', input_string).group()
    cite_title = re.search(r'(?<=citeTitle:[\n ]).*?(?=\n)', input_string).group()
    cite_id = re.search(r'(?<=citeID:[\n ]).*?(?=\n)', input_string).group()
    url = re.search(r'(?<=url: ).*?(?=\n)', input_string).group()
    zotero = re.search(r'(?<=zotero: ).*?(?=\n)', input_string).group()
    tags = re.search(r'(?<=tags:: ).*?(?=\n)', input_string).group()
    read = re.search(r'(?<=read\?:: ).*?(?=\n)', input_string).group()
    comment = re.search(r'(?<=comment:: ).*?(?=\n)', input_string).group()
    return {
        "year_published": year_published,
        "title": title,
        "authors": authors,
        "in_": in_,
        "page_range": page_range,
        "cite_title": cite_title,
        "cite_id": cite_id,
        "url": url,
        "zotero": zotero,
        "tags": tags,
        "read": read,
        "comment": comment
    }

def build_output_string(field_values: dict, rest: str, splitter: str) -> str:
    """Build output string using string formatting method and join()."""
    lines = [
        "---",
        f"year: {field_values['year_published']}",
        f"title: {field_values['title']}",
        f"authors: {field_values['authors']}",
        f"in: {field_values['in_']}",
        f"page: {field_values['page_range']}",
        "---",
        f"```citeTitle:\n{field_values['cite_title']}\n```",
        f"```citeID:\n{field_values['cite_id']}\n```",
        "---",
        f"url: {field_values['url']}",
        f"zotero: {field_values['zotero']}",
        "---",
        f"tags:: {field_values['tags']}",
        f"read?:: {field_values['read']}",
        f"comment:: {field_values['comment']}",
        "---",
    ]
    return "\n".join(lines) + splitter + rest

def reformat(input_string: str, splitter: str = "\n# Learning\n") -> tuple:
    pieces = input_string.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]
    
    field_values = extract_field_values(work)
    output_string = build_output_string(field_values, rest, splitter)
    return output_string, field_values


def extract_file_folder(input_path):
    data_all = [f for f in listdir(input_path)]
    data_files = []
    data_folders = []
    for elm in data_all:
        if isfile(join(input_path, elm)):
            data_files.append(elm)
        else:
            data_folders.append(elm)
    return data_files, data_folders


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

def reformat(text):
    splitter = "\n# Learning\n"
    pieces = text.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]
    finddict = {
        "year" : '(?<=year: ).*?(?=\\n)',
        "title" : '(?<=title: ).*?(?=\\n)',
        "authors" : '(?<=authors: ).*?(?=\\n)',
        "var_in" : '(?<=in: ).*?(?=\\n)',
        "page" : '(?<=page: ).*?(?=\\n)',
        "citeTitle" : '(?<=citeTitle:[\n ]).*?(?=\\n)',
        "citeID" : '(?<=citeID:[\n ]).*?(?=\\n)',
        "url" : '(?<=url: ).*?(?=\\n)',
        "zotero" : '(?<=zotero: ).*?(?=\\n)',
        "tags" : '(?<=tags:: ).*?(?=\\n)',
        "read?" : '(?<=read\?:: ).*?(?=\\n)',
        "comment" : '(?<=comment:: ).*?(?=\\n)',
    }
    dic_var = {}
    for key, value in finddict.items():
        dic_var[key] = re.search(value, work).group()
        if key == "title" or key == "authors" or key == "var_in":
            if len(dic_var[key]) > 0:
                if dic_var[key].startswith('"'):
                    pass
                elif dic_var[key].startswith(' '):
                    dic_var[key][0] = '"'
                else:
                    dic_var[key] = '"' + dic_var[key]
                if dic_var[key].endswith('"'):
                    pass
                elif dic_var[key].endswith(' '):
                    dic_var[key][-1] = '"'
                else:
                    dic_var[key] = dic_var[key] + '"'
    
    build = "---\n"
    build += "year: " + dic_var["year"] + "\n"
    build += "title: " + dic_var["title"] + "\n"
    build += "authors: " + dic_var["authors"] + "\n"
    build += "in: " + dic_var["var_in"] + "\n"
    build += "page: " + dic_var["page"] + "\n"
    build += "---\n"
    build += "```citeTitle:\n" + dic_var["citeTitle"] + "\n```\n"
    build += "```citeID:\n" + dic_var["citeID"] + "\n```\n"
    build += "---\n"
    build += "url: " + dic_var["url"] + "\n"
    build += "zotero: " + dic_var["zotero"] + "\n"
    build += "\n---\n"
    build += "tags:: " + dic_var["tags"] + "\n"
    build += "read?:: " + dic_var["read?"] + "\n"
    build += "comment:: " + dic_var["comment"] + "\n"
    build += "\n---\n"
    text = build + splitter + rest
    return text, dic_var

my_path = os.getcwd()
obsidian_path = os.path.dirname(my_path)
TIB_path = obsidian_path + "\\TIB"
input_path = TIB_path
data_files, data_folders = extract_file_folder(input_path)
data_files += concatenate_files(data_folders, input_path)
notes = []
literature = []
for file in data_files:
    if file.endswith('.md'):
        if file.startswith(LITERATURE + '\\'):
            literature.append(file)
        else:
            notes.append(file)
bib = {}
for lit in literature:
    filepath = input_path + '\\' + lit
    with open(filepath, 'r', encoding='UTF8') as f:
        text = f.read()
    text_in = text
    text, var_dict = reformat(text)
    with open(filepath, 'w', encoding='UTF8') as f:
        f.write(text)
    pieces = var_dict["citeTitle"].split('|', 1)
    
    # m = re.findall('(?<=citeTitle:\\n\[\[).*?(?=\]\]\\n)', text)[0]
    # pieces = m.split('|', 1)
    uid = pieces[0]
    title = pieces[1]
    bib.update({uid: title})
    bell = "ring"


for note in notes:
    filepath = input_path + '\\' + note
    with open(filepath, 'r', encoding='UTF8') as f:
        text = f.read()
    text_in = text
    for uid, title in bib.items():
        check = [title]
        if "?" in title:
            temp = []
            for token in check:
                temp.append(token.replace("?", "❓"))
            check += temp
        if ":" in title:
            temp = []
            for token in check:
                temp.append(token.replace(":", ";"))
            check += temp
        if "–" in title:
            temp = []
            for token in check:
                temp.append(token.replace("–", "-"))
            check += temp
        for token in check:
            text = re.sub(re.escape(
                "[[" + token + "]]"), "[[" + uid + "|" + title + "]]", text, flags=re.I)
            text = re.sub(re.escape("[[" + token),
                          "[[" + uid, text, flags=re.I)
    if text != text_in:
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(text)
        bell = "ring"
    bell = "ring"
import util_bibtex
import os
import re
from typing import List, Dict, Any, Union
import shutil


class BibTeXEntry:
    def __init__(self, bib_entry: Dict[str, Any]) -> None:
        self.entry_type: str = bib_entry['ENTRYTYPE']
        self.citation_key: str = bib_entry['ID']
        for key, value in bib_entry.items():
            if value is None or key in ['entry_type', 'citation_key', 'ENTRYTYPE', 'ID']:
                continue
            # if not hasattr(self, key):
            #     print(
            #         f"Attribute '{key}' is a new type of BibTeX property. Please add it to the BibTeXEntry class.")
            setattr(self, key, value)

    def get(self, attr: str):
        try:
            return getattr(self, attr)
        except:
            return None

    def get_links(self):
        file = self.get("file")
        if not file:
            return None
        links = []
        link_pattern = r'(?<!\\);'
        sub_pattern = r'([^:]+):((?:\\.|[^\\:])*):([^:]+)'
        for group in re.split(link_pattern, file):
            for link in re.findall(sub_pattern, group):
                name, path, mime_type = link
                path = path.replace("\\:\\", ":\\")
                path = path.replace("\\\\", "\\")
                path = path.replace("\\;", ";")
                links.append({
                    'name': name.strip(),
                    'path': path.strip(),
                    'mime_type': mime_type.strip()
                })
        return links

    def save(self, file_path: str = None, mode: str = 'w') -> str:
        res = ""
        res += f"@{self.entry_type}{{{self.citation_key},\n"
        for attribute, value in reversed(self.__dict__.items()):
            if value is None or attribute in ['entry_type', 'citation_key']:
                continue
            if isinstance(value, list):
                value = " and ".join(value)
            res += f"    {attribute} = {{{value}}},\n"
        res += "}\n\n"
        if file_path:
            with open(file_path, mode, encoding="utf-8") as file:
                file.write(res)
        return res


def store_bibtex_entries(entries: List[BibTeXEntry], file_path: str, mode: str = 'w') -> None:
    with open(file_path, mode, encoding="utf-8") as file:
        for entry in entries:
            file.write(entry.save())


def sort_pdf(entries: List[BibTeXEntry], root_folder: str, dst_folder: str) -> None:
    for entry in entries:
        links = entry.get_links()
        if links is None:
            continue
        # todo: Handle if item exists twice
        # todo: Handle if item has ;
        # remove unwanteds
        basenames = [os.path.basename(file_link['path'])
                     for file_link in links]
        drop = {}
        for name in basenames:
            if basenames.count(name) > 1 and name not in drop:
                indices = [i for i, x in enumerate(basenames) if x == name]
                for i in indices:
                    if links[i]['path'].startswith("files/"):
                        indices.remove(i)
                        drop[name] = indices
                        break
        queue = sorted([val for sublist in drop.values()
                       for val in sublist], reverse=True)
        for i in queue:
            links.pop(i)
        for file_link in links:
            name, path, mime_type = file_link['name'], file_link['path'], file_link['mime_type']
            basename = os.path.basename(path)
            dst_folder_new = os.path.join(dst_folder, entry.citation_key)
            dst_path = os.path.join(dst_folder_new, basename)
            os.makedirs(dst_folder_new, exist_ok=True)
            move = False
            src_path = path
            if not os.path.isabs(path):
                # relative -> copy
                src_path = os.path.join(root_folder, path)
                move = True

            if not os.path.exists(src_path):
                print(
                    f"Warning: File '{src_path}' not found for entry '{entry.citation_key}'.")
                continue

            if os.path.exists(dst_path):
                dst_path = os.path.join(
                    dst_folder_new, f"{entry.citation_key}_{basename}")
            if move:
                try:
                    shutil.move(src_path, dst_path)
                except Exception as e:
                    print(e)
            else:
                shutil.copy(src_path, dst_path)
            file_link['path'] = os.path.relpath(dst_path, root_folder)

    walk = list(os.walk(os.path.join(root_folder, "files")))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            os.rmdir(path)


# class BibTeXEntry:
#     def __init__(self, entry_type=None, citation_key=None, fields=None):
#         self.entry_type = entry_type
#         self.citation_key = citation_key
#         self.fields = fields or {}

#     def add_field(self, field_name, field_value):
#         self.fields[field_name] = field_value

#     def __str__(self):
#         fields_str = ', '.join(f'{key}={val}' for key, val in self.fields.items())
#         return f'{self.entry_type}{{{self.citation_key},\n{fields_str}\n}}'


def convert_export(path):
    files_folder_path = None
    bibtex_path = None
    PDF_path = os.path.join(path, "00_PDFs")
    folder_name = os.path.basename(path)
    for entry in os.listdir(path):
        if entry == "files" and os.path.isdir(os.path.join(path, entry)):
            files_folder_path = os.path.join(path, entry)
        elif entry == folder_name + ".bib" and os.path.isfile(os.path.join(path, entry)):
            bibtex_path = os.path.join(path, entry)
    if not bibtex_path or not files_folder_path:
        print(f"Missing Zotero export at {path}:")
        if not bibtex_path:
            print(f"There must be a file called '{folder_name}.bib'")
        if not bibtex_path:
            print(f"There must be a folder called 'files'")

    with open(bibtex_path, encoding="utf-8") as bibtex_file:
        parser = util_bibtex.bibtexparser.bparser.BibTexParser()
        parser.ignore_nonstandard_types = False
        parser.homogenize_fields = False
        parser.common_strings = False
        bib_database = util_bibtex.bibtexparser.load(bibtex_file, parser)

    entries = [BibTeXEntry(entry) for entry in bib_database.entries]
    sort_pdf(entries, path, PDF_path)
    store_bibtex_entries(
        entries, bibtex_path.replace(".bib", "_processed.bib"))

    bib = util_bibtex.clean(bibtex_path)
    resources: List[BibTeXEntry] = []
    for resource in bib:
        resources.append(BibTeXEntry(fields=resource))


convert_export("D:\workspace\Zotero\SE2A-B4-2")

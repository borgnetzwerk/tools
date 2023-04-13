import bibtexparser
import os
import re
from typing import List, Dict, Any
import shutil


class BibTeXEntry:
    def __init__(self, bib_entry: Dict[str, Any]) -> None:
        self.entry_type: str = bib_entry['ENTRYTYPE']
        self.citation_key: str = bib_entry['ID']
        for key, value in bib_entry.items():
            if value is None or key in ['entry_type', 'citation_key', 'ENTRYTYPE', 'ID']:
                continue
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
        res = "\n"
        res += f"@{self.entry_type}{{{self.citation_key},\n"
        for attribute, value in reversed(self.__dict__.items()):
            if value is None or attribute in ['entry_type', 'citation_key']:
                continue
            if isinstance(value, list):
                value = " and ".join(value)
            res += f"    {attribute} = {{{value}}},\n"
        res += "}\n"
        if file_path:
            with open(file_path, mode, encoding="utf-8") as file:
                file.write(res)
        return res


class BibResources:
    def __init__(self, path=None, entries: List[BibTeXEntry] = None) -> None:
        self.entries: List[BibTeXEntry] = entries or []
        self.folder_path = path or None
        self.files_folder_path = None
        self.bibtex_path = None
        self.pdf_path = None
        if path:
            self.from_path(path)

    def get_pdf_path(self, path=None):
        if self.pdf_path and not path:
            return self.pdf_path
        if path is None:
            path = self.folder_path
        else:
            self.folder_path = path
        self.pdf_path = os.path.join(path, "00_PDFs")
        return self.pdf_path

    def add_entries(self):
        with open(self.bibtex_path, encoding="utf-8") as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser()
            parser.ignore_nonstandard_types = False
            parser.homogenize_fields = False
            parser.common_strings = False
            bib_database = bibtexparser.load(bibtex_file, parser)
            self.entries.extend(BibTeXEntry(entry)
                                for entry in bib_database.entries)

    def from_path(self, path):
        self.get_pdf_path(path)
        folder_name = os.path.basename(path)
        for entry in os.listdir(path):
            if entry == "files" and os.path.isdir(os.path.join(path, entry)):
                files_folder_path = os.path.join(path, entry)
            elif entry == folder_name + ".bib" and os.path.isfile(os.path.join(path, entry)):
                self.bibtex_path = os.path.join(path, entry)

        if not self.bibtex_path or not files_folder_path:
            print(f"Missing Zotero export at {path}:")
            if not self.bibtex_path:
                print(f"There must be a file called '{folder_name}.bib'")
            if not self.bibtex_path:
                print(f"There must be a folder called 'files'")
            return None

        self.add_entries()
        self.sort_pdf()
        self.store_bibtex_entries(
            self.bibtex_path.replace(".bib", "_processed.bib"))

    def store_bibtex_entries(self, new_file_name=None) -> None:
        if new_file_name is None:
            new_file_name = self.bibtex_path
        with open(new_file_name, "w", encoding="utf-8") as file:
            for entry in self.entries:
                file.write(entry.save())

    def sort_pdf(self) -> None:
        for entry in self.entries:
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
                dst_folder_new = os.path.join(
                    self.get_pdf_path(), entry.citation_key)
                dst_path = os.path.join(dst_folder_new, basename)
                os.makedirs(dst_folder_new, exist_ok=True)
                move = False
                src_path = path
                if not os.path.isabs(path):
                    # relative -> copy
                    src_path = os.path.join(self.folder_path, path)
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
                file_link['path'] = os.path.relpath(dst_path, self.folder_path)

        walk = list(os.walk(os.path.join(self.folder_path, "files")))
        for path, _, _ in walk[::-1]:
            if len(os.listdir(path)) == 0:
                os.rmdir(path)


bibs = BibResources(path="D:\workspace\Zotero\SE2A-B4-2")

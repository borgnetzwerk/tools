import bibtexparser
import os
import re
from typing import List, Dict, Any
import shutil


class BibTeXEntry:
    # To Debug:
    # keys = set()
    def __init__(self, bib_entry: Dict[str, Any]) -> None:
        self.entry_type: str = bib_entry['ENTRYTYPE']
        self.citation_key: str = bib_entry['ID']
        for key, value in bib_entry.items():
            if value is None or key in ['entry_type', 'citation_key', 'ENTRYTYPE', 'ID']:
                continue
            setattr(self, key, value)
            # To Debug:
            # BibTeXEntry.keys.add(key)

    def merge(self, other: 'BibTeXEntry', extra_careful = False) -> None:
        if hasattr(self,'entry_type') and hasattr(other, 'entry_type') and self.entry_type != other.entry_type:
            # better not merge different entries
            return False
        
        if hasattr(self, 'file') and ".pdf" in self.file:
            pass
        elif hasattr(other, 'file') and ".pdf" in other.file:
            # the other is a better version
            other.merge(self)
            setattr(other, 'citation_key', self.citation_key)
            self = other
            return True

        for key, value in other.__dict__.items():
            # priority for the entry that has a pdf:

            # handled above or not needed
            if value is None or key in ['citation_key', 'entry_type', 'file']:
                continue
            # not sure if we want to merge these. They might change what the entry is about
            skip = ['url', 'urldate']
            if key in skip:
                continue

            if key not in self.__dict__:
                # if the key is not in the original, we can add it.
                if not extra_careful:
                    setattr(self, key, value)
            else:
                old = getattr(self, key)
                if old == value:
                    continue
                else:
                    # TODO: Merge if both have an attribute, but they are not the same
                    if old in value:
                        # presume the longer is a more detailed version:
                        setattr(self, key, value)
                    elif value in old:
                        # the longer is already the existing one
                        continue
                    else:
                        if key == 'author':
                            # merge authors
                            # TODO: Complicated merge. Order, abreviations, differnt characters, ...
                            # authors_old = old.split(" and ")
                            # authors_new = value.split(" and ")
                            pass
                        else:
                            pass
        
        return True

    def get_dict(self):
        res_dict = vars(self)
        if "entry_type" in res_dict:
            res_dict["ENTRYTYPE"] = res_dict.pop("entry_type")
        if "citation_key" in res_dict:
            res_dict["ID"] = res_dict.pop("citation_key")
        return res_dict

    def get(self, attr: str):
        try:
            if attr == "dict":
                return self.get_dict()
            return getattr(self, attr)
        except:
            return None

    def get_links(self):
        file = self.get("file")
        if not file:
            return None
        links = {}
        link_pattern = r'(?<!\\);'
        sub_pattern = r'([^:]+):((?:\\.|[^\\:^\\])*):([^:]+)'
        for group in re.split(link_pattern, file):
            for link in re.findall(sub_pattern, group):
                name, path, mime_type = link
                path = path.replace("\\:\\", ":\\")
                path = path.replace("\\\\", "\\")
                path = path.replace("\\;", ";")
                links.update({path.strip(): {
                    'name': name.strip(),
                    'mime_type': mime_type.strip()
                }
                })
        return links

    def set_links(self, links: Dict[str, str]):
        res = []
        for path, values in links.items():
            name = values["name"]
            mime_type = values["mime_type"]
            path = path.replace(";", "\\;")
            path = path.replace(":\\", "\\:\\\\")
            # path = path.replace("\\", "\\\\")
            res.append(f"{name}:{path}:{mime_type}")
        self.file = ";".join(res)

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
    def __init__(self, path=None, entries: Dict[str, BibTeXEntry] = None) -> None:
        self.entries: Dict[str, BibTeXEntry] = entries or {}
        self.missing: Dict[str, BibTeXEntry] = {}
        self.folder_path = path or None
        self.files_folder_path = None
        self.bibtex_path = None
        self.pdf_path = None
        self.pdfs = []
        if path:
            self.from_path(path)

    def get_metadata(self, path: str):
        if path in self.pdfs:
            i = self.pdfs.index(path)
            basename = os.path.basename(os.path.dirname(path))
            if basename in self.entries:
                data = self.entries[basename].get_dict()
                return data
            else:
                print("Error adding metadata for " + path)
                return -1

            # data = list(self.entries.values())[i].get_dict()

            # if data and 'file' in data:
            #     if path not in data['file']:
            #         print("Error adding metadata for " + path)
            # return data
        return None

    def get_pdf_path(self, path=None):
        if self.pdf_path and not path:
            return self.pdf_path
        if path is None:
            path = self.folder_path
        else:
            self.folder_path = path
        self.pdf_path = os.path.join(path, "00_PDFs")
        return self.pdf_path

    def merge_duplicates(self):
        """
        example: These are NOT equal
        @inproceedings{agrawal_web-based_2004,
            address = {Palm Springs, California},
            title = {Web-based {Visualization} {Environment} for {Decision}-{Making} in {Multidisciplinary} {Design} {Optimization}},
            isbn = {978-1-62410-079-6},
            url = {http://arc.aiaa.org/doi/abs/10.2514/6.2004-1684},
            doi = {10.2514/6.2004-1684},
            language = {en},
            urldate = {2024-02-27},
            booktitle = {45th {AIAA}/{ASME}/{ASCE}/{AHS}/{ASC} {Structures}, {Structural} {Dynamics} \&amp; {Materials} {Conference}},
            publisher = {American Institute of Aeronautics and Astronautics},
            author = {Agrawal, Gautam and English, Ken and Bloebaum, Christina and Bisantz, A. and Uggirala, A.},
            month = apr,
            year = {2004},
        }

        @inproceedings{agrawal_web-based_2004-1,
            title = {Web-based visualization framework for decision-making in multidisciplinary design optimization},
            url = {https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=e94eda1e9ac59fb4202d213685594c903e7910d7},
            urldate = {2024-02-27},
            booktitle = {45th {AIAA}/{ASME} {Conference}},
            publisher = {Citeseer},
            author = {Agrawal, G. and Parashar, S. and English, K. W. and Bloebaum, C. L.},
            year = {2004},
            pages = {19--22},
            file = {Available Version (via Google Scholar):files/9423/Agrawal et al. - 2004 - Web-based visualization framework for decision-mak.pdf:application/pdf},
        }
        """

        duplicates = {}
        for key, value in self.entries.items():
            # can only catch duplicates up to 99. should be enough
            if '-' in key[-3:]:
                original_key = key.rsplit('-', 1)[0]
                if original_key in self.entries:
                    if original_key not in duplicates:
                        duplicates[original_key] = []
                    duplicates[original_key].append(value)
        
        del_keys = {}

        for key, value in duplicates.items():
            original = self.entries[key]
            for entry in value:
                # check if they are the same
                check_similarity = {
                    "title" : 0,
                    "year": 0,
                    "author": 0
                }
                
                for attr in check_similarity:
                    if hasattr(original, attr) and hasattr(entry, attr):
                        original_attr = getattr(original, attr)
                        entry_attr = getattr(entry, attr)
                        if original_attr == entry_attr:
                            check_similarity[attr] = 1
                        else:
                            original_attr_string = ''.join(letter for letter in original_attr if letter.isalnum()).lower()
                            entry_attr_string = ''.join(letter for letter in entry_attr if letter.isalnum()).lower()
                            if original_attr_string and original_attr_string == entry_attr_string:
                                check_similarity[attr] = 0.9

                if check_similarity["title"]:
                    # they are the same
                    if sum(check_similarity.values()) >= 1.5:
                        if original.merge(entry):
                            # print(f"Merged {entry.citation_key} into {original.citation_key}")
                            del_keys[entry.citation_key] = entry
                        else:
                            # did not merge -> keep both.
                            pass

        del_path =  self.bibtex_path.replace(".bib", "_merged.bib")
        self.store_bibtex_entries(new_file_name=del_path, entries=del_keys)
        for key, entry in del_keys.items():
            del self.entries[key]

    def add_entries(self):
        with open(self.bibtex_path, encoding="utf-8") as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser()
            parser.ignore_nonstandard_types = False
            parser.homogenize_fields = False
            parser.common_strings = False
            bib_database = bibtexparser.load(bibtex_file, parser)
            for entry in bib_database.entries:
                value = BibTeXEntry(entry)
                key = value.citation_key
                self.entries[key] = value


        self.merge_duplicates()
        # To Debug:
        # print(BibTeXEntry.keys)

    def look_for_export(self, path, folder_name):
        for entry in os.listdir(path):
            if entry == folder_name and os.path.isdir(os.path.join(path, entry)):
                new_path = os.path.join(path, entry)
                self.look_for_export(new_path, folder_name)
                if self.files_folder_path and self.bibtex_path:
                    return
            # todo: make an implementation where the og bibtex file is written on
            elif entry == "files" and os.path.isdir(os.path.join(path, entry)):
                self.files_folder_path = os.path.join(path, entry)
            elif entry == folder_name + ".bib" and os.path.isfile(os.path.join(path, entry)):
                self.bibtex_path = os.path.join(path, entry)

    def from_path(self, path):
        self.get_pdf_path(path)
        # if path ends on "/", we need to prune that:
        if path[-1] == "/":
            path = path[:-1]
        # TODO: See if this applies to other areas as well
        folder_name = os.path.basename(path)
        self.look_for_export(path, folder_name)

        if not self.bibtex_path or not self.files_folder_path:
            print(f"Found no new Zotero export at {path}:")
            if not self.files_folder_path:
                print(f"There should be a folder called 'files'")
            if not self.bibtex_path:
                print(f"There must be a file called '{folder_name}.bib'")
                return None

        self.add_entries()
        self.sort_pdf()
        self.store_bibtex_entries(
            self.bibtex_path.replace(".bib", "_processed.bib"))

    def store_bibtex_entries(self, new_file_name=None, entries: Dict[str, BibTeXEntry]=None) -> None:
        if entries is None:
            entries = self.entries
        if new_file_name is None:
            new_file_name = self.bibtex_path
        with open(new_file_name, "w", encoding="utf-8") as file:
            for entry in entries.values():
                file.write(entry.save())

    def sort_pdf(self) -> None:
        for entry in self.entries.values():
            old_links = entry.get_links()
            if old_links is None:
                continue
            links = {}
            dst_folder = os.path.join(
                self.get_pdf_path(), entry.citation_key)

            failures: Dict[str, List] = {}
            for src_path, values in old_links.items():
                basename = os.path.basename(src_path)
                dst_path = os.path.join(dst_folder, basename)

                move = False
                failed = False
                if not os.path.isabs(src_path) and src_path.startswith("files"):
                    # relative -> copy
                    if self.files_folder_path:
                        prefix = self.files_folder_path
                        if src_path.startswith("files"):
                            prefix = os.path.dirname(prefix)
                        src_path = os.path.join(prefix, src_path)
                        move = True

                if os.path.exists(dst_path):
                    if dst_path not in links:
                        links[dst_path] = values
                        if dst_path.endswith(".pdf"):
                            self.pdfs.append(dst_path)
                    if move and os.path.exists(src_path):
                        os.remove(src_path)
                    continue

                if not os.path.exists(src_path):
                    failed = True

                if not failed:
                    os.makedirs(dst_folder, exist_ok=True)
                    if move:
                        try:
                            shutil.move(src_path, dst_path)
                        except Exception as e:
                            print(e)
                            failed = True
                    else:
                        try:
                            shutil.copy(src_path, dst_path)
                        except Exception as e:
                            print(e)
                            failed = True
                if not failed:
                    links[dst_path] = values
                    if basename in failures:
                        del failures[basename]
                    if dst_path.endswith(".pdf"):
                        self.pdfs.append(dst_path)
                else:
                    if basename not in failures:
                        failures[basename] = []
                    failures[basename].append(src_path)

            entry.set_links(links)
            for key, values in failures.items():
                print('Missing: ' + ' ; '.join(values))
                continue
        if self.files_folder_path:
            walk = list(os.walk(self.files_folder_path))
            for path, _, _ in walk[::-1]:
                if len(os.listdir(path)) == 0:
                    os.rmdir(path)
        walk = list(os.walk(self.get_pdf_path()))
        for path, _, _ in walk[::-1]:
            if len(os.listdir(path)) == 0:
                os.rmdir(path)
        print(f"We now have {len(self.pdfs)} PDFs stored at {self.pdf_path}")

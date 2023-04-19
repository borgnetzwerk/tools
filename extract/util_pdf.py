import pdfminer
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfrw import PdfReader
from pdfquery import PDFQuery
from tika import parser
import PyPDF2
import fitz
import io
import os
import re
import Levenshtein
from typing import List
import statistics
from collections import defaultdict
# does not (really) work on windows: from polyglot.detect import Detector


class PDFDocument:
    def __init__(self, path=None, text=None, pages=None, language=None, force=False):
        """
        A class representing a PDF document.

        Args:
            path (str): Path to the PDF document.
            text (str): Text content of the PDF document.
            pages (list): A list of strings, where each string is the text content of a single page.

        Attributes:
            path (str): Path to the PDF document.
            text (str): Text content of the PDF document.
            pages (list): A list of strings, where each string is the text content of a single page.
        """
        self.path = path
        self.text = text
        self.text_path = None
        self.pages = pages
        self.language = language
        if path:
            self.fromfile(force=force)
            self.save(force=force)

    def get_text_path(self):
        if self.text_path:
            return self.text_path
        if self.path:
            self.text_path = self.path.replace(".pdf", ".txt")
            return self.text_path
        else:
            return None

    def get_dict(self):
        return {
            'text': self.text,
        }

    def get(self, attr: str):
        if attr == "dict":
            return self.get_dict()
        elif hasattr(self, attr):
            return getattr(self, attr)

    def save(self, force=False):
        if self.text:
            if force or not os.path.exists(self.text_path):
                with open(self.get_text_path(), "w", encoding="utf-8") as f:
                    f.write(self.text)

    def from_text_file(self):
        with open(self.text_path, "r", encoding="utf-8") as f:
            self.text = f.read()

    def fromfile(self, path=None, force=False):
        """
        Load PDF document from the given path.

        Args:
            path (str): Path to the PDF document.
        """
        if not force and os.path.exists(self.get_text_path()):
            self.from_text_file()
            self.detect_language()
            return
        if path is None:
            path = self.path
        else:
            self.path = path
        if not path:
            print("need path to load PDFDocument")
            return None
        # Ranking according to minor testing, future improvements welcome!
        if not self.text:
            self.text = extract_text_pdfminer(path)
        if not self.text:
            self.text = extract_text_pymupdf(path)
        if not self.text:
            self.text = extract_text_pypdf2(path)
        if not self.text:
            self.text = extract_text_pdfquery(path)
        # needs Java
            # self.text_tika = extract_text_tika(path)
        # looks like this can't do proper text
            # self.text_pdfrw = extract_text_pdfrw(path)
        self.clean_text()
        self.detect_language()

    def detect_language(self):
        # https://stackoverflow.com/questions/39142778/how-to-determine-the-language-of-a-piece-of-text
        # TODO: All these seem to involve further libraries like Visual C++ etc., and/or are tricky to run on Windows
        if not self.language:
            # todo: implement actual detection once issues are resolved
            self.language = "en"

    def clean_text(self, level=3):
        # https://tex.stackexchange.com/questions/33476/why-cant-fi-be-separated-when-being-copied-from-a-compiled-pdf
        changes = {
            "lvl1": {
                "ﬁ": "fi",
                "ﬀ": "ff",
                "ﬁ": "fi",
                "ﬂ": "fl",
                "ﬃ": "ffi",
                "ﬄ": "ffl",
            },
            "lvl2": {
                "–": "--",
                "—": "---"
            },
            "lvl3": {
                "“": "‘‘",
                "”": "’’",
                "¡": "!‘",
                "¿": "?‘",
            }
        }
        if not self.text:
            return None
        for swap in list(changes.values())[:level]:
            for wrong, right in swap.items():
                self.text = self.text.replace(wrong, right)
        # TODO: Remove lines that are not text, i.e. page numbers, Header, Footer, etc.
        # Optional: Remove Footnotes etc., though these may provide value

    def iscomplete(self):
        if self.path and self.text:
            return True
        return False

    def complete(self, path=None):
        if not self.iscomplete():
            self.fromfile(path)
        return self.iscomplete()

    def get_dict(self):
        return {
            'text': self.text,
            'pages': self.pages,
        }


def extract_text_pypdf2(pdf_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page_obj = pdf_reader.pages[page_num]
                text += page_obj.extract_text()
            return text
    except Exception as e:
        print(e)
        return None


def extract_text_tika(pdf_path):
    try:
        parsed_pdf = parser.from_file(pdf_path)
        return parsed_pdf['content']
    except Exception as e:
        print(e)
        return None


def extract_text_pymupdf(pdf_path):
    try:
        text = ''
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text
    except Exception as e:
        print(e)
        return None


def extract_text_pdfrw(pdf_path):
    # looks like this can't export proper Text
    try:
        pdf = PdfReader(pdf_path)
        text = ''
        for page in pdf.pages:
            text += page.Contents.stream
        return text
    except Exception as e:
        print(e)
        return None


MIN_SUFFIX_LENGTH = 3
MAX_SUFFIX_LENGTH = 500
HISTORY_LENGTH = 5


def find_similar_ending(string_list: List[str], begin=MIN_SUFFIX_LENGTH, history=HISTORY_LENGTH, do_endings=True):
    numbers_regex = r"\d+"
    x = begin

    true_shared_threshold = len(string_list)/3
    endings = defaultdict(None)
    banished = []
    while x < MAX_SUFFIX_LENGTH:
        possible_endings = defaultdict(list)
        if do_endings:
            candidates = [piece[-x:] for piece in string_list]
        else:
            candidates = [piece[:x] for piece in string_list]
        for idx, candidate in enumerate(candidates):
            if idx in banished:
                continue
            clean_candidate = re.sub(numbers_regex, "0", candidate)
            if clean_candidate:
                possible_endings[clean_candidate].append(idx)
        for ending, users in possible_endings.items():
            # FIXME: current iteration struggles to handle:
                # "beginnings", starting 
                # "endings", ending 
            # with different amounts of digits
            if len(users) < true_shared_threshold:
                for user in users:
                    if user in endings and endings[user] == ending:
                        pass
                    else:
                        endings[user] = x-1 if x > begin else None
                        banished.append(user)
            else:
                for user in users:
                    endings[user] = ending
        x += 1
        if len(banished) == len(string_list):
            return endings


def remove_repetition(string_list: List[str], footer: bool = True, header: bool = True, merge: bool = True) -> str:
    result = ""
    endings = find_similar_ending(string_list, MIN_SUFFIX_LENGTH)
    openings = find_similar_ending(string_list, MIN_SUFFIX_LENGTH, do_endings=False)
    for i in range(len(string_list)):
        end_limit = -endings[i] if (i in endings and endings[i]) else None
        start_limit = openings[i] if i in openings else None
        result += string_list[i][start_limit:end_limit]
    return result
    # if header:
    # if merge:
    #     return


def extract_text_pdfminer(pdf_path, clean=False):
    # Rank 1: appears to be the best. Formatting is nice, accuracy works.
    # Tested: Can read multiple Columns correctly
    # Test pending: Scans
    if not clean:
        text = extract_text(pdf_path, laparams=LAParams())
        return text
    # todo: cleaning is messy right now.
    with open(pdf_path, 'rb') as fp:
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(
            rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        pages = []
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
            pages.append(retstr.getvalue())
            retstr.truncate(0)
            retstr.seek(0)
        return remove_repetition(pages)



def extract_text_pdfquery(pdf_path):
    try:
        pdf = PDFQuery(pdf_path)
        pdf.load()
        text = ''
        for element in pdf.tree.iter():
            if element.text:
                text += element.text
        return text
    except Exception as e:
        print(e)
        return None


filename = "D:/workspace/Zotero/SE2A-B4-2/00_PDFs/allaire_mathematical_2014/Allaire und Willcox - 2014 - A MATHEMATICAL AND COMPUTATIONAL FRAMEWORK FOR MUL.pdf"

PDFDocument(filename, force=True)

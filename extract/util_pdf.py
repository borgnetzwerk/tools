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
                with open(self.text_path, "w", encoding="utf-8") as f:
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


MIN_SUFFIX_LENGTH = 5
MAX_SUFFIX_LENGTH = 500
HISTORY_LENGTH = 5


def keeps_getting_worse(l):
    for el in l[1:]:
        if el >= l[0]:
            return False
    return True


def find_similar_ending(string_list: List[str], begin=MIN_SUFFIX_LENGTH, history=HISTORY_LENGTH):
    numbers_regex = r"\d+"
    recent_sims = [0] * history
    x = begin
    matched_pattern = ""
    while x < MAX_SUFFIX_LENGTH:
        dst = 1
        candidates = [piece[-x:] for piece in string_list]
        for idx, candidate in enumerate(candidates):
            candidates[idx] = re.sub(numbers_regex, "0", candidate)
        similar_to = []
        for idc, candidate in enumerate(candidates[:-dst]):
            if candidate:
                similar_to.append(1 - (Levenshtein.distance(
                    candidate, candidates[idc+dst]) / x))
        min_sim = min(similar_to)
        max_sim = max(similar_to)
        median_sim = statistics.median(similar_to)
        recent_sims.pop(0)
        recent_sims.append(median_sim)
        x += 1
        if keeps_getting_worse(recent_sims):
            return x-history
            # valid run


def remove_repetition(string_list: List[str], footer: bool = True, header: bool = True, merge: bool = True) -> List[str]:
    if footer:
        even_odd_equal = False
        len_s = find_similar_ending(string_list, MIN_SUFFIX_LENGTH)
        if len_s == MIN_SUFFIX_LENGTH:
            even = []
            odd = []
            for idx, string in enumerate(string_list):
                if idx % 2 == 0:
                    even.append(string)
                else:
                    odd.append(string)

            len_s_even = find_similar_ending(even, MIN_SUFFIX_LENGTH)
            if len_s_even == MIN_SUFFIX_LENGTH:
                cry = True
                # todo
            len_s_odd = find_similar_ending(odd, MIN_SUFFIX_LENGTH)
            if len_s_odd == MIN_SUFFIX_LENGTH:
                cry = True
                # todo
            result = 0
            for idx in range(len(string_list)):
                if idx % 2 == 0:
                    result += even.pop(0)[:-len_s_even]
                else:
                    result += odd.pop(0)[:-len_s_odd]

        return result
    return None
    # if header:
    # if merge:
    #     return


def extract_text_pdfminer(pdf_path, clean=True):
    # Rank 1: appears to be the best. Formatting is nice, accuracy works.
    # Tested: Can read multiple Columns correctly
    # Test pending: Scans
    try:
        if not clean:
            text = extract_text(pdf_path, laparams=LAParams())
            return text
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
        try:
            remove_repetition(pages)
        except Exception as e:
            print(e)
            return "".join(pages)
    except Exception as e:
        print(e)
        return None


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

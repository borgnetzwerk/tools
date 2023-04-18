from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfrw import PdfReader
from pdfquery import PDFQuery
from tika import parser
import PyPDF2
import fitz
import io
import os
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
            self.fromfile()
            self.save()

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
        if os.path.exists(self.get_text_path()):
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


def extract_text_pdfminer(pdf_path):
    # Rank 1: appears to be the best. Formatting is nice, accuracy works.
    try:
        text = extract_text(pdf_path, laparams=LAParams())
        return text
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

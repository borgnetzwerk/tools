import pdfplumber
import pdfminer
import os

class PDFDocument:
    def __init__(self, path=None, text=None, pages=None):
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
        self.pages = pages
        if path:
            self.fromfile()

    def fromfile(self, path=None):
        """
        Load PDF document from the given path.

        Args:
            path (str): Path to the PDF document.
        """
        if path is None:
            path = self.path
        else:
            self.path = path
        if not path:
            print("need path to load PDFDocument")
            return None
        # use a PDF parser to extract the text content of each page
        with open(path, 'rb') as f:
            parser = PDFParser(f)
            doc = PDFDocument(parser)
            parser.set_document(doc)
            doc.initialize()
            # check if the PDF is searchable (i.e. not an image-based PDF)
            if not doc.is_extractable:
                print("PDF is not searchable")
                return None
            # extract the text content of each page
            pages = []
            for page in doc.get_pages():
                interpreter = PDFPageInterpreter(parser, page)
                text = ''
                for obj in interpreter:
                    if isinstance(obj, LTTextBox):
                        text += obj.get_text().strip() + '\n'
                pages.append(text)
            self.pages = pages
            self.text = '\n'.join(pages)

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

# def get(filename, filepath):
#     if not filename.endswith(".pdf"):
#         filename += ".pdf"
#     with pdfplumber.open(os.path.join(filepath, filename)) as pdf:
#         # first_page = pdf.pages[0]
#         # print(first_page.chars[0])
#         text_pages = []
#         for page_id, page in enumerate(pdf.pages):
#             if page_id < 3:
#                 text_pages.append(page.extract_text())
#             else:
#                 left = page.crop((0, 0.4 * float(page.height), 0.5 * float(page.width), 0.9 * float(page.height)))
#                 right = page.crop((0.5 * float(page.width), 0.4 * float(page.height), page.width, 0.9 * float(page.height)))
#                 text_pages.append(left.extract_text())

#                 Extract text from the right half.
#                 right.extract_text()
#     return text_pages

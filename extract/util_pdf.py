import pdfplumber
import os


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

import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

from extract import util_whisper
from extract.nlp import util_nlp
from publish.Obsidian import nlped_whispered_folder

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
# test = "C:/Users/TimWittenborg/workspace/data"

query = [
    {"folder": "D:/workspace/Zotero/SE2A-B4-2",
     "language": "en"},
    # {"folder": "D:/workspace/raw (MP3)/Weltverbesserer",
    #  "image": "D:/workspace/raw (MP3)/Weltverbesserer/mask/49faa272-1663-44cb-ae49-6c7a7356cc12 - Kopie - Kopie.jpg",
    #  "language": "de"},
    # {"folder": "D:/workspace/raw (MP3)/HoP",
    #  "image": "D:/workspace/raw (MP3)/HoP/mask/ab67656300005f1fcabcff3dcfa8fbd5f5b0fa04.jpeg",
    #  "language": "en"},
]


# Extract
## Transcribe (Whisper)
nlptools = util_nlp.NLPTools()
for do in query:
    old_stdout = sys.stdout
    # todo: make this clearer
    if "mp3" in do["folder"].lower():
        util_whisper.extract_info(do["folder"])
    if "zotero" in do["folder"].lower():
        pass
        # todo: make this productive

    sys.stdout = old_stdout
    ## NLP (Flair and SpaCy)
    folder = util_nlp.Folder(
        do["folder"], nlptools=nlptools, language=do["language"])

    # Obsidian
    nlped_whispered_folder.folder(folder, force=True)


# paths = [
#     "D:/workspace/Zotero/SE2A-B4-2/00_PDFs/allaire_mathematical_2014/Allaire und Willcox - 2014 - A MATHEMATICAL AND COMPUTATIONAL FRAMEWORK FOR MUL.pdf",
#     "D:/workspace/Zotero/SE2A-B4-2/00_PDFs/ahmed_multifidelity_2020/Ahmed et al. - 2020 - Multifidelity Surrogate Assisted Rapid Design of T.pdf"
# ]
# docs = []
# for path in paths:
#     docs.append(PDFDocument(path))
# a = 1

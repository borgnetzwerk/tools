import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

from publish.Obsidian import nlped_whispered_folder
from extract.nlp import util_nlp
from extract import util_whisper

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
# test = "C:/Users/TimWittenborg/workspace/data"

query = [
    {"folder": "D:/workspace/raw (MP3)/Weltverbesserer",
     "image": "D:/workspace/raw (MP3)/Weltverbesserer/mask/49faa272-1663-44cb-ae49-6c7a7356cc12 - Kopie - Kopie.jpg",
     "language": "de"},
    # {"folder": "D:/workspace/raw (MP3)/HoP",
    #  "image": "D:/workspace/raw (MP3)/HoP/mask/ab67656300005f1fcabcff3dcfa8fbd5f5b0fa04.jpeg",
    #  "language": "en"},
]


# Extract
## Transcribe (Whisper)
nlptools = util_nlp.NLPTools()
for do in query:
    old_stdout = sys.stdout
    #todo: make this clearer
    util_whisper.extract_info(do["folder"])
    sys.stdout = old_stdout
    ## NLP (Flair and SpaCy)
    folder = util_nlp.Folder(do["folder"], nlptools=nlptools, language=do["language"])

    # Obsidian
    nlped_whispered_folder.folder(folder, force=True)

import yaml
import os
import sys
import importlib


bnw_tools_spec = importlib.util.find_spec('bnw_tools')

if bnw_tools_spec is None:
    sys.path.append(os.getcwd())
    import bnw_tools

from bnw_tools.publish import util_wordcloud
from bnw_tools.publish.Obsidian import nlped_whispered_folder
from bnw_tools.extract.nlp import util_nlp
from bnw_tools.extract import util_whisper

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
# test = "C:/Users/TimWittenborg/workspace/data"

query = [
    {"folder": "D:/workspace/raw (MP3)/Weltverbesserer",
     "image": "D:/workspace/raw (MP3)/Weltverbesserer/mask/49faa272-1663-44cb-ae49-6c7a7356cc12 - Kopie - Kopie.jpg",
     "language": "de"},
    {"folder": "D:/workspace/raw (MP3)/HoP",
     "image": "D:/workspace/raw (MP3)/HoP/mask/ab67656300005f1fcabcff3dcfa8fbd5f5b0fa04.jpeg",
     "language": "en"},
]


# Extract
## Transcribe (Whisper)
nlptools = util_nlp.NLPTools()
for do in query:

    util_whisper.extract_info(do["folder"])

    ## NLP (Flair and SpaCy)
    folder = util_nlp.Folder(do["folder"], nlptools=nlptools, language=do["language"])

    # Publish

    # Wordcloud
    util_wordcloud.generate_wordcloud(
        folder.bag_of_words.get(), os.path.join(do["folder"], "00_bag_of_words"))
    util_wordcloud.generate_wordcloud(
        folder.named_entities.get_frequencies(), os.path.join(do["folder"], "00_named_entities"))
    mask = util_wordcloud.generate_mask(do["image"])
    util_wordcloud.generate_wordcloud_mask(
        folder.bag_of_words.get(), mask, os.path.join(do["folder"], "00_bag_of_words_mask"))
    util_wordcloud.generate_wordcloud_mask(folder.named_entities.get_frequencies(
    ), mask, os.path.join(do["folder"], "00_named_entities_mask"))

    # Obsidian
    nlped_whispered_folder.folder(do["folder"], force=True)

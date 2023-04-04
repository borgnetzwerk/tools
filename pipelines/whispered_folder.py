import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

from extract import util_whisper
from extract.nlp import util_nlp
from publish.Obsidian import nlped_whispered_folder
from publish import util_wordcloud

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
# test = "C:/Users/TimWittenborg/workspace/data"
test = "D:/workspace/raw (MP3)/Weltverbesserer"
# image = "D:/workspace/data/masks/49faa272-1663-44cb-ae49-6c7a7356cc12 - Kopie.jpg"
image = "D:/workspace/raw (MP3)/Weltverbesserer/mask/49faa272-1663-44cb-ae49-6c7a7356cc12 - Kopie - Kopie.jpg"

# Extract
## Transcribe (Whisper)
util_whisper.extract_info(test)

## NLP (Flair and SpaCy)
folder = util_nlp.process_folder(test, language="de")

# Publish

# # Wordcloud
# util_wordcloud.generate_wordcloud(
#     folder.bag_of_words.get(), os.path.join(test, "00_bag_of_words"))
# util_wordcloud.generate_wordcloud(
#     folder.named_entities.get_frequencies(), os.path.join(test, "00_named_entities"))
# mask = util_wordcloud.generate_mask(image)
# util_wordcloud.generate_wordcloud_mask(
#     folder.bag_of_words.get(), mask, os.path.join(test, "00_bag_of_words_mask"))
# util_wordcloud.generate_wordcloud_mask(folder.named_entities.get_frequencies(
# ), mask, os.path.join(test, "00_named_entities_mask"))

# Obsidian
nlped_whispered_folder.folder(test, force=True)

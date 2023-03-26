import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

from extract.nlp import util_nlp
from publish.Obsidian import nlped_whispered_folder
from publish import util_wordcloud

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
test = "C:/Users/TimWittenborg/workspace/data"
image = "C:/Users/TimWittenborg/workspace/data/masks/ab67656300005f1fcabcff3dcfa8fbd5f5b0fa04.jpeg"
# util_nlp.process_folder("C:/Users/TimWittenborg/workspace/data")
folder = util_nlp.process_folder(test)
util_wordcloud.generate_wordcloud(folder.non_stop_words.get(), os.path.join(test, "00_non_stop_words"))
util_wordcloud.generate_wordcloud(folder.named_entities.get_frequencies(), os.path.join(test, "00_named_entities"))
mask = util_wordcloud.generate_mask(image)
util_wordcloud.generate_wordcloud_mask(folder.non_stop_words.get(), mask, os.path.join(test, "00_non_stop_words_mask"))
util_wordcloud.generate_wordcloud_mask(folder.named_entities.get_frequencies(), mask, os.path.join(test, "00_named_entities_mask"))
nlped_whispered_folder.folder(test)
import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

from extract.nlp import util_nlp
from publish.Obsidian import nlped_whispered_folder

# test = "C:/Users/TimWittenborg/workspace/test/whispered"
test = "C:/Users/TimWittenborg/workspace/data"
# util_nlp.process_folder("C:/Users/TimWittenborg/workspace/data")
util_nlp.process_folder(test)
nlped_whispered_folder.folder(test)

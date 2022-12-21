import helper

import re
import csv
import sys
import mediaWiki
import nlp
import json
import os
import time
import numpy
import difflib
import shutil
from pprint import pprint
from os import listdir
from os.path import isfile, join
from datetime import datetime
from os.path import exists
import os.path as path
from flair.data import Sentence
from flair.models import SequenceTagger

editfolder = 'edited'


def split_layers(string, characters=" ", keep_char=False, layer=0):
    if layer == len(characters):
        return [string]
    x = characters[layer]
    pieces = []
    if x in string:
        layer_pieces = string.split(x)
        for piece in layer_pieces:
            if piece == '':
                continue
            inner_results = split_layers(piece, characters, keep_char, 1+layer)
            if len(inner_results) == 0:
                continue
            for s in inner_results[:-1]:
                pieces.append(s)
            last_piece = inner_results[-1]
            if keep_char:
                last_piece += x
            pieces.append(last_piece)
    else:
        pieces = split_layers(string, characters, keep_char, 1+layer)
    return pieces


def wordify(string):
    candidates = split_layers(string, ' ,.!?\n')
    res = []
    for candidate in candidates:
        found = re.search(r'\D', candidate)
        if found != None:
            found = re.search(r'\w', candidate)
            if found != None:
                res.append(candidate)
    return res


def sentencify(string):
    return split_layers(string, '.!?', True)


def test(input_path, playlist_name, playlist_info, episodes_info, tagger):
    # make a sentence
    # sentence = Sentence('I love Berlin .')

    # run NER over sentence
    # tagger.predict(sentence)

    # print('The following NER tags are found:')

    # iterate over entities and print each
    # for entity in sentence.get_spans('ner'):
    #     print(entity)
    tokens = {}
    # TODO: Make sure input_path comes from the right place
    #
    # --- 1. Setup --- #
    # Log file
    # check what info is available

    # Read existing info
    playlist_info = {}
    episodes_info = {}

    # If major changes are made:

    edit_path = input_path + editfolder
    data_files, data_folders = helper.extract_file_folder(edit_path)

    jsons = []
    for filename in data_files:
        split_tup = os.path.splitext(edit_path + '\\' + filename)
        file_name = split_tup[0]
        file_extension = split_tup[1]
        if file_extension == '.json':
            jsons.append(filename)

    # Dictionary block:
    lexicon = {}
    lexicon_episode = {}
    lexicon_full = {}
    lexicon_ner = {}
    lexicon_ner_episode = {}
    lexicon_ner_full = {}

    with open(edit_path + '\\' + '_text.txt', "r", encoding="utf8") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        lexicon_episode = {}
        filename = jsons[idx]
        fileID = int(filename[:3])
        words = wordify(line)
        for word in words:
            helper.nested_add(lexicon_episode, [word], 1)
            helper.nested_add(lexicon_full, [word, fileID], 1)
        for key, value in lexicon_episode.items():
            helper.nested_add(lexicon, [key], value)
        if idx % 50 == 0 or idx == len(lines)-1:
            lexicon = dict(sorted(lexicon.items()))
            lexicon_full = dict(sorted(lexicon_full.items()))
            helper.dict2json(lexicon, '_lexicon', edit_path)
            helper.dict2json(lexicon_full, '_lexicon_full', edit_path)
            lexicon_ranked = {k: v for k, v in sorted(lexicon.items(), reverse=True, key=lambda item: item[1])}
            lexicon_full_ranked = sorted(lexicon_full_ranked, reverse=True, key=lambda k: len(lexicon_full_ranked[k]))
            helper.dict2json(lexicon_ranked, "_lexicon_ranked", edit_path)
            helper.dict2json(lexicon_full_ranked, "_lexicon_full_ranked", edit_path)

    for idx, line in enumerate(lines):
        lexicon_episode = {}
        filename = jsons[idx]
        fileID = int(filename[:3])
        print(filename + ':')
        sentences = sentencify(line)
        for s in sentences:
            sentence = Sentence(s)

            # run NER over sentence
            tagger.predict(sentence)

            # iterate over entities and print each
            sentence.get_token
            for entity in sentence.get_spans('ner'):
                text = entity.text
                helper.nested_add(lexicon_ner_episode, [text, fileID], 1)
                helper.nested_add(lexicon_ner_full, [
                                  text, fileID, entity.tag], [entity.score])
        for text, dict_var in lexicon_ner_episode.items():
            for fileID, value in dict_var.items():
                helper.nested_add(lexicon_ner, [text, fileID], value)
        if idx % 50 == 0 or idx == len(lines)-1:
            lexicon_ner = dict(sorted(lexicon_ner.items()))
            lexicon_ner_full = dict(sorted(lexicon_ner_full.items()))
            helper.dict2json(lexicon_ner, '_lexicon_ner', edit_path)
            helper.dict2json(lexicon_ner_full, '_lexicon_ner_full', edit_path)

        print('', flush=True)


def main(input_path=os.getcwd(), playlist_name='BMZ', playlist_info={}, episodes_info={}):
    if input_path[-1] != '\\':
        input_path += '\\'
    # print('vorher', flush=True)
    # # log_file = open("logfile_" + playlist_name + ".log", "w", encoding='utf8')
    # # sys.stdout = log_file
    # print('nachher', flush=True)
    # load the NER tagger
    tagger = SequenceTagger.load('ner-multi-fast')
    test(input_path, playlist_name, playlist_info, episodes_info, tagger)


if __name__ == '__main__':
    main()

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
import spacy
from pprint import pprint
from os import listdir
from os.path import isfile, join
from datetime import datetime
from os.path import exists
import os.path as path
from flair.data import Sentence
from flair.models import SequenceTagger

editfolder = 'edited'


def test(input_path, playlist_name, playlist_info, episodes_info, tagger, nlp):
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
    lexicon_episodes = {}
    lexicon_ep_count = {}
    lexicon_ner = {}
    lexicon_ner_episode = {}
    lexicon_ner_full = {}

    with open(edit_path + '\\' + '_text.txt', "r", encoding="utf8") as f:
        lines = f.readlines()

    do_words = True
    # do_words = False
    if do_words:
        for idx, line in enumerate(lines):
            lexicon_episode = {}
            filename = jsons[idx]
            fileID = int(filename[:3])
            words = helper.wordify(line)
            for word in words:
                helper.nested_add(lexicon_episode, [word], 1)
                helper.nested_add(lexicon_ep_count, [word, fileID], 1)
            for key, value in lexicon_episode.items():
                helper.nested_add(lexicon, [key], value)
            helper.nested_add(lexicon_episodes, [fileID], sorted(
                lexicon_episode.items(), reverse=True, key=lambda item: item[1]))
            print(str(len(words)) + ' words in ' + filename, flush=True)
            # if idx % 50 == 0 or idx == len(lines)-1:
            if idx == len(lines)-1:
                lexicon = dict(sorted(lexicon.items()))
                helper.dict2json(lexicon, '_lexicon_alphabetical', edit_path)
                lexicon = {k: v for k, v in sorted(
                    lexicon.items(), reverse=True, key=lambda item: item[1])}
                helper.dict2json(lexicon,
                                 "_lexicon", edit_path)
                lexicon_ep_count = sorted(
                    lexicon_ep_count.items(), reverse=True, key=lambda k: len(lexicon_ep_count[k]))
                helper.dict2json(lexicon_ep_count,
                                 "_lexicon_ep_count", edit_path)

    else:
        helper.json2dict(lexicon, "_lexicon", edit_path)

    if nlp:
        do_lemma = True
    else:
        do_lemma = False
    if do_lemma:
        lemmacon = helper.lemmatize(lexicon, nlp)
        lemmacon = {k: v for k, v in sorted(
            lemmacon.items(), reverse=True, key=lambda item: sum(list(item[1].values())))}
        helper.dict2json(lemmacon,
                         "_lemmacon", edit_path)
    # Stemming
    # https://medium.com/@tusharsri/nlp-a-quick-guide-to-stemming-60f1ca5db49e
    # Cutting words down till the same for alle declinations remains
    # Lemmatization
    # Link
    # Wir können von allen wörter auf das gleiche kern-wort mappen
    # https://github.com/wartaal/HanTa
    # https://pypi.org/project/spacy/
    # https://stackoverflow.com/questions/57857240/ho-to-do-lemmatization-on-german-text

    do_sim = True
    # do_sim = False
    if do_sim:
        lexicon_similar = {}
        upper_range = 2000
        max = len(lexicon)/2
        counter = 0
        for idx, word in enumerate(lexicon):
            for idy, comp in enumerate(lexicon):
                if idy <= idx:
                    continue
                if idy > max:
                    break
                are_sim = helper.similar(word, comp)
                if are_sim:
                    if word in lexicon_similar:
                        lexicon_similar[word] += [comp]
                    else:
                        lexicon_similar[word] = [comp]
            # if upper_range + 1 < max:
            #     upper_range+=1
            if idx % 10 == 0:
                print(str(counter) + ' words checked.')
                counter += 10
                helper.dict2json(
                    lexicon_similar, "_lexicon_similar", edit_path)

    if tagger:
        do_ner = True
    else:
        do_ner = False
    if do_ner:
        for idx, line in enumerate(lines):
            lexicon_ner_episode = {}
            filename = jsons[idx]
            fileID = int(filename[:3])
            print(filename + ':')
            sentences = helper.sentencify(line)
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
                helper.dict2json(lexicon_ner_full,
                                 '_lexicon_ner_full', edit_path)

            print('', flush=True)


def main(input_path=os.getcwd(), playlist_name='BMZ', playlist_info={}, episodes_info={}):
    if input_path[-1] != '\\':
        input_path += '\\'
    # print('vorher', flush=True)
    # # log_file = open("logfile_" + playlist_name + ".log", "w", encoding='utf8')
    # # sys.stdout = log_file
    # print('nachher', flush=True)
    # load the NER tagger
    tagger = False
    nlp = False
    # tagger = SequenceTagger.load('ner-multi-fast')
    # nlp = spacy.load('de_core_news_md')
    test(input_path, playlist_name, playlist_info, episodes_info, tagger, nlp)


if __name__ == '__main__':
    main()

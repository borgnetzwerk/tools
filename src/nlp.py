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


def sentencify(string):
    sentences = []
    for x in '.!?':
        if x in string:
            pieces = string.split(x)
            for piece in pieces:
                if piece == '':
                    continue
                inner_sentences = sentencify(piece)
                if len(inner_sentences) > 0:
                    for s in inner_sentences[:-1]:
                        sentences.append(s)
                    last_piece = inner_sentences[-1] + x
                    sentences.append(last_piece)
                else:
                    sentences.append(piece + x)
    return sentences
            

def test(input_path, playlist_name, playlist_info, episodes_info):
    # make a sentence
    sentence = Sentence('I love Berlin .')

    # load the NER tagger
    tagger = SequenceTagger.load('ner')

    # run NER over sentence
    tagger.predict(sentence)

    print('The following NER tags are found:')

    # iterate over entities and print each
    for entity in sentence.get_spans('ner'):
        print(entity)
        tokens = {}
        with open(input_path + 'text.txt', "r", encoding="utf8") as f:
            lines = f.readlines()
        for line in lines:
            sentences = sentencify(line)
            for s in sentences:
                sentence = Sentence(s)

                # run NER over sentence
                tagger.predict(sentence)

                # iterate over entities and print each
                for entity in sentence.get_spans('ner'):
                    print(entity)


def main(input_path=os.getcwd(), playlist_name='BMZ', playlist_info={}, episodes_info={}):
    # load the NER tagger
    tagger = SequenceTagger.load('ner')
    test(input_path, playlist_name, playlist_info, episodes_info)


if __name__ == '__main__':
    main()

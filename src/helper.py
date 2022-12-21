import json
import difflib
import re
import os
import spacy
from os import listdir
from os.path import isfile, join

similar_enough = 0.9


def similar(seq1, seq2, level=similar_enough):
    return difflib.SequenceMatcher(a=seq1.lower(), b=seq2.lower()).ratio() > similar_enough


def extract_file_folder(input_path):
    data_all = [f for f in listdir(input_path)]
    data_files = []
    data_folders = []
    for elm in data_all:
        if isfile(join(input_path, elm)):
            data_files.append(elm)
        else:
            data_folders.append(elm)
    return data_files, data_folders

def json2dict(name, path=os.getcwd()):
    json_pos = name.find(".json")
    if json_pos != len(name)-5:
        name += '.json'
    if path[-2:] != "\\":
        path += "\\"
    with open(path + name, encoding='utf-8') as json_file:
        dict_var = json.load(json_file)
    # return temp
        # dict_var = temp
    return dict_var


def lemmatize(string, nlp):
    # this might change the reslts
    doc = nlp(string)
    result = [x.lemma_.lower() for x in doc if re.search(r'\b[\w]+(?<!\d)-*\w*\b', x.lemma_)]
    return result


def dict2json(dict_var, name, path=os.getcwd()):
    json_pos = name.find(".json")
    if json_pos != len(name)-5:
        name += '.json'
    if path[-2:] != "\\":
        path += "\\"
    json_object = json.dumps(dict_var, indent=4, ensure_ascii=False)
    with open(path + name, "w", encoding='utf8') as outfile:
        outfile.write(json_object)

# dict stuff:
# https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys


def nested_set(dic, keys, value):
    for key in keys[:-1]:
        if key in dic and dic[key] == None:
            dic[key] = {}
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def nested_add(dic, keys, value):
    for key in keys[:-1]:
        if key in dic and dic[key] == None:
            dic[key] = {}
        dic = dic.setdefault(key, {})
    if keys[-1] in dic:
        dic[keys[-1]] += value
    else:
        dic[keys[-1]] = value


def nested_get(dic, keys):
    for key in keys:
        dic = dic[key]
    return dic


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
    regex = r'\b[\w]+(?<!\d)-*\w*\b'
    res = [x.lower() for x in re.findall(regex, string)]
    return res


def sentencify(string):
    return split_layers(string, '.!?', True)
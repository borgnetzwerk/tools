import os
import json
from os import listdir
from os.path import isfile, join


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


def dict2json(dict_var, name, path=os.getcwd()):
    json_pos = name.find(".json")
    if json_pos != len(name)-5:
        name += '.json'
    json_object = json.dumps(dict_var, indent=4, ensure_ascii=False)
    if path[-2:] != "//":
        path += "//"
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

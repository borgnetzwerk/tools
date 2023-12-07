import yaml
import os
import sys

# todo: make this import cleaner
sys.path.append(os.getcwd())

import core.helper as helper
import publish.graphvizify as graphvizify

MAX_LINKS = 5
MIN_IMPORTANCE = 5
MAX_CHAR_LEN_NAME = 100

tg = {}
helper.json2dict(tg, "transitions_grouped", "data\ignore")


def super_clean_title(title):
    clean_title = title.replace("/","[SLASH]")
    clean_title = helper.get_clean_title(clean_title, obsidian=True)
    clean_title = clean_title.replace("[SLASH]","/")
    if clean_title.startswith("https"):
        clean_title = clean_title[5:]
    while clean_title.startswith("/"):
        clean_title = clean_title[1:]
    if clean_title.startswith("www."):
        clean_title = clean_title[4:]
    while clean_title.endswith("/"):
        clean_title = clean_title[:-1]
    return clean_title

nodes = []
edges = []

node_ID_dict = {}
nID_counter = 0

def get_nID(text):
    global nID_counter
    if text in node_ID_dict:
        return node_ID_dict[text]
    else:
        node_ID_dict[text] = nID_counter
        nID_counter += 1
        return node_ID_dict[text]

for key, value in tg.items():
    clean_title = super_clean_title(key)
    if len(clean_title) > MAX_CHAR_LEN_NAME:
        continue
    Obs_path = "H:/Meine Ablage/Viz_Obsidian/actions"
    note = ""
    counter = 0
    sum = value['sum']
    note += "sum"
    for action, weight in value['actions'].items():
        if len(action) > MAX_CHAR_LEN_NAME:
            continue
        traffic = round(sum*weight)
        if action != key and traffic > MIN_IMPORTANCE:
            target = super_clean_title(action)
            if target not in node_ID_dict:
                nodes.append([get_nID(target), target])
            edges.append([get_nID(clean_title), get_nID(target), traffic])
            note += f"[[{target}]]:: {weight}\n"

            counter += 1
            # if counter == MAX_LINKS:
            #     break
    if counter == 0:
        continue
    else:
        nodes.append([get_nID(clean_title), clean_title])
    filepath = Obs_path + "/" + clean_title + ".md"
    pieces = clean_title.split("/")
    if len(pieces)>1:

        os.makedirs(filepath.rsplit("/",1)[0], exist_ok=True)
        a = 1
    try:
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(note)
    except Exception as e:
        print(e)

graphvizify.generate_dot_file(nodes, edges, "actions", Obs_path.replace("/actions", "/graph"), image_format = "png")
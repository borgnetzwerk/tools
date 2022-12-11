import re
import csv
import sys
import mediaWiki
import json
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime
# ---- Functions ---- #

# Add digits until cap is reached
def fill_digits(var_s, cap = 2):
    while len(var_s) < cap:
        var_s = "0" + var_s
    return var_s

# Convert extracted time to readable time
def time_converter(var_s):
    if "Std." in var_s or "Min." in var_s or "Sek." in var_s:
        # Time: HH:MM:SS
        m = re.search('\d*(?= *Std.)', var_s)
        std = "" if m is None else m.group(0)
        time = fill_digits(std) + ":"
        m = re.search('\d*(?= *Min.)', var_s)
        min = "" if m is None else m.group(0)
        time += fill_digits(min) + ":"
        m = re.search('\d*(?= *Sek.)', var_s)
        sek = "" if m is None else m.group(0)
        time += fill_digits(sek)
        return time
    else:
        # Date: YYYY-MM-DD
        list = var_s.split(' ')
        day = ""
        month = list[0]
        year = list[1]
        # See if first entry is really a month
        just_once = 1
        while just_once == 1:
            if month == 'Jan.':
                month = '01'
            elif month == 'Feb.':
                month = '02'
            elif month == 'März':
                month = '03'
            elif month == 'Apr.':
                month = '04'
            elif month == 'Mai':
                month = '05'
            elif month == 'Juni':
                month = '06'
            elif month == 'Juli':
                month = '07'
            elif month == 'Aug.':
                month = '08'
            elif month == 'Sept.':
                month = '09'
            elif month == 'Okt.':
                month = '10'
            elif month == 'Nov.':
                month = '11'
            elif month == 'Dez.':
                month = '12'
            else:
                # If first entry is not a month: 
                #   redo check with second entry
                #   and assume year is current year
                just_once += 1
                year = str(datetime.now().year)
                month = list[1]
                day = str(list[0].replace(".",""))
                day = "-" + fill_digits(day)
            just_once -= 1
        # reminder: day is either "" or "-DD"
        return year + '-' + month + day 

# Remove leading and closing quotation marks
def remove_quot(var_s):
    if var_s:
        if var_s[0] == '"':
            var_s = var_s[1:]
        if var_s[-1] == '"':
            var_s = var_s[:-1]
    return var_s

# Cut a string at the first hypen
def cut_hypen(var_s):
    var_s = var_s.split(" -", 1)[0]
    var_s = var_s.split("-", 1)[0]
    var_s = remove_quot(var_s)
    return var_s

# Cut a string at predetermined marks
def cut_out(var_s, dict):
    storage = {}
    for key, value in dict.items():
        temp = var_s.split(value, 1)
        if len(temp) > 1:
            storage[key] = temp[1]
            var_s = temp[0]
        else:
            storage[key] = temp[0]
    del storage["final_destination"]
    if "void" in storage:
        del storage["void"]
    return storage

# Sort a dict according to a list.
# reminder: items not in the list won't be transferred.
def sort_dict(dict, order_list):
    temp = {}
    for k in order_list:
        if k in dict:
            temp[k] = dict[k]
    return temp

def sort_episodes(episodes):
    first = int(episodes[0]['date'].split('-',1)[0])
    # reminder: we cannot fine-sort every entry, since the date is not stored precisely
    lid = len(episodes)-1
    second = int(episodes[lid]['date'].split('-',1)[0])
    if second > first:
        return episodes
    else:
        temp = {}
        for idx, k in enumerate(reversed(list(episodes.keys()))):
            temp[idx] = episodes[k]
        return temp

# Prepare dict so it can be used for MediaWiki
def clean_dict(dict, playlist_name):
    temp = {}
    for k in dict:
        dict[k] = remove_quot(dict[k])
        if k == 'id':
            temp[k] = dict[k]
        elif k == 'date':
            dict[k] = time_converter(dict[k])
            temp[k] = dict[k]
        elif k == 'runtime':
            dict[k] = time_converter(dict[k])
            temp[k] = dict[k]
        elif k == 'name':
            temp[k] = dict[k]
        elif k == 'title':
            if 'Zwanzig Jahre zu sp' in dict[k]:
                a=1
            dict[k] = dict[k].replace('[','(')
            dict[k] = dict[k].replace(']',')')
            fulltitle = '[[' + playlist_name + ':'
            fulltitle += dict[k] + '|' + dict[k] + ']]'
            temp[k] = fulltitle
        elif k == 'description':
            temp[k] = dict[k]
        elif k == 'author':
            temp2 = cut_out(dict[k], dict_author)
            temp['author_type'] = remove_quot(temp2['author_type'])
            temp['author_name'] = remove_quot(temp2['author_name'])
        elif k == 'publisher':
            temp[k] = dict[k]
        elif k == 'language':
            temp[k] = dict[k]
        elif k == '@type':
            temp[k] = dict[k]
        elif k == 'accessMode':
            temp[k] = dict[k]
        elif k == 'url':
            temp[k] = '[' + dict[k] + ' Spotify]'
        elif k == 'image':
            temp[k] = '[' + dict[k] + ' image]'
        else:
            temp[k] = dict[k]
    return temp

# convert from Spotify index to dictionary
def Spotify2dict(index, input_path, filename, playlist_name):
    # Cut in between episode and playlist info
    split_index = index.split("alt=")

    # extract playlist info
    playlist_info = cut_out(split_index[0], dict_playlist)

    # remove unneeded rows
    split_index.pop(0)
    split_index.pop(0)

    # cutting out "neue Folge"
    episodes =  {}
    for idx, episode in enumerate(split_index):
        sub = episode.split("Neue Folge\"></span>")
        if len(sub) > 1:
            episode = sub[1]
        episode_info = cut_out(episode, dict_episode)
        episode_info["description"] = episode_info["description"].split("Werbung:", 1)[0]
        episodes[idx] = episode_info
    # m = re.search('(?<=episodeTitle">).+?(?=<\/div>)', index)
    # m.group(0)

    # TODO: Ideen
    # replace_dict benötigt ausnahme für Links
    # Werbung raus
    # Link
    # Nummer
    # add language and other data to episodes (can we do this? from podcast alone? redundand? what about changes?)
    # ID
    # Convert to Wiki page
    # Sortable
    # Kategorie
    # Struktur 
    # URL von neue Folgeklappt noch nicht

    # ---- Clean ---- #
    # sort_dict(playlist_info, key_order)
    playlist_info = clean_dict(playlist_info, playlist_name)
    for key, value in episodes.items():
        episodes[key] = clean_dict(value, playlist_name)

    # ---- Sort ---- #
    # sort_dict(playlist_info, key_order)
    playlist_info = sort_dict(playlist_info, key_order)
    for key, value in episodes.items():
        episodes[key] = sort_dict(value, key_order)
    episodes = sort_episodes(episodes)
    return playlist_info, episodes

# convert from youtube index to dictionary
def YouTube2dict(index, input_path, filename, playlist_name):
    return {}, {}

# convert from dictionary to json
def dict2json(playlist_info, episodes, input_path, filename, playlist_name):
    # Serializing json
    json_object = json.dumps(playlist_info, indent=4)
    
    # Writing to sample.json
    with open(input_path + "playlist_info.json", "w", encoding='utf8') as outfile:
        outfile.write(json_object)
    json_object = json.dumps(episodes, indent=4)
    with open(input_path + "episodes.json", "w", encoding='utf8') as outfile:
        outfile.write(json_object)
    return

# convert from json to csv
def json2csv(playlist_info, episodes, input_path, filename, playlist_name):
    # ---- Write ---- #
    playlist_header = [] + list(playlist_info.keys())
    episode_header = ["#"] + list(episodes[0].keys())
    # output_path = input_path.replace('input','output')
    with open(input_path + 'playlist.csv', 'w', newline='', encoding='utf8') as f:  # You will need 'wb' mode in Python 2.x
        writer = csv.writer(f, delimiter =';')
        writer.writerow(playlist_header)
        values = []
        for key, value in playlist_info.items():
            values.append(value)
        writer.writerow(values)

    with open(input_path + 'episodes.csv', 'w', newline='', encoding='utf8') as f:  # You will need 'wb' mode in Python 2.x
        writer = csv.writer(f, delimiter =';')
        writer.writerow(episode_header)
        for key, value in episodes.items():
            values = [key+1]
            for ekey, evalue in value.items():
                values.append(evalue)
            writer.writerow(values)
    return

# convert from csv to wiki
def csv2wiki(playlist_info, episodes, input_path, filename, playlist_name):
    # Könnte man auch als Übersicht über alle podcast machen, die im Data.bnwiki sind
    ## Sortierbar nach Sprache etc.
    ## Kategorien ...
    mediaWiki.main(input_path)
    return

# convert from json to wiki
def json2wiki(playlist_info, episodes, input_path, filename, playlist_name):
    # Könnte man auch als Übersicht über alle podcast machen, die im Data.bnwiki sind
    ## Sortierbar nach Sprache etc.
    ## Kategorien ...
    mediaWiki.main(input_path)
    return

# handle the difference between all the different input sources
# Todo: for example: add missing episodes, missing links, titles, add different links per source, ...
def handle_diff(list_var):
    keys = []
    res = {}
    # todo: differentiate between nested dicts (episodes) and normal (playlist) 
    for element in list_var:
        keys += element.keys()
    for key in keys:
        # Todo: make a decision which to take
        for element in list_var:
            if key in element:
                res[key] = element[key]
    return res

# ---- Globals ---- #

# --- 1. general --- #
# Replacements to be done from HTML to readable text
replace_dict = {
    "&nbsp;"    :   "",
    "&lt;"      :   "<",
    "&gt;"      :   ">",
    "&amp;"     :   "&",
    "&euro;"     :   "€",
    "&pound;"     :   "£",
    "&quot;"     :   "“",
    "&apos;"     :   "‘",
    "\\u00FC"   :   "ü"
    # TODO: further äö and others should be added
}

# --- 2. specific --- #
# order keys should be read in (for sort_dict function)
key_order = (
    'id',
    'date',
    'runtime',
    'name',
    'title',
    'description',
    'author_type',
    'author_name',
    'publisher',
    'language',
    '@type',
    'accessMode',
    'url',
    'image'
)

# Dict with episode keys to be found and values as extraction markers (for cut_out function)
dict_episode = {
    "final_destination" : "</span></p></div></div>",
    "runtime"   :   '</p><p class="Type__TypeElement-sc-goli3j-0 hGXzYa _q93agegdE655O5zPz6l"><span class="UyzJidwrGk3awngSGIwv">',
    "date"  :   '</div><div class="qfYkuLpETFW3axnfMntO"><p class="Type__TypeElement-sc-goli3j-0 hGXzYa _q93agegdE655O5zPz6l">',
    "void"  :   '</p></div><div',
    "description" : "</div></a></div></div><div class=\"upo8sAflD1byxWObSkgn\"><p class=\"Type__TypeElement-sc-goli3j-0 hGXzYa LbePDApGej12_NyRphHu\">",
    "title"  :   '><div class="Type__TypeElement-sc-goli3j-0 kUtbWF bG5fSAAS6rRL8xxU5iyG" data-testid="episodeTitle\">',
    "url"  :   'href='
}

# Dict with playlist keys to be found and values as extraction markers (for cut_out function)
dict_playlist = {
    "final_destination" : "}</script><link rel=",
    "language"  :   ',"inLanguage":',
    "accessMode"  :   ',"accessMode":',
    "image"  :   ',"image":',
    "author"  :   ',"author":',
    "publisher"  :   ',"publisher":',
    "description"  :   ',"description":',
    "name"  :   ',"name":',
    "url"  :   ',"url":',
    "@type"  :   ',"@type":'
}

# Author_name and _type is nested in author, so they have to be extracted as well (for cut_out function)
dict_author = {
    "final_destination" : "}",
    'author_name' : ',"name":',
    'author_type' : '{"@type":'
}

# ---- Main ---- #

def extract_info(input_path, playlist_name):
    # --- 1. Setup --- #
    # Log file
    old_stdout = sys.stdout
    log_file = open("logfile.log","w")
    sys.stdout = log_file

    # check what info is available
    data_all = [f for f in listdir(input_path)]
    data_files = []
    data_folders = []
    for elm in data_all:
        if isfile(join(input_path, elm)):
            data_files.append(elm)
        else:
            data_folders.append(elm)

    # Read existing info
    playlist_info = {}
    if 'playlist_info.json' in data_files:
        with open(input_path + 'playlist_info.json') as json_file:
            playlist_info = json.load(json_file)

    episodes_info = {}
    if 'episodes_info.json' in data_files:
        with open(input_path + 'episodes_info.json') as json_file:
            episodes_info = json.load(json_file)

    for filename in data_files:
        if filename.split('.')[-1] == 'html':
            HTMLFile = open(input_path + filename, "r", encoding="utf8")
            index = HTMLFile.read()
            # convert from HTML to readable text
            # TODO: Make exceptions for elements within links !
            for key in replace_dict:
                index = index.replace(key, replace_dict[key])
            # handle different sources
            if filename == "YouTube.html":
                pass
                playlist_info_YT, episodes_info_YT = YouTube2dict(index, input_path, filename, playlist_name)
            elif filename == "Spotify.html":
                playlist_info_SF, episodes_info_SF = Spotify2dict(index, input_path, filename, playlist_name)
    
    tempList = [playlist_info]
    if 'YouTube.html' in data_files:
        tempList.append(playlist_info_YT)
    if 'Spotify.html' in data_files:
        tempList.append(playlist_info_SF)
    playlist_info = handle_diff(tempList)

    tempList = [episodes_info]
    if 'YouTube.html' in data_files:
        tempList.append(episodes_info_YT)
    if 'Spotify.html' in data_files:
        tempList.append(episodes_info_SF)
    episodes_info = handle_diff(tempList)
    del tempList

    # Read file
    dict2json(playlist_info, episodes_info, input_path, filename, playlist_name)
    
    json2csv(playlist_info, episodes_info, input_path, filename, playlist_name)

    csv2wiki(playlist_info, episodes_info, input_path, filename, playlist_name)

    sys.stdout = old_stdout
    log_file.close()

def main():
    my_path = os.getcwd()
    data_path = os.path.dirname(my_path) + '\\data\\'
    playlist_names = [f for f in listdir(data_path) if not isfile(join(data_path, f))]
    playlist_names.remove('sample')
    for pl_n in playlist_names:
        data_pl_path = data_path + pl_n + '\\'
        extract_info(data_pl_path, pl_n)

if __name__ == '__main__':
    main()
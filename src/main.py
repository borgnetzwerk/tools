import re
import csv
import sys
import mediaWiki
import json
import os
import time
import difflib
from pprint import pprint
from os import listdir
from os.path import isfile, join
from datetime import datetime
from os.path import exists

# Define
similar_enough = 0.9
audiofolder = 'mp3'
# If major changes have been made: Flush out these old ones
flush_out_relics = True

# ---- Functions ---- #

# Add digits until cap is reached


def fill_digits(var_s, cap=2):
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
                day = str(list[0].replace(".", ""))
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
        canidate = ""
        if len(temp) > 1:
            var_s = temp[0]
            canidate = temp[1]
        else:
            canidate = temp[0]
        if 'void' not in canidate and len(canidate) > 0:
            storage[key] = canidate
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
    first = int(episodes[0]['date'].split('-', 1)[0])
    # reminder: we cannot fine-sort every entry, since the date is not stored precisely
    lid = len(episodes)-1
    second = int(episodes[lid]['date'].split('-', 1)[0])
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
            temp[k] = dict[k]
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
            temp[k] = dict[k]
        elif k == 'image':
            temp[k] = dict[k]
        else:
            temp[k] = dict[k]
    return temp


def wikify_dict(dict, playlist_name):
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
            dict[k] = dict[k].replace('[', '(')
            dict[k] = dict[k].replace(']', ')')
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
    episodes = {}
    for idx, episode in enumerate(split_index):
        sub = episode.split("Neue Folge\"></span>")
        if len(sub) > 1:
            episode = sub[1]
        episode_info = cut_out(episode, dict_episode)
        if 'description' in episode_info:
            episode_info["description"] = episode_info["description"].split("Werbung:", 1)[
                0]
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


def get_playlist_info_YT(var_str):
    temp = {}
    for key, value in dict_playlist_YT.items():
        if key == "make_boxes" or key == "box_begin":
            var_str = var_str.split(value, 1)[1]
        elif key == "box_end":
            var_str = var_str.split(value, 1)[0]
        else:
            group = var_str.split(value, 1)
            if 'void' not in group[0] and len(group[0]) > 0:
                temp[key] = group[0]
            var_str = group[1]
    return temp

# convert from youtube index to dictionary


def YouTube2dict(index, input_path, filename, playlist_name):
    boxes = index.split(dict_episode_YT['make_boxes'])
    episode_info_YT = {}
    playlist_info_YT = {}
    # Todo: Extract youtube Link to playlist
    for idx, box in enumerate(boxes):
        if idx == 0:
            playlist_info_YT = get_playlist_info_YT(box)
        box = box.split(dict_episode_YT['box_begin'])[-1]
        box = box.split(dict_episode_YT['box_end'])[0]
        episode = {}
        rest = box.split(dict_episode_YT['title'])
        if len(rest) > 1:
            episode['title'] = remove_quot(rest[1])
            episode['url'] = remove_quot(rest[0])
            episode_info_YT[idx] = episode
    return playlist_info_YT, episode_info_YT


def dict2json(dict_var, name, path=os.getcwd()):
    json_object = json.dumps(dict_var, indent=4)
    if path[-2:] != "//":
        path += "//"
    with open(path + name + ".json", "w", encoding='utf8') as outfile:
        outfile.write(json_object)

# convert from dictionary to json


def infos2json(playlist_info, episodes_info, input_path, filename, playlist_name):
    # Serializing json
    dict2json(playlist_info, "playlist_info", input_path)
    dict2json(episodes_info, "episodes_info", input_path)
    return

# convert from json to csv


def json2csv(playlist_info, episodes, input_path, filename, playlist_name):
    # ---- Write ---- #
    playlist_header = [] + list(playlist_info.keys())
    episode_header = ["#"] + list(episodes[0].keys())
    # output_path = input_path.replace('input','output')
    # You will need 'wb' mode in Python 2.x
    with open(input_path + 'playlist.csv', 'w', newline='', encoding='ANSI') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(playlist_header)
        values = []
        for key, value in playlist_info.items():
            values.append(value)
        writer.writerow(values)

    # You will need 'wb' mode in Python 2.x
    with open(input_path + 'episodes.csv', 'w', newline='', encoding='ANSI') as f:
        writer = csv.writer(f, delimiter=';')
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
    # Sortierbar nach Sprache etc.
    # Kategorien ...
    mediaWiki.main(input_path)
    return

# convert from json to wiki


def json2wiki(playlist_info, episodes, input_path, filename, playlist_name):
    # Könnte man auch als Übersicht über alle podcast machen, die im Data.bnwiki sind
    # Sortierbar nach Sprache etc.
    # Kategorien ...
    # mediaWiki.main(input_path)
    return


title_structure = {
    'BMZ':   {
        'playlist_name':   [r'(^B+MZ)', 0],
        'void1':   [r'([- ]{0,3})', 0],
        'special':   [r'(\w*[- ]{0,3})', 0.1],
        'void2':   [r'([ # ]{0,3})', 0],
        'eID':   [r'(\d*)', 1],
        'void3':   [r'([: ,]{0,2})', 0],
        'title':   [r'(.*)', 1]
    },
    'Hagrids Hütte':   {
        'eID':   [r'(^[\d\w]{1}\.[\d]{2})', 1],
        'void1':   [r'[- ]{0,3}\w*[- ]{0,3}', 0],
        'title':   [r'.*', 1]
    }
}


def title_mine(title, playlist_name):
    temp = {}
    splits = title_structure[playlist_name]
    for split in splits:
        sep = splits[split][0]
        found = re.split(sep, title, 1)
        if len(found) > 2:
            if 'void' not in split and len(found[1]) > 0:
                temp[split] = found[1]
                # temp[split] = str(found[1])
            title = found[2]
    return temp


def similar(seq1, seq2, level=similar_enough):
    return difflib.SequenceMatcher(a=seq1.lower(), b=seq2.lower()).ratio() > similar_enough


def compare_titles(try_this, comp, playlist_name):
    similarity_score = 0
    for struc in try_this:
        if struc in try_this and struc in comp:
            if comp[struc] == try_this[struc]:
                similarity_score += title_structure[playlist_name][struc][1]
                # We have found the matching episode and it has the ID idx
    return similarity_score


def search_for_title(try_this, episodes_infos, playlist_name):
    for idx, eID in enumerate(episodes_infos):
        comp = title_mine(episodes_infos[eID]['title'], playlist_name)
        is_match = compare_titles(try_this, comp, playlist_name)
        if is_match >= 1:
            return idx
        # if 'try_pl_name' in try_this and 'try_pl_name' in comp:   Playlists should always be the same
    # Currently limited to only compare longer titles, otherwise may be unprecise
    #! Very time expensive
    # if len(title.lower()) > 10:
    #     for idx, eID in enumerate(episodes_infos):
    #         comp = title_mine(episodes_infos[eID]['title'])
    #         sim = similar(title, episodes_infos[eID]['title'])
    #         if sim:
    #             return idx
    return -1

# handle the difference between all the different input sources
# Todo: for example: add missing episodes, missing links, titles, add different links per source, ...


def handle_diff_ep(list_var, playlist_name):
    for element in list_var:
        if not element:
            list_var.remove(element)
    longest = 0
    for idx, element in enumerate(list_var):
        if len(element) > len(list_var[longest]):
            longest = idx
    specials = 0
    # Step 1:
    # run through this once and allign every possible title
    # possible results:
    # fID >= 0
    #       wir haben ein Match gefunden und es ist an der Stelle fID
    # nachher prüfen, ob alle fIDs verwendet wurden ->
    #       sonst haben die kürzeren eine folge, die die längere nicht hat
    #       Dann die nachbarn checken und herausfinden, wo diese Folge in longest eingefügt werden muss
    # fID == -1
    #       wir haben kein Match gefunden
    #           diese folge existiert nur in longest

    # Phase 1: alle plID ausprobieren
    #       Ergebnis:
    # input: playlist_ID, eID, specials
    # output: fID

    # Phase 2: alle playlist_ID_shorter prüfen, die keine fID haben
    # input: fID, shorter_playlist
    # output: missing_pl_id = [prior_neighbor, later_neighbor]

    #
    # Wenn eID Sprung macht, aber kein Special dabei war: ring a bell
    #
    order = [0] * len(list_var[longest])
    matched = []
    for episode_infos in list_var:
        matched_counters = []
        for each in episode_infos:
            matched_counters.append([])
        matched.append(matched_counters)
    # print('order:')
    last_eID = 0
    for plID, episode in list_var[longest].items():
        # TODO: find out why suddenly read as string -> saved in dict -> find out why
        plID = int(plID)
        title = episode['title']
        try_this = title_mine(title, playlist_name)
        try_this['plID'] = str(plID)
        # try_this['plID'] = plID
        # if the ID is missing from the main Episode
        if 'eID' in try_this:
            try:
                last_eID = int(try_this['eID'])
            except:
                last_eID += 1
        elif 'special' not in try_this:
            last_eID += 1
            try_this['eID'] = str(last_eID)
            # try_this['eID'] = str(plID+1)
            # try_this['eID'] = plID+1
        findings = [plID]
        for listID, element in enumerate(list_var):
            if listID != longest:
                # Make new dicts and resort them here
                fID = search_for_title(
                    try_this, list_var[listID], playlist_name)
                if fID >= 0:
                    matched[listID][fID].append(plID)
                findings.append(fID)
        order[plID] = findings
        # print('\t' + ',\t'.join(str(e) for e in findings), flush=True)
        title = episode['title']

    # handle Miss-Matches

    multi_match = []
    # Case 1: Multi-matches
    print('Case 1: Multi-matches:')
    for idx, element in enumerate(list_var):
        if idx != longest:
            for fID, episode in enumerate(element):
                if len(matched[idx][fID]) > 1:
                    entry = {
                        'listID':   idx,
                        'eID':   fID,
                        'matches':   matched[idx][fID]
                    }
                    multi_match.append(entry)
                    print(list_var[idx][fID]['title'])
                    print('[' + str(idx) + '][' + str(fID) + ']\t' + str(len(matched[idx][fID])) +
                          ' matches:\t' + ',\t'.join(str(e) for e in matched[idx][fID]), flush=True)
                    for id in matched[idx][fID]:
                        print('\t\t\t\t' + list_var[longest][id]['title'])

    zero_match = []
    # Case 2: 0-Matches
    print('Case 2: 0-Matches:')
    for idx, element in enumerate(list_var):
        if idx != longest:
            for fID, episode in enumerate(element):
                if len(matched[idx][fID]) == 0:
                    entry = {
                        'title':   list_var[idx][fID]['title'],
                        'listID':   idx,
                        'eID':   fID,
                        'matches':   matched[idx][fID],
                    }
                    zero_match.append(entry)
                    print(entry['title'])
                    print('[' + str(idx) + '][' + str(fID) + ']\t' + str(len(matched[idx][fID])) +
                          ' matches:\t' + ',\t'.join(str(e) for e in matched[idx][fID]), flush=True)
    # TODO: Remove short term fix

    # Case 1: Duplicate Upload:
    # Status: Working!
    deletes = []
    for idx, missing_match in enumerate(zero_match):
        # look if repetition:
        eID = missing_match['eID']
        listID = missing_match['listID']
        title = missing_match['title']
        try_this = title_mine(title, playlist_name)
        clone_score = compare_titles(try_this, try_this, playlist_name)
        for idy in range(1, 3+1):
            try:
                comp = title_mine(
                    list_var[listID][eID-idy]['title'], playlist_name)
                score = compare_titles(try_this, comp, playlist_name)
                if score == clone_score:
                    print('[' + str(listID) + '][' + str(eID) + ']' +
                          ' is a copy of [' + str(listID) + '][' + str(eID-idy) + ']', flush=True)
                    deletes.append(idx)
                    break
            except:
                pass
    for x in reversed(deletes):
        del zero_match[x]

    # Case 2: Ment for zero_match:
    # Status: Working!
    deletes = []
    for mmID, entry in enumerate(multi_match):
        delete_here = []
        # entry eID from list listID has to many matches from list longest, namely matches
        listID = entry['listID']
        eID = entry['eID']
        ep_prev = list_var[listID][eID-1]['title']
        episode = list_var[listID][eID]['title']
        ep_next = list_var[listID][eID+1]['title']
        episode_triple = [ep_prev, episode, ep_next]
        matched_ep_titles = []
        for match in entry['matches']:
            matched_ep_prev = list_var[longest][match-1]['title']
            matched_episode = list_var[longest][match]['title']
            matched_ep_next = list_var[longest][match+1]['title']
            matched_ep_titles.append(
                [matched_ep_prev, matched_episode, matched_ep_next])
        # Case 1:
        match_score_list = []
        for matched_triple in matched_ep_titles:
            score = 0
            for x in range(0, 3):
                try_this = title_mine(episode_triple[x], playlist_name)
                comp = title_mine(matched_triple[x], playlist_name)
                score += compare_titles(try_this, comp, playlist_name)
            match_score_list.append(score)
        hightest = 0
        for score in match_score_list:
            if score > hightest:
                hightest = score
        for match_ID, score in enumerate(match_score_list):
            if score != hightest:
                main_eID = entry['matches'][match_ID]
                for idy, missing_match in enumerate(zero_match):
                    if missing_match['title'] != matched_ep_titles[match_ID][1]:
                        continue
                    if zero_match[idy]['listID'] != listID:
                        continue
                    pot_eID = zero_match[idy]['eID']
                    pot_ep_prev = list_var[listID][pot_eID-1]['title']
                    pot_episode = list_var[listID][pot_eID]['title']
                    pot_ep_next = list_var[listID][pot_eID+1]['title']
                    pot_title = [pot_ep_prev, pot_episode, pot_ep_next]
                    score = 0
                    for x in range(0, 3):
                        try_this = title_mine(pot_title[x], playlist_name)
                        comp = title_mine(
                            matched_ep_titles[match_ID][x], playlist_name)
                        score += compare_titles(try_this, comp, playlist_name)
                    if score >= 2:
                        # update order (!most important)
                        order[main_eID][listID] = pot_eID
                        # update matched (optional, for better overview)
                        matched[listID][pot_eID].append(main_eID)
                        del zero_match[idy]
                        # mark for update here
                        delete_here.append(match_ID)
                        print('[' + str(listID) + '][' + str(pot_eID) + ']' + ' is matched to [' + str(
                            main_eID) + '] instead of [' + str(listID) + '][' + str(eID) + ']', flush=True)
                        break
        for x in reversed(delete_here):
            del entry['matches'][x]
        if len(entry['matches']) == 1:
            deletes.append(mmID)
    for x in reversed(deletes):
        del multi_match[x]

    # Case 3: Completely missplaced duplicates
    deletes = []
    for idx, missing_match in enumerate(zero_match):
        # look if repetition:
        eID = missing_match['eID']
        listID = missing_match['listID']
        title = missing_match['title']
        try_this = title_mine(title, playlist_name)
        clone_score = compare_titles(try_this, try_this, playlist_name)
        for exID in list_var[listID]:
            if exID != eID:
                episode = list_var[listID][exID]
                comp = title_mine(episode['title'], playlist_name)
                score = compare_titles(try_this, comp, playlist_name)
                if score == clone_score:
                    print('[' + str(listID) + '][' + str(eID) + ']' +
                          ' is a copy of [' + str(listID) + '][' + str(exID) + ']', flush=True)
                    # This is way to time consumative, but at this point: just tell the spotify / whatever person to delete the duplicate.
                    # lookaround: which fits better:
                    # Done: Option to delete the existing one and place this one in its place:
                    # eg 0 1 2 3 4 50 5 6 7 8 .. 48 49 50 51
                    # currently first 50 would be kept
                    # fixed

                    # Check around existing
                    start_ID = exID
                    error_existing = 0
                    pre_c = min([3, min([exID, int(eID)])])
                    post_c = min([3, len(list_var[listID]) +
                                 1 - max([exID, int(eID)])])
                    for pre in range(1, pre_c+1):
                        check2 = title_mine(
                            list_var[listID][start_ID-pre]['title'], playlist_name)
                        error_existing += (int(comp['eID']) +
                                           pre) - int(check2['eID'])
                    for post in range(1, post_c+1):
                        check2 = title_mine(
                            list_var[listID][start_ID+post]['title'], playlist_name)
                        error_existing += int(check2['eID']) - \
                            (int(comp['eID']) + post)

                    # Check around missing
                    start_ID = int(eID)
                    error_missing = 0
                    # previous: 3
                    for pre in range(1, pre_c+1):
                        check2 = title_mine(
                            list_var[listID][start_ID-pre]['title'], playlist_name)
                        error_existing += (int(try_this['eID']) +
                                           pre) - int(check2['eID'])
                    # following: 3
                    for post in range(1, post_c+1):
                        check2 = title_mine(
                            list_var[listID][start_ID+post]['title'], playlist_name)
                        error_existing += int(check2['eID']) - \
                            (int(try_this['eID']) + post)
                    if error_existing > error_missing:
                        # existing was the faulty duplicate
                        # matched[]
                        print('[' + str(listID) + '][' + str(exID) + ']' +
                              'may be seriously missplaced. It\'s copy is better suited and will be kept.')
                        existing_matches = matched[listID][exID]
                        if len(existing_matches) != 1:
                            print(
                                'unresolvable error at multi_match  [' + str(listID) + '][' + str(exID) + ']')
                        order[existing_matches[0]][listID] = eID
                        matched[listID][eID] = existing_matches
                        matched[listID][exID] = []
                    deletes.append(idx)

                    break
    for x in reversed(deletes):
        del zero_match[x]

    # Case 4: Newcomer -> die wollen wir behalten
    deletes = []
    inserted = 0
    for idx, missing_match in enumerate(zero_match):
        # Check if they had the missing one
        eID = int(missing_match['eID'])
        listID = missing_match['listID']
        title = missing_match['title']
        try_this = title_mine(title, playlist_name)

        # previous episode
        prev_match = int(matched[listID][eID-1][0])
        prev_ep = list_var[listID][eID-1]
        prev_ep_title = prev_ep['title']
        prev_split = title_mine(prev_ep_title, playlist_name)
        if 'eID' in prev_split:
            prev_mined_ID = int(prev_split['eID'])

        # next episode
        next_match = int(matched[listID][eID+1][0])
        next_ep = list_var[listID][eID+1]
        next_ep_title = next_ep['title']
        next_split = title_mine(next_ep_title, playlist_name)
        if 'eID' in next_split:
            next_mined_ID = int(next_split['eID'])

        this_is_it = False
        # Todo: handle exception if no ['eID'] in prev_split or next_split
        if prev_mined_ID + 1 < next_mined_ID:
            this_is_it = True
        elif int(eID) == prev_mined_ID + 1:
            this_is_it = True
        elif int(eID) == next_mined_ID - 1:
            this_is_it = True

        if this_is_it:
            position = int(prev_match) + 1 + inserted

        # See if thing has matches
        findings = [-1]
        cur_LID = listID
        for listID, element in enumerate(list_var):
            if listID != longest or listID == cur_LID:
                fID = search_for_title(
                    try_this, list_var[listID], playlist_name)
                if fID >= 0:
                    matched[listID][fID].append(plID)
                findings.append(fID)
        order.insert(position, findings)
        deletes.append(idx)
        inserted += 1
        print('[' + str(cur_LID) + '][' + str(eID) +
              '] has been inserted at order[' + str(position) + '].')

    for x in reversed(deletes):
        del zero_match[x]

    dict2json(order, "order")
    dict2json(matched, "matched")
    for idx, episode_infos in enumerate(list_var):
        dict2json(list_var[idx], "episode_infos_" + str(idx))
    dict2json(zero_match, "zero_match")
    dict2json(multi_match, "multi_match")

    # for row in order:
    #     print('\t' + ',\t'.join(str(e) for e in row))

    # TODO: Sort according to order
    episode_info = {}
    for main_ID, element in enumerate(order):
        temp_episode = {}
        episode_info_parts = []
        for listID, id_in_list in enumerate(element):
            if id_in_list >= 0:
                episode_info_parts.append(list_var[listID][id_in_list])
        episode = handle_diff(episode_info_parts)
        episode_info[main_ID] = episode
    return episode_info

def handle_diff(pieces):
    unified = {}
    used = []
    for key in key_order:
        candidates = []
        for main_ID, element in enumerate(pieces):
            if key in element:
                candidates.append(element[key])
        if len(candidates) > 0:
            used.append(key)
            if len(candidates) == 1:
                unified[key] = candidates[0]

            elif key == 'url':
                # TODO: Handle Spotify+Youtube URL
                Spotify = False
                YouTube = False
                # flush out multi-entries
                temp = []
                for candidate in candidates:
                    temp_list = candidate.split(' ; ')
                    for e in temp_list:
                        temp.append(e)
                candidates = temp
                winners = []
                for candidate in candidates:
                    if "spotify.com" in candidate:
                        if not Spotify:
                            Spotify = True
                            winners.append(candidate)
                    elif "youtube.com" in candidate:
                        if not YouTube:
                            YouTube = True
                            winners.append(candidate)
                    else:
                        winners.append(candidate)
                winner = ' ; '.join(winners)
                unified[key] = winner
            else:
                winner = ""
                print(
                    str(main_ID) + ':\t' + '\tor\t'.join(str(e) for e in candidates), flush=True)
                # just pick the longest
                for candidate in candidates:
                    if len(candidate) > len(winner):
                        winner = candidate
                unified[key] = winner

    for main_ID, element in enumerate(pieces):
        unused = []
        for key in element:
            if key not in used:
                unused.append(key)
        if len(unused) > 0:
            print('unused: ' ', '.join(unused), flush=True)
    return unified


# ---- Globals ---- #


# --- 1. general --- #
# Replacements to be done from HTML to readable text
replace_dict = {
    "&nbsp;":   "",
    "&lt;":   "<",
    "&gt;":   ">",
    "&amp;":   "&",
    "&euro;":   "€",
    "&pound;":   "£",
    "&quot;":   "“",
    "&apos;":   "‘",
    "\\u00FC":   "ü",
    # TODO: further äö and others should be added
    # https://www.cl.cam.ac.uk/~mgk25/ucs/quotes.html
    "”":    '"',
    "“":    '"',
    "&#39;": "'",
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
    'author_url',
    'publisher',
    'language',
    '@type',
    'accessMode',
    'url',
    'image'
)

dict_playlist_YT = {
    "make_boxes":   '</yt-formatted-string></h3><div id="publisher-container" class="style-scope ytd-playlist-panel-renderer"><yt-formatted-string class="byline-title style-scope ytd-playlist-panel-renderer complex-string" ellipsis-truncate="" hidden="" ellipsis-truncate-styling="" title="',
    "box_begin":   'omplex-string" ellipsis-truncate="" hidden="" ellipsis-truncate-styling="" title="',
    "box_end":   '</a></yt-formatted-string><div class="index-message-wrapper style-scope ytd-playlist-panel-renderer"><span class="index-message style-scope ytd-playlist-panel-renderer" hidden="">',
    "title":   '" has-link-only_=""><a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href="',
    "url":   '" dir="auto">',
    "void":   '</a></yt-formatted-string><ytd-badge-supported-renderer class="style-scope ytd-playlist-panel-renderer" disable-upgrade="" hidden=""></ytd-badge-supported-renderer><yt-formatted-string class="publisher style-scope ytd-playlist-panel-renderer complex-string" ellipsis-truncate="" link-inherit-color="" ellipsis-truncate-styling="" title="',
    "author_name":   '" has-link-only_=""><a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href="',
    "author_url":   '" dir="auto">',
}

dict_episode_YT = {
    "make_boxes": '<ytd-video-meta-block class="playlist',
    "box_begin":   '<a id="video-title" class="yt-simple-endpoint style-scope ytd-playlist-video-renderer" href=',
    "box_end":   '">\n',
    "title":   ' title=',
    "url":   ''
}

# Dict with episode keys to be found and values as extraction markers (for cut_out function)
dict_episode = {
    "final_destination_void": "</span></p></div></div>",
    "runtime":   '</p><p class="Type__TypeElement-sc-goli3j-0 hGXzYa _q93agegdE655O5zPz6l"><span class="UyzJidwrGk3awngSGIwv">',
    "date":   '</div><div class="qfYkuLpETFW3axnfMntO"><p class="Type__TypeElement-sc-goli3j-0 hGXzYa _q93agegdE655O5zPz6l">',
    "void":   '</p></div><div',
    "description": "</div></a></div></div><div class=\"upo8sAflD1byxWObSkgn\"><p class=\"Type__TypeElement-sc-goli3j-0 hGXzYa LbePDApGej12_NyRphHu\">",
    "title":   '><div class="Type__TypeElement-sc-goli3j-0 kUtbWF bG5fSAAS6rRL8xxU5iyG" data-testid="episodeTitle\">',
    "url":   'href='
}

# Dict with playlist keys to be found and values as extraction markers (for cut_out function)
dict_playlist = {
    "final_destination_void": "}</script><link rel=",
    "language":   ',"inLanguage":',
    "accessMode":   ',"accessMode":',
    "image":   ',"image":',
    "author":   ',"author":',
    "publisher":   ',"publisher":',
    "description":   ',"description":',
    "title":   ',"name":',
    "url":   ',"url":',
    "@type":   ',"@type":'
}

# Author_name and _type is nested in author, so they have to be extracted as well (for cut_out function)
dict_author = {
    "final_destination_void": "}",
    'author_name': ',"name":',
    'author_type': '{"@type":'
}

# ---- Main ---- #


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


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def clean_filenames():
    #! not foolproof yet
    return
    # for filename in data_files_audio:
    #     clean_name = re.sub('-[-\d\w]{11}.', '.', filename)
    #     path_old = input_path + '\\' + foldername + '\\' + filename
    #     path_new = input_path + '\\' + foldername + '\\' + clean_name
    #     if filename != clean_name:
    #         file_exists = exists(path_new)
    #         counter = 1
    #         while file_exists:
    #             split_tup = os.path.splitext(path_new)
    #             file_name = split_tup[0]
    #             file_extension = split_tup[1]
    #             if counter >1:
    #                 file_name = rreplace(file_name,' #' + str(counter), '', 1)
    #             counter += 1
    #             path_new = file_name + " #" + str(counter) + file_extension
    #             file_exists = exists(path_new)
    #         os.rename(path_old, path_new)


def extract_info(input_path, playlist_name):
    # --- 1. Setup --- #
    # Log file
    old_stdout = sys.stdout
    log_file = open("logfile.log", "w", encoding='utf8')
    sys.stdout = log_file

    # check what info is available
    data_files, data_folders = extract_file_folder(input_path)

    # Read existing info
    playlist_info = {}
    episodes_info = {}

    # If major changes are made:
    if not flush_out_relics:
        if 'playlist_info.json' in data_files:
            with open(input_path + 'playlist_info.json') as json_file:
                playlist_info = json.load(json_file)
                # Todo: if an "old replacement" 
                # index = index.replace(key, replace_dict[key])
        if 'episodes_info.json' in data_files:
            with open(input_path + 'episodes_info.json') as json_file:
                episodes_info = json.load(json_file)
                # index = index.replace(key, replace_dict[key])
                episodes_info = {int(k): v for k, v in episodes_info.items()}

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
                playlist_info_YT, episodes_info_YT = YouTube2dict(
                    index, input_path, filename, playlist_name)
            elif filename == "Spotify.html":
                playlist_info_SF, episodes_info_SF = Spotify2dict(
                    index, input_path, filename, playlist_name)

    for foldername in data_folders:
        if foldername == audiofolder:
            data_files_audio, data_folders_audio = extract_file_folder(
                input_path + '\\' + foldername)
            # clean_filenames(data_files_audio)

    tempList = [playlist_info]
    if 'YouTube.html' in data_files:
        dict2json(playlist_info_YT, "playlist_info_YT", input_path)
        tempList.append(playlist_info_YT)
    if 'Spotify.html' in data_files:
        dict2json(playlist_info_SF, "playlist_info_YT", input_path)
        tempList.append(playlist_info_SF)
    playlist_info = handle_diff(tempList)

    tempList = [episodes_info]
    if 'YouTube.html' in data_files:
        dict2json(episodes_info_YT, "episodes_info_YT", input_path)
        tempList.append(episodes_info_YT)
    if 'Spotify.html' in data_files:
        dict2json(episodes_info_SF, "episodes_info_SF", input_path)
        tempList.append(episodes_info_SF)
    episodes_info = handle_diff_ep(tempList, playlist_name)
    del tempList

    # Read file
    infos2json(playlist_info, episodes_info,
               input_path, filename, playlist_name)

    json2csv(playlist_info, episodes_info, input_path, filename, playlist_name)

    csv2wiki(playlist_info, episodes_info, input_path, filename, playlist_name)

    sys.stdout = old_stdout
    log_file.close()


def main():
    my_path = os.getcwd()
    data_path = os.path.dirname(my_path) + '\\data\\'
    playlist_names = [f for f in listdir(
        data_path) if not isfile(join(data_path, f))]
    playlist_names.remove('sample')
    for pl_n in playlist_names:
        data_pl_path = data_path + pl_n + '\\'
        extract_info(data_pl_path, pl_n)


if __name__ == '__main__':
    main()

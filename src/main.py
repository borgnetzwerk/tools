import helper
import obsidize

import re
import csv
import sys
import mediaWiki
import nlp
import json
import os
import time
import numpy
import shutil
from pprint import PrettyPrinter
from os import listdir
from os.path import isfile, join
from os.path import exists
import os.path as path
import spellcheck.main as s_check
# Define
audiofolder = helper.audiofolder
tokenfolder = helper.tokenfolder
editfolder = helper.editfolder
# If major changes have been made: Flush out these old ones
flush_out_relics = True

# ---- Functions ---- #


# Convert extracted time to readable time


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


def texify(var_s, k):
    if k == 'url':
        tokens = var_s.split(' ; ')
        winner = ""
        for t in tokens:
            url_var = helper.get_brand(t)
            winner += ' \href{' + t + \
                '}{\includegraphics[height=11pt]{gfx/' + url_var + '.png}}'
        var_s = winner
    return var_s


# convert from Spotify index to dictionary


def Spotify2dict(index, input_path, filename, playlist_name):
    # Cut in between episode and playlist info
    split_index = index.split("alt=")

    # extract playlist info
    playlist_info = helper.cut_out(split_index[0], dict_playlist)

    # remove unneeded rows
    split_index.pop(0)
    split_index.pop(0)

    # cutting out "neue Folge"
    episodes = {}
    for idx, episode in enumerate(split_index):
        sub = episode.split("Neue Folge\"></span>")
        if len(sub) > 1:
            episode = sub[1]
        episode_info = helper.cut_out(episode, dict_episode)
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
    playlist_info = helper.clean_dict(playlist_info, playlist_name)
    for key, value in episodes.items():
        episodes[key] = helper.clean_dict(value, playlist_name)

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
            episode['title'] = helper.remove_quot(rest[1])
            episode['url'] = helper.remove_quot(rest[0])
            episode_info_YT[idx] = episode
    return playlist_info_YT, episode_info_YT


# convert from dictionary to json


def infos2json(playlist_info, episodes_info, input_path, filename, playlist_name):
    # Serializing json
    helper.dict2json(playlist_info, "playlist_info", input_path)
    helper.dict2json(episodes_info, "episodes_info", input_path)
    return

# convert from json to csv


def json2csv(playlist_info, episodes, input_path, playlist_name):
    # ---- Write ---- #
    playlist_header = [] + list(playlist_info.keys())
    episode_header = ["#"] + list(episodes[0].keys())
    # TODO: make sure to catch all, if first hasnt got all
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
                actual_key = len(values)
                while ekey != episode_header[actual_key]:
                    values.append('')
                    actual_key += 1
                values.append(evalue)
            writer.writerow(values)
    return


def search_for_title(try_this, episodes_info, playlist_name):
    for idx, eID in enumerate(episodes_info):
        comp = helper.title_mine(episodes_info[eID]['title'], playlist_name)
        is_match = helper.compare_titles(try_this, comp, playlist_name)
        if is_match >= 1:
            return idx
        # if 'try_pl_name' in try_this and 'try_pl_name' in comp:   Playlists should always be the same
    # Currently limited to only compare longer titles, otherwise may be unprecise
    #! Very time expensive
    # if len(title.lower()) > 10:
    #     for idx, eID in enumerate(episodes_info):
    #         comp = helper.title_mine(episodes_info[eID]['title'])
    #         sim = helper.similar(title, episodes_info[eID]['title'])
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
        try_this = helper.title_mine(title, playlist_name)
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
        try_this = helper.title_mine(title, playlist_name)
        clone_score = helper.compare_titles(try_this, try_this, playlist_name)
        for idy in range(1, 3+1):
            try:
                comp = helper.title_mine(
                    list_var[listID][eID-idy]['title'], playlist_name)
                score = helper.compare_titles(try_this, comp, playlist_name)
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
                try_this = helper.title_mine(episode_triple[x], playlist_name)
                comp = helper.title_mine(matched_triple[x], playlist_name)
                score += helper.compare_titles(try_this, comp, playlist_name)
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
                        try_this = helper.title_mine(
                            pot_title[x], playlist_name)
                        comp = helper.title_mine(
                            matched_ep_titles[match_ID][x], playlist_name)
                        score += helper.compare_titles(try_this,
                                                       comp, playlist_name)
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
        try_this = helper.title_mine(title, playlist_name)
        clone_score = helper.compare_titles(try_this, try_this, playlist_name)
        for exID in list_var[listID]:
            if exID != eID:
                episode = list_var[listID][exID]
                comp = helper.title_mine(episode['title'], playlist_name)
                score = helper.compare_titles(try_this, comp, playlist_name)
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
                        check2 = helper.title_mine(
                            list_var[listID][start_ID-pre]['title'], playlist_name)
                        error_existing += (int(comp['eID']) +
                                           pre) - int(check2['eID'])
                    for post in range(1, post_c+1):
                        check2 = helper.title_mine(
                            list_var[listID][start_ID+post]['title'], playlist_name)
                        error_existing += int(check2['eID']) - \
                            (int(comp['eID']) + post)

                    # Check around missing
                    start_ID = int(eID)
                    error_missing = 0
                    # previous: 3
                    for pre in range(1, pre_c+1):
                        check2 = helper.title_mine(
                            list_var[listID][start_ID-pre]['title'], playlist_name)
                        error_existing += (int(try_this['eID']) +
                                           pre) - int(check2['eID'])
                    # following: 3
                    for post in range(1, post_c+1):
                        check2 = helper.title_mine(
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
        try_this = helper.title_mine(title, playlist_name)

        # previous episode
        prev_match = int(matched[listID][eID-1][0])
        prev_ep = list_var[listID][eID-1]
        prev_ep_title = prev_ep['title']
        prev_split = helper.title_mine(prev_ep_title, playlist_name)
        if 'eID' in prev_split:
            prev_mined_ID = int(prev_split['eID'])

        # next episode
        next_match = int(matched[listID][eID+1][0])
        next_ep = list_var[listID][eID+1]
        next_ep_title = next_ep['title']
        next_split = helper.title_mine(next_ep_title, playlist_name)
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

    helper.dict2json(order, "order")
    helper.dict2json(matched, "matched")
    for idx, episode_infos in enumerate(list_var):
        helper.dict2json(list_var[idx], "episode_infos_" + str(idx))
    helper.dict2json(zero_match, "zero_match")
    helper.dict2json(multi_match, "multi_match")

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


# ---- Main ---- #


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


def show_newest_files(input_path, files):
    dates = []
    for file in files:
        date = os.path.getmtime(input_path+'\\'+file)
        dates.append(date)
    order = numpy.argsort(dates)
    files_sorted = []
    for position in reversed(order):
        files_sorted.append(files[position])
    return files_sorted


def extract_html_info(input_path, playlist_name, playlist_info, episodes_info):
    data_files, data_folders = helper.extract_file_folder(input_path)
    data_files = show_newest_files(input_path, data_files)
    for file in data_files:
        if ".html" in file:
            break
        if "episodes_info.json" == file:
            # We are up to date
            return

    # --- 1. Setup --- #
    # Log file

    # check what info is available

    # Read existing info

    # If major changes are made:
    if not flush_out_relics:
        playlist_info, episodes_info = helper.setup_infos(
            playlist_info, episodes_info, input_path)

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

    tempList = [playlist_info]
    if 'YouTube.html' in data_files:
        helper.dict2json(playlist_info_YT, "playlist_info_YT", input_path)
        tempList.append(playlist_info_YT)
    if 'Spotify.html' in data_files:
        helper.dict2json(playlist_info_SF, "playlist_info_SF", input_path)
        tempList.append(playlist_info_SF)
    if len(tempList) > 1:
        playlist_info = handle_diff(tempList)
    else:
        playlist_info = tempList[0]

    tempList = [episodes_info]
    if 'YouTube.html' in data_files:
        helper.dict2json(episodes_info_YT, "episodes_info_YT", input_path)
        tempList.append(episodes_info_YT)
    if 'Spotify.html' in data_files:
        helper.dict2json(episodes_info_SF, "episodes_info_SF", input_path)
        tempList.append(episodes_info_SF)

    if len(tempList) > 1:
        episodes_info = handle_diff_ep(tempList, playlist_name)
    else:
        episodes_info = tempList[0]
    del tempList

    # Read file
    infos2json(playlist_info, episodes_info,
               input_path, filename, playlist_name)

    return (playlist_info, episodes_info)


token_puncs = {
    '......':   r'(......)',
    '...':   r'(...$)',
    ',':   r'(,$)',
    '.':   r'((?<!\d)\.$)',
    '!':   r'(!$)',
    '?':   r'(\?$)',
}

token_puncs_ok = {
    '.':   r'\d\.$',
}


def split_punctuation(token):
    found = []
    for find, finder in token_puncs.items():
        if find in token:
            token_parts = re.split(finder, token, 1)
            for part in token_parts:
                if part == '':
                    continue
                if part == find:
                    found.append(part)
                if part == token:
                    continue
                else:
                    found += split_punctuation(part)
    if len(found) == 0:
        found = [token]
    return found


def dictify_tokens(token, token_text, var_int, var_dict):
    if token in var_dict:
        if token_text in var_dict[token]:
            if var_int in var_dict[token][token_text]:
                var_dict[token][token_text][var_int] += 1
            else:
                var_dict[token][token_text].update({var_int: 1})
        else:
            var_dict[token][token_text] = {var_int: 1}
    else:
        var_dict[token] = {token_text: {var_int: 1}}


def do_token_stuff(input_path, jsons):
    # phase 1: Addapt names
    detected_nothing = "detected_nothing!!!"
    detected_occurence = 'detected_occurence!!!'
    tokenpath = input_path + tokenfolder + '\\'

    token2string_dict = {}

    # Read in all the transcribts
    phase_2 = True
    if phase_2:
        # Todo: Build a Dict with { Token : Word or ,.!? }
        # Status: Currently on hold due to it Tokens not alligning 100% with words
        full_dict = {}
        wrong_dict = {}
        list_wrong_matches = []
        counter_match = 0
        counter_no_match = 0
        for filename in jsons:
            transcript = helper.get_transcript(input_path, filename)
            for segment in transcript['segments']:
                tokens = segment['tokens']
                text = segment['text']
                tokens_text = text.split()
                if len(tokens) != len(tokens_text):
                    better_tokens_text = []
                    for token in tokens_text:
                        temp = split_punctuation(token)
                        for x in temp:
                            better_tokens_text.append(x)
                    tokens_text = better_tokens_text
                if len(tokens) != len(tokens_text):
                    counter_no_match += 1
                    list_wrong_matches.append([tokens, tokens_text])
                else:
                    token_translation = {}
                    for idx, token in enumerate(tokens):
                        # dictify_tokens(token, tokens_text[idx], int(filename.split('_')[0]), token_translation)
                        dictify_tokens(token, tokens_text[idx], int(
                            filename.split('_')[0]), full_dict)
                    counter_match += 1
                # ['Hallo', 'und', 'herzlich', 'willkommen', 'hier', 'ist', 'Bardo', 'mit', 'einem', 'neuen', 'Video', 'zu', 'WoW', 'zu', ...]
                # ' Hallo und herzlich willkommen
                # [21242, 674, 45919, 46439,
                # hier ist Bardo mit
                # 3296, 1418, 363, 12850,
                # einem neuen Video zu
                # 2194, 6827, 21387, 9777,
                # WoW zu Legion heute'
                # 2164, 6622, 54 2164
                # ?? ??
                # 33024 9801
            if not os.path.exists(tokenpath):
                os.makedirs(tokenpath)
            # helper.dict2json(token_translation, filename.replace('.json', '') + "_tokens", tokenpath)

            print('Match rate: ' +
                  str(round(counter_match/counter_no_match, 2)), flush=True)
            # print('While ' + str(counter_match) + ' could be matched, ' + str(counter_no_match) + ' could not.', flush=True)
        for token in full_dict:
            if len(full_dict[token]) == 1:
                token2string_dict.update({token: list(full_dict[token])[0]})
        token2string_dict = dict(sorted(token2string_dict.items()))
        helper.dict2json(token2string_dict, "_token2string", tokenpath)
        helper.dict2json(full_dict, "_tokens", tokenpath)
        occurs_with = {}

        for tokens, tokens_text in list_wrong_matches:
            for token in tokens:
                if token in full_dict:
                    text = list(full_dict[token])[0]
                    if text in tokens_text:
                        tokens_text.remove(text)
                        tokens.remove(token)
            # print(',\t'.join(str(e) for e in tokens))
            # print(',\t'.join(str(e) for e in tokens_text), flush=True)
            while len(tokens) > len(tokens_text):
                tokens_text.append(detected_nothing)
            while len(tokens) < len(tokens_text):
                tokens.append(-1)
            for idx, token in enumerate(tokens):
                dictify_tokens(token, tokens_text[idx], int(
                    filename.split('_')[0]), wrong_dict)
                dictify_tokens(token, token, detected_occurence, occurs_with)
                for text in tokens_text:
                    dictify_tokens(token, token, text, occurs_with)
    else:
        with open(tokenpath + '_tokens_occurs_with.json', encoding='utf-8') as json_file:
            occurs_with = json.load(json_file)

    phase_3 = True
    if phase_3:
        # helper.dict2json(occurs_with, "_tokens_occurs_with", tokenpath)
        determined_tokens = {}
        progress_made = True
        while progress_made:
            progress_made = False
            blacklist = []
            occurs_with_filtered = {}
            # TODO: remove soon:
            for token in list(occurs_with):
                if detected_occurence in occurs_with[token][token]:
                    del occurs_with[token][token][detected_occurence]
                if detected_nothing in occurs_with[token][token]:
                    del occurs_with[token][token][detected_nothing]
                # make that work later on
                # if detected_occurence in occurs_with[token][token]:
                #     det_count = occurs_with[token][token][detected_occurence]
                # else:
                max_v = 0
                for key, value in occurs_with[token][token].items():
                    max_v = max(max_v, value)
                det_count = max_v
                occurs_with_filtered[token] = {}

                for text in occurs_with[token][token]:
                    fin_count = occurs_with[token][token][text]
                    if fin_count >= 0.5 * det_count:
                        occurs_with_filtered[token][text] = fin_count
                if len(occurs_with_filtered[token]) == 1:
                    text = list(occurs_with_filtered[token])[0]
                    determined_tokens[token] = text
                    blacklist.append([token, text])
                    progress_made = True
            for token, text in blacklist:
                if token in occurs_with:
                    del occurs_with[token]
                for token in list(occurs_with):
                    if text in occurs_with[token][token]:
                        del occurs_with[token][token][text]
            blacklist = []

        helper.dict2json(occurs_with_filtered,
                         "_tokens_occurs_with_filtered", tokenpath)
        helper.dict2json(determined_tokens, "_tokens_determined", tokenpath)

    phase_4 = True
    if phase_4:
        pass
    # helper.dict2json(occurs_with_filtered, "_tokens_occurs_with_filtered", tokenpath)
    # helper.dict2json(occurs_with, "_tokens_occurs_with", tokenpath)
    # helper.dict2json(wrong_dict, "_tokens_wrong", tokenpath)


spellcheck_dict = s_check.main_dict


def spellcheck_string(text, playlist_name):
    for dict_s in spellcheck_dict:
        if dict_s == 'regular':
            for x, y in spellcheck_dict[dict_s].items():
                try:
                    text = re.sub(x, y, text, flags=re.IGNORECASE)
                except:
                    text = text.replace(x, y)
        elif dict_s == playlist_name:
            for x, y in spellcheck_dict[dict_s].items():
                try:
                    text = re.sub(x, y, text, flags=re.IGNORECASE)
                except:
                    text = text.replace(x, y)
    return text


def spellcheck(input_path, playlist_name, jsons):
    edited_path = input_path + editfolder + '\\'
    with open(edited_path + "_text.txt", "w", encoding='utf8') as f:
        for filename in jsons:
            transcript = helper.get_transcript(input_path, filename)
            # temp = transcript['text']
            found = re.search(r'[^,.!\?]{2000}', transcript['text'])
            if found is not None:
                print('stuck in no-punctuation mode: ' + filename)
            # https://github.com/openai/whisper/discussions/194
            # TODO: redo translation or sth
            # Status: Yet to be fixed
            transcript['text'] = spellcheck_string(
                transcript['text'], playlist_name)
            # TODO: Improve segment checks if correction happens in text, but is split in segment:
            # Port Pala -> "... Pot", "Pala ..."
            for segment in transcript['segments']:
                segment['text'] = spellcheck_string(
                    segment['text'], playlist_name)
            # TODO: make a check if no need to write to file again
            f.write(transcript['text'] + '\n')

            if not os.path.exists(edited_path):
                os.makedirs(edited_path)

            helper.dict2json(transcript, filename, edited_path)


def add_transcript(input_path, playlist_name, playlist_info, episodes_info):
    # Phase 0: Setup
    data_files, data_folders = helper.extract_file_folder(input_path)
    data_files = show_newest_files(input_path, data_files)
    # --- 1. Setup --- #
    # Log file
    # check what info is available

    # Read existing info
    playlist_info = {}
    episodes_info = {}

    # If major changes are made:
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)

    if len(data_folders) == 0 or audiofolder not in data_folders:
        return

    for foldername in data_folders:
        if foldername == audiofolder:
            data_files_audio, data_folders_audio = helper.extract_file_folder(
                input_path + foldername + '\\')

    jsons = []
    audios = []

    for filename in data_files_audio:
        split_tup = os.path.splitext(input_path + foldername + '\\' + filename)
        file_name = split_tup[0]
        file_extension = split_tup[1]
        # TODO: if filename.endswith('.json'):
        if file_extension == '.json':
            jsons.append(filename)
        elif file_extension == '.mp3':
            audios.append(filename)
            # jsons.append(filename.replace('.mp3', '.json'))
        else:
            print(filename)
    # phase 1: Addapt names
    phase_1 = False
    if phase_1:
        # TODO: generalize this
        for filename in jsons:
            entry = filename[:4]
            if "BMZ" not in entry:
                continue
            title = filename.replace('.json', '')
            try_this = helper.title_mine(title, playlist_name)
            for idx, eID in enumerate(episodes_info):
                new_title = episodes_info[eID]['title']
                for each in helper.noFileChars:
                    new_title = new_title.replace(each, '')
                comp = helper.title_mine(new_title, playlist_name)
                is_match = helper.compare_titles(try_this, comp, playlist_name)
                matched = False
                if is_match >= 1:
                    matched = True
                else:
                    matched = helper.similar(title, new_title)
                if matched:
                    clean_name = helper.fill_digits(idx, 3) + '_' + new_title
                    path_old = input_path + audiofolder + '\\' + filename
                    path_new = input_path + audiofolder + '\\' + clean_name + '.json'
                    if exists(path_old):
                        if exists(path_new):
                            continue
                        os.rename(path_old, path_new)
                    filename = filename.replace('.json', '.mp3')
                    path_old = input_path + audiofolder + '\\' + filename
                    path_new = input_path + audiofolder + '\\' + clean_name + '.mp3'
                    if filename in audios:
                        if exists(path_old) and not exists(path_new):
                            if not exists(path_new):
                                os.rename(path_old, path_new)
    spellcheck(input_path, playlist_name, jsons)
    # do_token_stuff(input_path, jsons)
    # Todo: make every subsequential call look for transcripts in edited


def convert_to_wiki(input_path, playlist_name, playlist_info, episodes_info):
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)
    return mediaWiki.main(playlist_info, episodes_info, input_path, playlist_name)


tex_esc = {
    chr(92):   chr(92) + 'textbackslash',
    '^':   chr(92) + 'textasciicircum',
    '~':   chr(92) + 'textasciitilde',
    '&':   chr(92) + '&',
    '%':   chr(92) + '%',
    '$':   chr(92) + '$',
    '#':   chr(92) + '#',
    '_':   chr(92) + '_',
    '{':   chr(92) + '{',
    '}':   chr(92) + '}',
}


def latex_escape(title, skip=False):
    # https://tex.stackexchange.com/questions/34580/escape-character-in-latex
    for key, value in tex_esc.items():
        if key == '#' and skip:
            continue
        if key == '&' and skip:
            continue
        title = title.replace(key, value)
    return title


tex_title_esc = {
    '[':   '{[}',
    ']':   '{]}',
}


def latex_title_escape(title):
    for key, value in tex_title_esc.items():
        title = title.replace(key, value)
    return title


def add_acronyms(playlist_name, f):
    if playlist_name in s_check.acro:
        ac_dict = s_check.acro[playlist_name]
    else:
        return
    if len(ac_dict) == 0:
        return

    f.write('\\begin{acronym}[MMORPG]\n')
    for ac, entries in ac_dict.items():
        line = '\t\\acro{' + ac + '}[' + ac + ']{' + entries[0] + '}'
        f.write(line + '\n')
        if len(entries) > 1:
            line = '\t\\acrodefplural{' + ac + \
                '}[' + entries[1] + ']{' + entries[2] + '}'
            f.write(line + '\n')
    f.write('\\end{acronym}\n')


def texify_acronyms(text, playlist_name):
    if playlist_name in s_check.acro:
        ac_dict = s_check.acro[playlist_name]
    else:
        return text
    if len(ac_dict) == 0:
        return text

    for ac, entries in ac_dict.items():
        # Todo: find out why r'\b(?=\w)' might be used instead r'\b'
        ac_s = r'\b' + re.escape(ac) + r'\b'
        ac = r'\\ac{' + ac + '}'
        if len(entries) > 1:
            acp_s = r'\b' + re.escape(entries[1]) + r'\b'
            acp = r'\\ac{' + entries[1] + '}'
        else:
            acp_s = r'\b' + re.escape(ac) + r's\b'
            acp = r'\\ac{' + ac + 's}'
        text = re.sub(ac_s, ac, text, flags=re.IGNORECASE)
        text = re.sub(acp_s, acp, text, flags=re.IGNORECASE)
    return text


def convert_to_tex(input_path, playlist_name, playlist_info, episodes_info, wiki_episodes_info={}):
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)
    language = 'de'
    if 'language' in playlist_info:
        language = playlist_info['language']
    # https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
    two_up = path.abspath(path.join(input_path, ".."))
    tex_path_sample = two_up + '\\sample\\' + language + '\\LaTeX\\'
    tex_path = input_path + 'LaTeX\\'
    if not os.path.exists(tex_path):
        os.makedirs(tex_path)
    data_files, data_folders = helper.extract_file_folder(tex_path_sample)
    tex_filenames = []
    for filename in data_files:
        split_tup = os.path.splitext(tex_path_sample + filename)
        file_name = split_tup[0]
        file_extension = split_tup[1]
        if file_extension == '.tex':
            tex_filenames.append(filename)
    data_files = tex_filenames
    for filename in data_files:
        filename
        src = tex_path_sample + '\\' + filename
        dst = tex_path + '\\' + filename
        shutil.copyfile(src, dst)

    if 'raw' in data_folders:
        data_folders.remove('raw')
    for foldername in data_folders:
        if not os.path.exists(tex_path + '\\' + foldername):
            os.makedirs(tex_path + '\\' + foldername)

    # make changes according to podcast_info

    # Fill input
    index_lines = []
    author = ''
    if 'author_name' in playlist_info:
        author = playlist_info['author_name']
    for e_key in episodes_info:
        # min = 726
        # max = 726
        # # max = 999
        # if e_key < min:
        #     continue
        # if e_key > max:
        #     break
        episode = episodes_info[e_key]
        title = episode['title']
        clean_name, json_path = helper.clean_title(title, input_path, e_key)
        # reminder: Episodes that have no mp3 (i.E. Spotify exclusives) cannot be found
        if exists(json_path):
            with open(json_path, encoding='utf-8') as json_file:
                info = json.load(json_file)

            author_here = author
            # Todo: Make this read and differentiate the episodes author
            # Currently this is not even extracted from YouTube
            if 'author' in episode:
                author_here = episode['author']
            # YouTube and Spotify
            if 'url' in episode:
                # author_here += texify(episode['url'], 'url')
                # Wenn Icons dort sind, brauchen wir das "Onkel Barlow" vielleicht nicht
                urls = episode['url']
                if e_key in wiki_episodes_info:
                    if 'url_wiki' in wiki_episodes_info[e_key]:
                        url_wiki = wiki_episodes_info[e_key]['url_wiki'].replace(
                            '%', '\\%')
                        urls = url_wiki + ' ; ' + urls
                author_here = texify(urls, 'url')
            # Wiki
                # author_here += texify(episode['url'], 'url')
            title_forged = helper.forge_title(title, e_key, playlist_name)
            title_tex = latex_escape(title_forged)
            title_tex = latex_title_escape(title_tex)
            # No BMZ in title:
            # title_tex = re.sub(r'BMZ *:*', '', title_tex, 1)

            line = '\\newchapter{' + title_tex + '}{' + author_here + '}'
            # line = '\\newchapter{' + title_tex + '}{' + author_here + '}'
            index_lines.append(line)

            index_lines.append('\\acresetall')
            # Todo: find out why double space is a no-go
            clean_name_tex = latex_escape(clean_name, True).replace("  ", " ")

            line = '\\input{' + 'input/' + clean_name_tex + '.tex' + '}'
            index_lines.append(line)

            # Todo: find out why double space is a no-go
            tex_path_episode = tex_path + 'input\\' + \
                clean_name.replace("  ", " ") + '.tex'
            with open(tex_path_episode, "w", encoding='utf8') as f:
                text = latex_escape(info['text'])
                text = texify_acronyms(text, playlist_name)
                text = text.replace(' ', '\n')
                f.write(text)

            index_lines.append('\clearpage')
            # \newchapter{Story One}{Author One}

    if len(index_lines) > 0:
        # TODO: acronyms
        with open(tex_path + 'input\\index.tex', "w", encoding='utf8') as f:
            add_acronyms(playlist_name, f)
            line = '\part{' + playlist_name + '}'
            f.write(line + '\n')
            for line in index_lines:
                f.write(line + '\n')


def NLP(input_path, playlist_name, playlist_info, episodes_info):
    # print('vor NPL')
    nlp.main(input_path, playlist_name, playlist_info, episodes_info)
    # print('nach NPL')


def main():
    data_path, playlist_names = helper.get_data_folders()
    # for pl_n in playlist_names:
    for pl_n in playlist_names[:1]:
        old_stdout = sys.stdout
        log_file = open("logfile_" + pl_n + ".log", "w", encoding='utf8')
        sys.stdout = log_file

        data_pl_path = data_path + pl_n + '\\'
        playlist_info = {}
        episodes_info = {}
        # TODO: Find out why this doesnt work
        # playlist_info, episodes_info = extract_html_info(data_pl_path, pl_n)
        print('extract_html_info', flush=True)
        extract_html_info(data_pl_path, pl_n, playlist_info, episodes_info)
        print('add_transcript')
        add_transcript(data_pl_path, pl_n, playlist_info, episodes_info)
        # wiki_episodes_info = convert_to_wiki(data_pl_path, pl_n, playlist_info, episodes_info)
        # print('convert_to_tex', flush=True)
        # convert_to_tex(data_pl_path, pl_n, playlist_info, episodes_info, wiki_episodes_info)
        print('NLP', flush=True)
        # NLP(data_pl_path, pl_n, playlist_info, episodes_info)
        print('Obsidian', flush=True)
        obsidize.main(data_pl_path, pl_n, playlist_info, episodes_info)

        sys.stdout = old_stdout
        log_file.close()


if __name__ == '__main__':
    main()

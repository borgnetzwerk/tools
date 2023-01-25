import core.helper as helper
import publish.Obsidian.obsidize as obsidize
import publish.MediaWiki.mediaWiki as mediaWiki
import extract.nlp.nlp as nlp

import re
import csv
import sys
import json
import os
import time
import numpy
from pprint import PrettyPrinter
from os import listdir
from os.path import isfile, join
from os.path import exists
import os.path as path
# Define
tokenfolder = helper.TOKENFOLDER
editfolder = helper.EDITFOLDER
# If major changes have been made: Flush out these old ones

# ---- Functions ---- #


# Convert extracted time to readable time


# Sort a dict according to a list.
# reminder: items not in the list won't be transferred.


# convert from Spotify index to dictionary


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
    if not found:
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


def convert_to_wiki(input_path, playlist_name, playlist_info, episodes_info):
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)
    return mediaWiki.main(playlist_info, episodes_info, input_path, playlist_name)


def main():
    # path of our playlist folders: data_path -> str
    # names of our playlists: playlist_names -> List
    data_path, playlist_names = helper.get_data_folders()
    for pl_n in playlist_names:
        # Change stdout so it writes to logfile_{pl_n}.log
        old_stdout = sys.stdout
        log_file = open("logfile_" + pl_n + ".log", "w", encoding='utf8')
        sys.stdout = log_file

        # Setup
        data_pl_path = data_path + pl_n + '\\'
        playlist_info = {}
        episodes_info = {}

        # todo: read json file first
        wiki_episodes_info = convert_to_wiki(
            data_pl_path, pl_n, playlist_info, episodes_info)

        sys.stdout = old_stdout
        log_file.close()


if __name__ == '__main__':
    main()

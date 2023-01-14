import json
import difflib
import difflib
import Levenshtein
import re
import re
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime
import math
from collections import Counter
import numpy as np
from numpy.linalg import norm

SIMILAR_ENOUGH = {
    "cosine": 0.9,
    "levenshtein": 0.85,
    "jaccard": 0.9,
    "sequencematcher": 0.9,
}
AUDIOFOLDER = 'mp3'
TOKENFOLDER = 'token'
EDITFOLDER = 'edited'


# Prepare dict so it can be used for MediaWiki
noFileChars = '":\<>*?/'


def cosine_similarity(A, B):
    # define two lists or array

    # compute cosine similarity
    cosine = np.dot(A, B)/(norm(A)*norm(B))
    return cosine


def get_clean_title(title, eID, obsidian=False):
    """
    Cleans a given title to make it suitable for filenames.

    Parameters:
    title (string): The title. "episode1"
    eID (int): The position of that episode in the playlist. 

    Returns:
    string: cleaned title for use as filename
    """
    clean_title = title
    for each in noFileChars:
        clean_title = clean_title.replace(each, '')
    if obsidian:
        clean_title = clean_title.replace("#", '')
    clean_title = fill_digits(eID, 3) + '_' + clean_title
    return clean_title


def get_edited_path(clean_title, input_path):
    if input_path[-1] != '\\':
        input_path += '\\'
    json_path = input_path + EDITFOLDER + '\\' + clean_title + '.json'
    return json_path


def show_newest_files(input_path, files):
    # todo: Test if this could be replaced by:
    # files = [x for x in sort(os.path.getmtime(input_path+'\\'+x))]
    dates = []
    for file in files:
        date = os.path.getmtime(input_path+'\\'+file)
        dates.append(date)
    order = np.argsort(dates)
    files_sorted = []
    for position in reversed(order):
        files_sorted.append(files[position])
    return files_sorted


def clean_dict(dict, playlist_name):
    def default_cleaner(k, v):
        return v

    def split_authors(v, temp):
        temp2 = cut_out(v, dict_author)
        temp['author_type'] = remove_quot(temp2['author_type'])
        temp['author_name'] = remove_quot(temp2['author_name'])
        return temp

    cleaners = {
        'id': default_cleaner,
        'date': time_converter,
        'runtime': time_converter,
        'name': default_cleaner,
        'title': default_cleaner,
        'description': default_cleaner,
        'publisher': default_cleaner,
        'language': default_cleaner,
        '@type': default_cleaner,
        'accessMode': default_cleaner,
        'url': default_cleaner,
        'image': default_cleaner
    }

    temp = {}
    for k, v in dict.items():
        v = remove_quot(v)
        if k in cleaners:
            temp[k] = cleaners[k](k, v)
        elif k == 'author':
            temp[k] = split_authors(v, temp)
        else:
            temp[k] = default_cleaner(k, v)
    return temp


def compare_titles(try_this, comp, playlist_name):
    similarity_score = 0
    for struc in try_this:
        if struc in try_this and struc in comp:
            if comp[struc] == try_this[struc]:
                similarity_score += title_structure[playlist_name][struc][1]
                # We have found the matching episode and it has the ID idx
    return similarity_score


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


def forge_title(title, eID, playlist_name):
    eID += 1  # use ID+1 as eID
    pieces = title_mine(title, playlist_name)
    if 'eID' in pieces:
        eID = pieces['eID']
    elif eID > 128:
        eID += 1
    title = ''
    if 'title' in pieces:
        title = pieces['title']
    title = '#' + str(eID) + ": " + title
    # No playlist_name in title:
    title = re.sub(re.escape(playlist_name) + ' *:*', '', title, 1)
    return title


# Author_name and _type is nested in author, so they have to be extracted as well (for cut_out function)
dict_author = {
    "final_destination_void": "}",
    'author_name': ',"name":',
    'author_type': '{"@type":'
}


def fill_digits(var_s, cap=2):
    """Add digits until cap is reached"""
    var_s = str(var_s)
    while len(var_s) < cap:
        var_s = "0" + var_s
    return var_s


def remove_quot(var_s):
    """Remove leading and closing quotation marks"""
    if var_s:
        if var_s[0] == '"':
            var_s = var_s[1:]
        if var_s[-1] == '"':
            var_s = var_s[:-1]
    return var_s


def get_brand(t):
    if "spotify.com" in t:
        return "Spotify"
    elif "youtube.com" in t:
        return "YouTube"
    elif "bnwiki.de" in t:
        return "BNW"
    return 'Link'


def setup_infos(playlist_info, episodes_info, input_path):
    if not playlist_info:
        with open(input_path + 'playlist_info.json', encoding='utf-8') as json_file:
            # Todo: if an "old replacement"
            playlist_info = json.load(json_file)
    if not episodes_info:
        with open(input_path + 'episodes_info.json', encoding='utf-8') as json_file:
            episodes_info = json.load(json_file)
            episodes_info = {int(k): v for k, v in episodes_info.items()}
    return [playlist_info, episodes_info]


def get_data_folders():
    """Goes up once, then down the data path"""
    my_path = os.getcwd()
    data_path = os.path.dirname(my_path) + '\\data\\'
    playlist_names = [f for f in listdir(
        data_path) if not isfile(join(data_path, f))]
    playlist_names.remove('sample')
    return [data_path, playlist_names]


def cut_hypen(var_s):
    """Cut a string at the first hypen"""
    var_s = var_s.split(" -", 1)[0]
    var_s = var_s.split("-", 1)[0]
    var_s = remove_quot(var_s)
    return var_s


def cut_out(var_s, dict):
    """Cut a string at predetermined marks"""
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


def time_converter(var_s):
    if "Std." in var_s or "Min." in var_s or "Sek." in var_s:
        # Time: HH:MM:SS
        m = re.search(r'\d*(?= *Std.)', var_s)
        std = "" if m is None else m.group(0)
        time = fill_digits(std) + ":"
        m = re.search(r'\d*(?= *Min.)', var_s)
        min = "" if m is None else m.group(0)
        time += fill_digits(min) + ":"
        m = re.search(r'\d*(?= *Sek.)', var_s)
        sek = "" if m is None else m.group(0)
        time += fill_digits(sek)
        return time
    else:
        # Date: YYYY-MM-DD
        list = var_s.split(' ')
        if len(list) == 1:
            # TODO: catch if date is already (somewhat) formatted
            return var_s
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


def cosine_similarity_text(seq1, seq2):
    # Convert the sequences to word count dictionaries
    seq1_word_count = Counter(seq1)
    seq2_word_count = Counter(seq2)

    # Get the set of unique words in both sequences
    common_words = set(seq1_word_count.keys()) & set(seq2_word_count.keys())

    # If the sequences have no words in common, return 0
    if not common_words:
        return 0

    # Calculate the dot product of the sequences
    dot_product = sum(
        seq1_word_count[word] * seq2_word_count[word] for word in common_words)

    # Calculate the Euclidean norms of the sequences
    seq1_norm = math.sqrt(
        sum(seq1_word_count[word] ** 2 for word in seq1_word_count))
    seq2_norm = math.sqrt(
        sum(seq2_word_count[word] ** 2 for word in seq2_word_count))

    # Return the Cosine similarity
    return dot_product / (seq1_norm * seq2_norm)


def similar(seq1, seq2, method='levenshtein', level=-1):
    """
    Compare two sequences and return True if they are similar enough, based on the chosen method and threshold.

    Parameters
    ----------
    seq1 : str
        The first sequence to compare.
    seq2 : str
        The second sequence to compare.
    method : str, optional
        The method to use for comparing the sequences. Supported values are 'cosine', 'levenshtein', 'jaccard', and 'sequencematcher'.
        Default is 'levenshtein'.
    level : float, optional
        The similarity threshold. Sequences with a similarity score greater than or equal to this value will be considered
        similar. Default is 0.9.

    Returns
    -------
    bool
        True if the sequences are similar enough, False otherwise.

    Raises
    ------
    ValueError
        If the specified method is not supported.
    """
    if level == -1:
        level = SIMILAR_ENOUGH[method]
    if method == 'levenshtein':
        distance = Levenshtein.distance(seq1.lower(), seq2.lower())
        max_length = max(len(seq1), len(seq2))
        return 1 - distance / max_length > level
    # todo: make jaccard worth
    elif method == 'jaccard':
        seq1 = set(re.findall(r'\w+', seq1.lower()))
        seq2 = set(re.findall(r'\w+', seq2.lower()))
        intersection = seq1 & seq2
        union = seq1 | seq2
        return len(intersection) / len(union) > level
    elif method == 'sequencematcher':
        return difflib.SequenceMatcher(a=seq1.lower(), b=seq2.lower()).ratio() > level
    elif method == 'cosine':
        return cosine_similarity_text(seq1, seq2) > level
    else:
        raise ValueError('Invalid method: {}'.format(method))


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


def json2dict(dict_var, name, path=os.getcwd()):
    json_pos = name.find(".json")
    if json_pos != len(name)-5:
        name += '.json'
    if path[-2:] != "\\":
        path += "\\"
    filepath = path + name
    with open(filepath, encoding='utf-8') as json_file:
        dict_var.update(json.load(json_file))
    return os.path.getmtime(filepath)


def lemmatize(var_dict, nlp):
    # this might change the reslts
    wordcount = len(var_dict)
    print('lemmatizing ' + str(wordcount) + ' words', flush=True)
    lemma_dict = {}
    lemmacon = {}
    # this currently turns 500kg to 500 kg, makes it 2 lemmata and thus brakes the sync
    # lemmas = nlp(' '.join(list(var_dict.keys())))
    min = 0
    steps = 1000
    words = list(var_dict.keys())
    lemmas_total = []
    for i in range(int(wordcount/1000)+1):
        words_here = words[i*steps:(i+1)*steps]
        lemmas = nlp(' '.join(words_here))
        if len(words_here) != len(lemmas):
            lemmas = []
            for word in words_here:
                check_lemmas = nlp(word)
                check_lemma_ = []

                for l in check_lemmas:
                    check_lemma_.append(l.lemma_)
                if len(check_lemma_) > 1:
                    print(
                        f"{word} gets lemmatized to {'; '.join(check_lemma_)}", flush=True)
                lemma = "".join(check_lemma_)
                lemmas.append(lemma)
        lemmas_total += lemmas

    for idx, [word, value] in enumerate(var_dict.items()):
        # check_lemmas = nlp(word)
        # check_lemma_ = []
        # if idx % 1000 == 0:
        # print(str(idx), flush=True)
        # for l in check_lemmas:
        # check_lemma_.append(l.lemma_)
        # if len(check_lemmas) > 1:
        # lemma = nlp(word)[0]
        # lemma = lemmas[idx].lemma_
        # if lemma != check_lemma_[0]:
        #     if lemma == check_lemma_[0].replace("ß", "ss"):
        #         continue
        #     print(f"{word} gets lemmatized to {lemma} and {check_lemma_}")
        # TODO: Find out why lemma is sometimes not automatically lower case
        lemma = lemmas_total[idx]
        if type(lemma) is not str:
            lemma = lemma.lemma_
        lemma = lemma.lower()
        # Todo: Not sure how to handle "Alte Rechtschreibung" yet
        # lemma = lemma.replace("ß", "ss"),
        # Due to lexicon being sorted, lemma elements should be automatically sorted
        # sort = False
        # if lemma in lemma_dict:
        #     sort = True
        lemma_dict[word] = lemma
        nested_add(lemmacon, [lemma], {word: value})
        # if sort:
        #     lemma_dict[lemma] = {k: v for k, v in sorted(
        #         lemma_dict[lemma].items(), reverse=True, key=lambda item: item[1])}
    print('reduced to  ' + str(len(lemmacon)) + ' words', flush=True)
    return lemmacon, lemma_dict


def get_transcript(input_path, filename):
    path_json = input_path + AUDIOFOLDER + '\\' + filename
    with open(path_json, encoding='utf-8') as json_file:
        transcript = json.load(json_file)
    return transcript


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
        if type(value) == dict:
            for key_i, value_i in value.items():
                nested_add(dic, keys + [key_i], value_i)
        else:
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
            if not inner_results:
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

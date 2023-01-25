import publish.graphvizify as graphvizify
import config.personal as personal
import core.helper as helper

from PIL import Image
from numpy.linalg import norm
import numpy as np
import json
import re
import os

# "path\to\your\Obsidian\vault"
OBSIDIAN_PATH = personal.OBSIDIAN_PATH


def add_links(links):
    note = "# Links\n"
    if links:
        link_preps = []
        for link in links.keys():
            link_preps.append("lexicon/" + link)
        note += "[[" + "]] ; [[".join(link_preps) + "]]"
    note += "\n\n"
    # text = re.sub(r"\b\w+\b", r"[[\g<0>]]", text)
    return note


def add_related(group_list, pl_n):
    note = "# Related Episodes\n"
    g_list = []
    for i in group_list:
        g_list.append(f"{pl_n}/{i}|{i}")
    note += "[[" + "]] ; [[".join(g_list) + "]]\n\n"
    # text = re.sub(r"\b\w+\b", r"[[\g<0>]]", text)
    return note


def add_urls_to_note(url, prefix):
    note = ""
    urls = url.split(" ; ")
    brands = []
    for url in urls:
        brand = helper.get_brand(url)
        if brand in brands:
            brand += str(brands.count(brand))
        brands.append(brand)
        note += prefix + "url_" + brand + ": \"" + url + "\"\n"
    return note


def make_a_note_out_of_me(transcript, episode_info, playlist_info):
    note = "---\n"
    tags = ""
    if len(transcript["text"]) < 50:
        tags += "#missingText "

    if "date" in episode_info:
        note += "date: " + episode_info["date"] + "\n"
    if "runtime" in episode_info:
        note += "runtime: " + episode_info["runtime"] + "\n"
    if "title" in episode_info:
        note += "title: \"" + episode_info["title"] + "\"\n"
    if "url" in episode_info:
        note += add_urls_to_note(episode_info["url"], "")
    if "playlist" in playlist_info:
        tags += "#" + playlist_info["playlist"] + " "
        note += "playlist: \"" + playlist_info["playlist"] + "\"\n"
    if "author_type" in playlist_info:
        note += "author_type: \"" + playlist_info["author_type"] + "\"\n"
    if "author_name" in playlist_info:
        tags += "#" + playlist_info["author_name"] + " "
        note += "author_name: \"" + playlist_info["author_name"] + "\"\n"
    if "author_url" in playlist_info:
        note += add_urls_to_note(playlist_info["author_url"], "author_")
    if "publisher" in playlist_info:
        note += "publisher: \"" + playlist_info["publisher"] + "\"\n"
    if "language" in playlist_info:
        tags += "#" + playlist_info["language"] + " "
        note += "language: \"" + playlist_info["language"] + "\"\n"
    if "@type" in playlist_info:
        tags += "#" + playlist_info["@type"] + " "
        note += "@type: \"" + playlist_info["@type"] + "\"\n"
    if "accessMode" in playlist_info:
        tags += "#" + playlist_info["accessMode"] + " "
        note += "accessMode: \"" + playlist_info["accessMode"] + "\"\n"
    if "url" in playlist_info:
        note += add_urls_to_note(playlist_info["url"], "playlist_")
    if "image" in playlist_info:
        note += "playlist_image: \"" + playlist_info["image"] + "\"\n"
    note += "---\n"
    # note += "```citeTitle:\n" +  + "\n```\n"
    # note += "```citeID:\n" + episode_info["citeID"] + "\n```\n"
    # note += "---\n"
    # note += "url: " + episode_info["url"] + "\n"
    # note += "zotero: " + episode_info["zotero"] + "\n"
    # note += "\n---\n"
    note += "tags:: " + tags + "\n"
    did_i_read_it = "#read/false "
    note += "read?:: " + did_i_read_it + "\n"
    comment = ""
    note += "comment:: " + comment + "\n"
    note += "\n---\n"
    return note


def add_full_text(text, links):
    for lemma, words in links.items():
        for word in words:
            text = re.sub(r"\b" + word + r"\b",
                          r"[[lexicon/" + lemma + "|\g<0>]]", text, flags=re.I)
    note = "# FullText\n"
    note += text + "\n\n"
    return note


def make_images(sim_matrix, edited_path):

    I8 = (((sim_matrix - sim_matrix.min()) /
          (sim_matrix.max() - sim_matrix.min())) * 255.9).astype(np.uint8)

    img = Image.fromarray(I8)
    factor = 9
    new_size = (img.size[0] * factor, img.size[1] * factor)
    img.save(edited_path + "_sim_matrix.png")
    img = img.resize(new_size, Image.Resampling.NEAREST)
    img.save(edited_path + f"_sim_matrix{factor}.png")

    I8 = I8 + I8.transpose()

    img = Image.fromarray(I8)
    factor = 9
    new_size = (img.size[0] * factor, img.size[1] * factor)
    img.save(edited_path + "_sim_matrixM.png")
    img = img.resize(new_size, Image.Resampling.NEAREST)
    img.save(edited_path + f"_sim_matrixM{factor}.png")

    np.savetxt(edited_path + "_sim_matrix_I8.csv", I8, delimiter=";")


def dotify(dict_var):
    #todo: Rework this
    episodes_info = {}
    lexicon_ep_count = {}
    linkpreps = {}
    ##
    dot = {}
    for eID, episode_info in episodes_info.items():
        words = {}
        if eID not in linkpreps:
            continue
        # if eID > 100:
        #     break
        for word, lemma in linkpreps[eID].items():
            count = 0
            if word in lexicon_ep_count:
                if eID in lexicon_ep_count[word]:
                    count = lexicon_ep_count[word][eID]
            if lemma not in words:
                words[lemma] = 0
            words[lemma] += count
        ep = {
            "title": episode_info["title"],
            "words": words
        }
        dot.update({eID: ep})


def include_episodes(edited_path, obs_pl_path, episodes_info, playlist_info):
    with open(edited_path + '_lexicon_ep_count.json', encoding='utf-8') as json_file:
        lexicon_ep_count = json.load(json_file)
    with open(edited_path + '_lemma_dict.json', encoding='utf-8') as json_file:
        lemma_dict = json.load(json_file)
    with open(edited_path + '_lemmacon.json', encoding='utf-8') as json_file:
        lemmacon = json.load(json_file)
    trivial_max = len(episodes_info) * 0.1
    trivial_min = len(episodes_info) * 0.01
    trivial_min_in_e = 3
    link_min = 2
    wordlen_min = 2
    groups = {}
    words_by_ep = {}
    e_vector = {}
    for lemma, words in lemmacon.items():
        count = sum(words.values())
        if count < trivial_min:
            # This lemma is insignificant
            continue
        episodes_with_word_and_count = {}
        for word in words:
            if len(word) < wordlen_min:
                # word is to short (here: 1 symbol)
                continue
            episodes = lexicon_ep_count[word]
            for eID, e_count in episodes.items():
                eID = int(eID)
                if e_count >= trivial_min_in_e:
                    if eID not in episodes_with_word_and_count:
                        episodes_with_word_and_count[eID] = {}
                    episodes_with_word_and_count[eID].update({word: e_count})
        if len(episodes_with_word_and_count) > trivial_max:
            # number of episodes where this word is significant is too high
            continue
        if len(episodes_with_word_and_count) < link_min:
            # number of episodes where this word is significant is too low
            continue
        else:
            for key, value in episodes_with_word_and_count.items():
                if key not in words_by_ep:
                    words_by_ep[key] = {}
                words_by_ep[key].update({lemma: value})
            e_vector[lemma] = 0

    words_by_ep = dict(sorted(words_by_ep.items()))

    # Now we have:
    # words_by_ep = {
    #   "0" : {
    #       "lemma1" : {
    #           "word1" : 5,
    #           "word2" : 17
    #       }
    #   }
    # }

    # give them their sim vector:
    e_vectors = {}
    for eID in range(len(episodes_info)):
        if eID not in words_by_ep:
            e_vectors[eID] = np.array(list(e_vector.values()))
    for eID, contents in words_by_ep.items():
        temp_vector = list(e_vector.values())
        for lemma, words in contents.items():
            index = list(e_vector.keys()).index(lemma)
            temp_vector[index] = sum(words.values())
        e_vectors[eID] = np.array(temp_vector)

    # similar episodes
    sim_matrix = np.zeros((len(episodes_info), len(episodes_info)))
    for idx, eID in enumerate(episodes_info):
        for idy, ieID in enumerate(list(episodes_info)[idx+1:], idx+1):
            if eID not in words_by_ep or ieID not in words_by_ep:
                sim_matrix[idx][idy] = 0
            else:
                sim_matrix[idx][idy] = helper.cosine_similarity(
                    e_vectors[eID], e_vectors[ieID])
    np.savetxt(edited_path + "_sim_matrix.csv", sim_matrix, delimiter=";")

    # make_images(sim_matrix, edited_path)

    sim_matrix = sim_matrix + sim_matrix.transpose()
    max_related = 5
    related = {}
    for eID in range(len(episodes_info)):
        if eID not in words_by_ep:
            continue
        related[eID] = {}
        sim = sim_matrix[eID]
        ind = np.argpartition(sim, -max_related)[-max_related:]
        ind = ind[np.argsort(sim[ind])]
        for ieID in reversed(ind):
            if ieID not in words_by_ep:
                continue
            title_temp = episodes_info[ieID]['title']
            clean_title_temp = helper.get_clean_title(title_temp, ieID, True)
            related[eID].update({clean_title_temp: sim[ieID]})

    # graphvizify.dotify()
    # graphvizify.generate_dot_file(dot, "_dot", edited_path)

    # helper.dict2json(linkpreps, "_linkpreps", edited_path)

    for eID, episode_info in episodes_info.items():
        eID = int(eID)
        # if eID <= 20:
        #     continue
        # if eID > 100:
        #     return
        title = episode_info["title"]
        clean_title = helper.get_clean_title(title, eID)
        file_path = edited_path + clean_title + ".json"
        if os.path.exists(file_path):
            with open(file_path, encoding='utf-8') as json_file:
                transcript = json.load(json_file)
        else:
            print("Missing: " + file_path)
            continue
        # convert transcript
        note = make_a_note_out_of_me(transcript, episode_info, playlist_info)
        links = {}
        if eID in words_by_ep:
            links = words_by_ep[eID]
        note += add_links(links)
        if len(links) > 0:
            note += add_related(related[eID], playlist_info['title'])
        note += add_full_text(transcript['text'], links)
        # write transcript
        clean_title = helper.get_clean_title(title, eID, True)
        filepath = obs_pl_path + "\\" + clean_title + ".md"
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(note)


def include_lexicon(edited_path, playlist_name):
    with open(edited_path + '_lexicon_similar.json', encoding='utf-8') as json_file:
        lexicon_similar = json.load(json_file)
    with open(edited_path + '_lemmacon.json', encoding='utf-8') as json_file:
        lemmacon = json.load(json_file)
    if not os.path.exists(OBSIDIAN_PATH + "\\lexicon"):
        os.makedirs(OBSIDIAN_PATH + "\\lexicon")
    for key, value in lemmacon.items():
        # handle if note already exists
        count_in_ = 0
        flexeds = []
        for flexed, count in value.items():
            count_in_ += count
            flexeds.append(flexed)
        if count_in_ < 3:
            continue
        similar = []
        if key in lexicon_similar:
            similar = lexicon_similar[key]
        note = "---\n"
        note += "count_in_" + playlist_name + ": " + str(count_in_) + "\n"

        note += "---\n"

        tags = "#lexem "

        note += "tags:: " + tags + "\n"
        comment = ""
        note += "comment:: " + comment + "\n"
        note += "\n---\n"
        note += "# Inflected words\n"
        note += "; ".join(flexeds) + "\n\n"
        note += "# similar words\n"
        note += "; ".join(similar) + "\n\n"
        # note += add_links(value)
        # write transcript
        filepath = OBSIDIAN_PATH + "\\lexicon\\" + key + ".md"

        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(note)


def include_to_obsidian(input_path, playlist_name, playlist_info, episodes_info):
    obs_pl_path = OBSIDIAN_PATH + "\\" + playlist_name
    if not os.path.exists(obs_pl_path):
        os.makedirs(obs_pl_path)
    data_path, playlist_names = helper.get_data_folders()
    input_path = data_path + playlist_name + "\\"
    edited_path = input_path + "edited\\"

    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)
    data_files, data_folders = helper.extract_file_folder(
        input_path + "edited\\")
    jsons = [filename for filename in data_files if filename.endswith(".json")]

    include_episodes(edited_path, obs_pl_path, episodes_info, playlist_info)
    # include_lexicon(edited_path, playlist_name)


def main(playlist_name='BMZ', input_path=os.getcwd(), playlist_info={}, episodes_info={}):
    include_to_obsidian(input_path, playlist_name,
                        playlist_info, episodes_info)


if __name__ == '__main__':
    main()

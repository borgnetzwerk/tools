import os
import helper
import re
import json
import personalInfos

# "path\to\your\Obsidian\vault"
OBSIDIAN_PATH = personalInfos.OBSIDIAN_PATH

def add_links(links):
    note = "# Links\n"
    note += "[[" + "]] ; [[".join(links) + "]]\n\n"
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
    for link in links:
        text = re.sub(r"\b" + link + r"\b", r"[[" + link + "|\g<0>]]", text, flags=re.I)
    note = "# FullText\n"
    note += text + "\n\n"
    return note

def include_to_obsidian(input_path, playlist_name, playlist_info, episodes_info):
    obs_pl_path = OBSIDIAN_PATH + "\\" + playlist_name
    if not os.path.exists(obs_pl_path):
        os.makedirs(obs_pl_path)
    data_path, playlist_names = helper.get_data_folders()
    input_path = data_path + playlist_name + "\\"
    edited_path = input_path + "edited\\"

    playlist_info, episodes_info = helper.setup_infos(
            playlist_info, episodes_info, input_path)
    data_files, data_folders = helper.extract_file_folder(input_path+ "edited\\")
    jsons = [filename for filename in data_files if filename.endswith(".json")]

    with open(edited_path + '_lexicon_ep_count.json', encoding='utf-8') as json_file:
        lexicon_ep_count = json.load(json_file)
    linkpreps = {}
    trivial_max = len(episodes_info) * 0.2
    trivial_min = 3
    link_min = 2
    wordlen_min = 2
    groups = {}
    for word, episodes in lexicon_ep_count.items():
        if len(word) < wordlen_min:
            continue
        # print(word + ":\t" + str(len(episodes)))
        if len(episodes) > trivial_max:
            continue
        group = []
        for eID, count in episodes.items():
            eID = int(eID)
            if count >= trivial_min:
                group.append(eID)
                if eID not in linkpreps:
                    linkpreps[eID] = []
        if len(group) < link_min:
            continue
        for eID in group:
            # words in the middle
            linkpreps[eID].append(word)
            # direct links:
            # for i_eID in group:
            #     if eID != i_eID:
            #         title = episodes_info[i_eID]["title"]
            #         clean_title = helper.get_clean_title(title, i_eID, True)
            #         link = playlist_name + "/" + clean_title
            #         if link not in linkpreps[eID]:
            #             linkpreps[eID].append(link)

    linkpreps = dict(sorted(linkpreps.items()))
        
    

    for eID, episode_info in episodes_info.items():
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
        #convert transcript
        note = make_a_note_out_of_me(transcript, episode_info, playlist_info)
        links = []
        if eID in linkpreps:
            links = linkpreps[eID]
        note += add_links(links)
        note += add_full_text(transcript['text'], links)    
        #write transcript
        clean_title = helper.get_clean_title(title, eID, True)
        filepath = obs_pl_path + "\\" + clean_title + ".md"
        with open(filepath, 'w', encoding='UTF8') as f:
            f.write(note)


def main(input_path=os.getcwd(), playlist_name='BMZ', playlist_info={}, episodes_info={}):
    include_to_obsidian(input_path, playlist_name, playlist_info, episodes_info)


if __name__ == '__main__':
    main()
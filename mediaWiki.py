import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import helper.helper as helper
import wiki_bot
import wiki.main as wiki_helpers


import json
import csv
import sys
import os
from os import listdir
from os.path import isfile, join
import urllib.parse


# from ...wiki_bot.src import main as wiki_bot
# https://iq-inc.com/importerror-attempted-relative-import/
# https://techwithtech.com/importerror-attempted-relative-import-with-no-known-parent-package/
# https://stackoverflow.com/questions/7505988/importing-from-a-relative-path-in-python

# first change the cwd to the script path
# scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
# os.chdir(scriptPath)

# #append the relative location you want to import from
# sys.path.append("../")
# import wiki_bot.src.main as wiki_bot
# sys.path.remove('/wiki_bot/src')
# import your module stored in '../common'


csv_delimiter = ';'

individual_wiki_pages_per_episode = False

"""
old functionality can be restored with:
write_individual_wiki_page

"""


def wiki_forge_title(title, playlist_name, id):
    if id is not None:
        title = helper.forge_title(title, id, playlist_name)
    title = title.replace('[', '(')
    title = title.replace(']', ')')
    title = title.replace('#', '')
    return title


def wikify_dict(dict, playlist_name, id=None, author_name='TBD'):
    temp = {}
    for k in dict:
        dict[k] = helper.remove_quot(dict[k])
        if k == 'id':
            temp[k] = dict[k]
        elif k == 'date':
            dict[k] = helper.time_converter(dict[k])
            temp[k] = dict[k]
        elif k == 'runtime':
            dict[k] = helper.time_converter(dict[k])
            temp[k] = dict[k]
        elif k == 'name':
            temp[k] = dict[k]
        elif k == 'title':
            temp['title_raw'] = dict[k]
            title = wiki_forge_title(dict[k], playlist_name, id)
            title_full = '/'.join([author_name, playlist_name, title])
            link_to_title = '[[' + title_full + '|' + title + ']]'
            temp['title'] = title
            temp['title_full'] = title_full
            temp['link_to_title'] = link_to_title
        elif k == 'description':
            temp[k] = dict[k]
        elif k == 'author':
            temp2 = helper.cut_out(dict[k], helper.dict_author)
            temp['author_type'] = helper.remove_quot(temp2['author_type'])
            temp['author_name'] = helper.remove_quot(temp2['author_name'])
        elif k == 'publisher':
            temp[k] = dict[k]
        elif k == 'language':
            temp[k] = dict[k]
        elif k == '@type':
            temp[k] = dict[k]
        elif k == 'accessMode':
            temp[k] = dict[k]
        elif k == 'url':
            tokens = dict[k].split(' ; ')
            winner = ""
            for t in tokens:
                url_var = 'Link'
                if "spotify.com" in t:
                    url_var = " Spotify"
                elif "youtube.com" in t:
                    url_var = " YouTube"
                winner += '[' + t + url_var + ']'
            temp[k] = winner
        elif k == 'image':
            temp[k] = '[' + dict[k] + ' image]'
        else:
            temp[k] = dict[k]
    return temp


def lookupCSV(input_path):
    input_path
    onlyfiles = [f for f in listdir(input_path) if isfile(join(input_path, f))]
    return [f for f in onlyfiles if ".csv" in f]


# convert from csv to wiki

def csv2wiki(playlist_info, episodes, input_path, playlist_name):
    # Könnte man auch als Übersicht über alle podcast machen, die im Data.bnwiki sind
    # Sortierbar nach Sprache etc.
    # Kategorien ...
    # mediaWiki.main(playlist_info, episodes, input_path, playlist_name)
    return

# convert from json to wiki


def json2wiki(playlist_info, episodes, input_path, filename, playlist_name):
    # Könnte man auch als Übersicht über alle podcast machen, die im Data.bnwiki sind
    # Sortierbar nach Sprache etc.
    # Kategorien ...
    # mediaWiki.main(input_path)
    return

# TODO: Rework these:


def some_old_func(playlist_info={}, episodes_info={}, input_path=os.getcwd(), playlist_name=''):
    playlist_info = wikify_dict(playlist_info, playlist_name)
    for e_key in episodes_info:
        episodes_info[e_key] = wikify_dict(episodes_info[e_key], playlist_name)
    # json2csv(playlist_info, episodes_info, input_path, playlist_name)


def add_wiki_url(wiki_episodes_info):
    for eID, episode_info in wiki_episodes_info.items():
        url_title = urllib.parse.quote(episode_info['title_full'])
        wiki_url = 'https://data.bnwiki.de/index.php?title=' + url_title
        episode_info['url_wiki'] = wiki_url
    return wiki_episodes_info


def update_wiki(playlist_info, episodes_info, input_path, playlist_name):
    wiki_playlist_info = wikify_dict(playlist_info, playlist_name)
    wiki_episodes_info = {}
    author_name = 'TBD'
    if 'author_name' in playlist_info:
        author_name = playlist_info['author_name']
    for eID, episode_info in episodes_info.items():
        wiki_episodes_info[eID] = wikify_dict(
            episode_info, playlist_name, eID, author_name)

    do_individual = True
    # do_individual = False

    queries = {}

    pagename = 'OnkelBarlow'

    text = wiki_helpers.write_episodes(
        playlist_name, wiki_episodes_info)
    tasks = {}

    order = 'edit'
    is_bot = True
    section = None
    promt = wiki_bot.page_promt(
        text, "edited from playlist2wiki-converter", is_bot, section)

    tasks.update({order: promt})

    queries.update({pagename: tasks})

    if do_individual:
        for eID, episode_info in wiki_episodes_info.items():
            # if eID > 2:
            #     break
            pagename = episode_info['title_full']

            transcript_text = ''
            clean_title = helper.get_clean_title(
                episode_info['title_raw'], eID)
            json_path = helper.get_edited_path(clean_title, input_path)

            if isfile(json_path):
                with open(json_path, encoding='utf-8') as json_file:
                    transcript = json.load(json_file)
                    # TODO: make this a better structured page:
                    transcript_text = transcript['text']
            episode_info['transcript'] = transcript_text

            episode_info['text'] = wiki_helpers.write_individual_wiki_page(
                playlist_name, eID, episode_info)
            tasks = {}

            order = 'edit'
            text = episode_info['text']
            is_bot = True
            section = None
            if 'section' in episode_info:
                section = episode_info['section']
            promt = wiki_bot.page_promt(
                text, "edited from playlist2wiki-converter", is_bot, section)

            tasks.update({order: promt})

            queries.update({pagename: tasks})
    # if len(queries) > 0:
    #     wiki_bot.main(queries)

    wiki_episodes_info = add_wiki_url(wiki_episodes_info)

    return wiki_episodes_info


def main(playlist_info={}, episodes_info={}, input_path=os.getcwd(), playlist_name=''):
    if input_path == os.getcwd():
        data_path, playlist_names = helper.get_data_folders()
        playlist_name = playlist_names[0]
        input_path = data_path + playlist_name + '\\'
        playlist_info, episodes_info = helper.setup_infos(
            playlist_info, episodes_info, input_path)
    # csv2table(input_path, lookupCSV(input_path))
    return update_wiki(playlist_info, episodes_info, input_path, playlist_name)


if __name__ == '__main__':
    main()

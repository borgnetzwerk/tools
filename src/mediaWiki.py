import helper
from ...wiki_bot.src import main as wiki_bot

import csv
import sys
import os
from os import listdir
from os.path import isfile, join

csv_delimiter = ';'

individual_wiki_pages_per_episode = False

"""
old functionality can be restored with:
write_individual_wiki_page

"""


def wikify_dict(dict, playlist_name):
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
            dict[k] = dict[k].replace('[', '(')
            dict[k] = dict[k].replace(']', ')')
            fulltitle = '[[' + playlist_name + ':'
            fulltitle += dict[k] + '|' + dict[k] + ']]'
            temp[k] = fulltitle
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


def write_individual_wiki_page(input_path, id, row, elements):
    text = ''
    text += row[elements['description']] + '\n'
    text += '\n'
    hashtag = '#'
    text += '{| class="wikitable"' + '\n'
    text += '! ' + hashtag + ' !! date !! runtime !! url' + '\n'
    text += '|-' + '\n'
    text += '| ' + str(id) + ' || ' + row[elements['date']] + ' || ' + \
        row[elements['runtime']] + ' || ' + row[elements['url']] + '\n'
    text += '|}' + '\n'
    text += '\n'
    text += '= Zusammenfassung =' + '\n'
    text += '<Zusammenfassung>' + '\n'
    text += '\n'
    text += '= Hörspiele =' + '\n'
    text += '== <Titel Hörspiel 1> ==' + '\n'
    text += '\n'
    text += '= Transkript =' + '\n'
    text += '\n'
    nickname = row[elements['title']].split("|", 1)[1]
    nickname = nickname.replace("]]", "")
    text += '[[Kategorie:Hagrids Hütte:Hörspiel|' + nickname + ']]' + '\n'
    text += '[[Kategorie:Hagrids Hütte:Episode|' + nickname + ']]' + '\n'
    # filename = helper.fill_digits(id, 4)
    # with open(input_path + filename + '_wiki.txt', 'w') as f:
    #     f.write(text)


def csv2table(input_path, filenames):
    for filename in filenames:
        cols = 1
        with open(input_path + filename, newline='') as rf, open(input_path + filename.replace(".csv", "") + '_wiki.txt', 'w') as f:
            freader = csv.reader(rf, delimiter=csv_delimiter)
            lines = []
            elements = {
                "runtime": -1,
                "date": -1,
                "description": -1,
                "title": -1,
                "url": -1
            }
            if filename == "episodes.csv":
                f.write('=== Episoden ===\n')
            f.write('{| class="wikitable sortable"' + '\n')
            f.write('|+ ' + filename.replace(".csv", "") + '\n')
            for idx, row in enumerate(freader):
                f.write('|-' + '\n')
                if len(row) > cols:
                    cols = len(row)
                if idx == 0:
                    for idy, element in enumerate(row):
                        if element in elements:
                            elements[element] = idy
                    f.write('! ' + ' !! '.join(row) + '\n')
                else:
                    f.write('| ' + ' || '.join(row) + '\n')
                    if individual_wiki_pages_per_episode and filename == "episodes.csv":
                        write_individual_wiki_page(
                            input_path, idx, row, elements)
            f.write('|}' + '\n')
        # outfile.write('{| class = class="wikitable sortable"\n')


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


def update_wiki(playlist_info, episodes_info, input_path, playlist_name):
    wiki_episodes = wikify_dict


def main(playlist_info={}, episodes_info={}, input_path=os.getcwd(), playlist_name=''):
    if input_path == os.getcwd():
        input_path, playlist_names = helper.get_data_folders()
        playlist_name = playlist_names[0]
        playlist_info, episodes_info = helper.setup_infos(
            playlist_info, episodes_info, input_path)
    # csv2table(input_path, lookupCSV(input_path))
    update_wiki(playlist_info, episodes_info, input_path, playlist_name)


if __name__ == '__main__':
    main()

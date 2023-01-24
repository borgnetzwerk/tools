import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import os
import re
import helper.helper as helper
import json
import shutil
import spellcheck.spellcheck as s_check


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
    if not ac_dict:
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
    if not ac_dict:
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


def convert_to_tex(input_path, playlist_name, playlist_info, episodes_info, wiki_episodes_info={}):
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)
    language = 'de'
    if 'language' in playlist_info:
        language = playlist_info['language']
    # https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
    two_up = os.path.abspath(os.path.join(input_path, ".."))
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
        clean_name = helper.get_clean_title(title, e_key)
        json_path = helper.get_edited_path(clean_name, input_path)

        # reminder: Episodes that have no mp3 (i.E. Spotify exclusives) cannot be found
        if os.path.exists(json_path):
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


def main(data_pl_path, pl_n, playlist_info, episodes_info):
    print('convert_to_tex', flush=True)
    wiki_episodes_info = "I need to change how this information is carried"
    # todo: make it so that wiki_episodes_infos is no longer needed
    convert_to_tex(data_pl_path, pl_n, playlist_info,
                   episodes_info, wiki_episodes_info)


if __name__ == '__main__':
    main()

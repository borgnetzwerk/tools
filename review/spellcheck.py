import core.helper as helper
import review.spellcheck as s_check

import re
import os


def spellcheck_string(text, playlist_name):
    spellcheck_dict = s_check.main_dict
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
    edited_path = input_path + helper.EDITFOLDER + '\\'
    if not os.path.exists(edited_path):
        os.makedirs(edited_path)
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

    # do_token_stuff(input_path, jsons)
    # Todo: make every subsequential call look for transcripts in edited


def add_transcript(input_path, playlist_name, playlist_info, episodes_info):
    # Phase 0: Setup
    audiofolder = helper.AUDIOFOLDER

    data_files, data_folders = helper.extract_file_folder(input_path)
    data_files = helper.show_newest_files(input_path, data_files)
    # --- 1. Setup --- #
    # Log file
    # check what info is available

    # Read existing info
    playlist_info = {}
    episodes_info = {}

    # If major changes are made:
    playlist_info, episodes_info = helper.setup_infos(
        playlist_info, episodes_info, input_path)

    if not data_folders or audiofolder not in data_folders:
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
            # if playlist_name not in entry:
            #     continue
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
                    matched = helper.similar(title, new_title, "levenshtein")
                if matched:
                    clean_name = helper.fill_digits(idx, 3) + '_' + new_title
                    path_old = input_path + audiofolder + '\\' + filename
                    path_new = input_path + audiofolder + '\\' + clean_name + '.json'
                    if os.path.exists(path_old):
                        if os.path.exists(path_new):
                            continue
                        os.rename(path_old, path_new)
                    filename = filename.replace('.json', '.mp3')
                    path_old = input_path + audiofolder + '\\' + filename
                    path_new = input_path + audiofolder + '\\' + clean_name + '.mp3'
                    if filename in audios:
                        if os.path.exists(path_old) and not os.path.exists(path_new):
                            if not os.path.exists(path_new):
                                os.rename(path_old, path_new)
    spellcheck(input_path, playlist_name, jsons)
    # ! TODO: make this way more permanent
    # TODO

    def rreplace(s, old, new, occurrence):
        li = s.rsplit(old, occurrence)
        return new.join(li)

    if len(episodes_info) < len(jsons):
        for file in jsons:
            eID = file.split("_", 1)[0]
            if eID not in episodes_info:
                title = file.split("_", 1)[1]
                title = rreplace(title, ".json", "", 1)
                episodes_info[eID] = {'title': title}
        playlist_info['title'] = playlist_name
        playlist_info['author_name'] = playlist_name
        helper.dict2json(playlist_info, "playlist_info", input_path)
        helper.dict2json(episodes_info, "episodes_info", input_path)


def main(data_pl_path, pl_n, playlist_info, episodes_info):
    print('add_transcript', flush=True)
    add_transcript(data_pl_path, pl_n, playlist_info, episodes_info)


if __name__ == '__main__':
    main()

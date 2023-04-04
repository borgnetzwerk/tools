from os.path import isfile, join
from os import listdir
import os
from datetime import datetime
import time
import json
import whisper
import sys


def benchmark(filename="C:/Users/TimWittenborg/workspace/borgnetzwerk/data/BMZ/mp3/BMZ #001 Legendaries und Artefakte.mp3"):
    old_stdout = sys.stdout
    with open("logfile.log", "a", encoding='utf-8') as log_file:
        sys.stdout = log_file

        checkpoint = time.time()
        print(str(time.time()-checkpoint) + '\n')

        model = whisper.load_model("tiny")
        result = model.transcribe(filename)
        with open('01_tiny.json'.format(1), 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)

        checkpoint = time.time()
        print(str(time.time()-checkpoint) + '\n')

        model = whisper.load_model("base")
        result = model.transcribe(filename)
        with open('02_bas.json'.format(1), 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)

        checkpoint = time.time()
        print(str(time.time()-checkpoint) + '\n')

        model = whisper.load_model("small")
        result = model.transcribe(filename)
        with open('03_small.json'.format(1), 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)

        checkpoint = time.time()
        print(str(time.time()-checkpoint) + '\n')

        model = whisper.load_model("medium")
        result = model.transcribe(filename)
        with open('04_medium.json'.format(1), 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)

        checkpoint = time.time()
        print(str(time.time()-checkpoint) + '\n')

        # if graphics card is strong enough:

        # model = whisper.load_model("large")
        # result = model.transcribe(filename)
        # with open('01_tiny.json'.format(1), 'w', encoding='utf-8') as file:
        #     json.dump(result, file, ensure_ascii=False, indent=4)

        # checkpoint = str(time.time())
        # print(checkpoint + '\n')

        # model = whisper.load_model("large-v2")
        # result = model.transcribe(filename)
        # json_object = json.dumps(result, indent=4)
        # with open("06_large-v2.json", "w", encoding='utf8') as outfile:
        #     outfile.write(json_object)

        # checkpoint = str(time.time())
        # print(checkpoint + '\n')
    sys.stdout = old_stdout


def grab(input_path, filename, device='cuda'):
    model = whisper.load_model("medium", device=device)
    result = model.transcribe(os.path.join(input_path, filename))
    if filename.endswith(".mp4"):
        newfilename_new = filename.replace('.mp4', '.json')
    elif filename.endswith(".mp3"):
        newfilename_new = filename.replace('.mp3', '.json')
    with open(os.path.join(input_path, newfilename_new), 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)


def grab_list(input_path, files, device='cuda'):
    model = whisper.load_model("medium", device=device)
    queue = []
    for filename in files:
        queue.append(os.path.join(input_path, filename))
    results = model.transcribe()
    for idx, result in enumerate(results):
        if files[idx].endswith(".mp4"):
            newfilename_new = files[idx].replace('.mp4', '.json')
        elif files[idx].endswith(".mp3"):
            newfilename_new = files[idx].replace('.mp3', '.json')
        with open(os.path.join(input_path, newfilename_new), 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)


def redo(filenames):
    file_path = os.getcwd() + '\\src\\redo.txt'
    with open(file_path, "r", encoding="utf8") as f:
        lines = f.readlines()
    files = [x.replace('stuck in no-punctuation mode: ', '') for x in lines]
    for file in files:
        file = file.replace('\n', '')
        # correct with files from redone
    return files


def redone(filename):
    file_path = os.getcwd() + '\\src\\redone.txt'
    with open(file_path, "r", encoding="utf8") as f:
        lines = f.readlines()
    files = [x.replace('stuck in no-punctuation mode: ', '') for x in lines]
    for file in files:
        file = file.replace('\n', '')
    return files


def extract_info(input_path, playlist_name=None):
    log_file = open("logfile.log", "a", encoding='utf-8')
    old_stdout = sys.stdout
    with open("logfile.log", "a", encoding='utf-8') as log_file:
        sys.stdout = log_file
        try:
            filenames = [f for f in listdir(
                input_path) if isfile(join(input_path, f))]
        except:
            return
        print('\n-------------\n', flush=True)
        print(str(datetime.now()) + '\n', flush=True)
        last_skipped = ""
        skipped = 0
        # redo_filenames = redo(filenames)
        for filename in filenames:
            if '.mp4' in filename or '.mp3' in filename:
                checkpoint = time.time()
                if filename.endswith(".mp4"):
                    newfilename_new = filename.replace('.mp4', '.json')
                elif filename.endswith(".mp3"):
                    newfilename_new = filename.replace('.mp3', '.json')
                if newfilename_new not in filenames:
                    if skipped > 0:
                        print('Skipping ' + str(skipped) +
                              ' until including ' + last_skipped + '.\n', flush=True)
                        skipped = 0
                    grab(input_path, filename)
                    print(str(datetime.now()), flush=True)
                    print(filename + ': ' + str(round(time.time() -
                                                      checkpoint, 2)) + " Sek." + '\n', flush=True)
                # elif filename in redo_filenames:
                #     if skipped > 0:
                #         print('Skipping ' + str(skipped) + ' until including ' + last_skipped + '.\n', flush=True)
                #         skipped = 0
                #     print('Redoing ' + filename + '.\n', flush=True)
                #     grab(input_path, filename)
                #     print(str(datetime.now()), flush=True)
                #     print(filename + ': ' + str(round(time.time()-checkpoint, 2)) + " Sek." + '\n', flush=True)
                #     redone(filename)
                else:
                    last_skipped = filename
                    skipped += 1
    sys.stdout = old_stdout


def main(my_path=None):
    my_path = os.getcwd()
    data_path = os.path.dirname(my_path) + '\\data\\'
    playlist_names = [f for f in listdir(
        data_path) if not isfile(join(data_path, f))]
    playlist_names.remove('sample')
    for pl_n in playlist_names:
        data_pl_path = data_path + pl_n + '\\mp3'
        extract_info(data_pl_path, pl_n)


if __name__ == '__main__':
    main()

# file formats
# vtt
# srt

# txt
# json

# with open("Output.txt", "w") as text_file:
#     text_file.write(result + '\n')

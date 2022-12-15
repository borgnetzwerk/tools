import whisper
import json
import sys
import time
from datetime import datetime
import os
from os import listdir
from os.path import isfile, join

def benchmark(filename = "C:/Users/TimWittenborg/workspace/borgnetzwerk/data/BMZ/mp3/BMZ #001 Legendaries und Artefakte.mp3"):
    old_stdout = sys.stdout
    log_file = open("logfile.log","a", encoding='utf-8')
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
    log_file.close()

def grab(input_path, filename):
    model = whisper.load_model("medium")
    result = model.transcribe(input_path + '\\' + filename)
    with open(input_path + '\\' + filename.replace('.mp3', '.json'), 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

def extract_info(input_path, playlist_name):
    old_stdout = sys.stdout
    log_file = open("logfile.log","a", encoding='utf-8')
    sys.stdout = log_file
    filenames = [f for f in listdir(input_path) if isfile(join(input_path, f))]
    print('\n-------------\n', flush=True)
    print(str(datetime.now()) + '\n', flush=True)
    last_skipped = ""
    skipped = 0
    for filename in filenames:
        if '.mp3' in filename:
            checkpoint = time.time()
            if filename.replace('.mp3', '.json') not in filenames:
                if skipped > 0:
                    print('Skipping ' + str(skipped) + ' until including ' + last_skipped + '.\n', flush=True)
                    skipped = 0
                grab(input_path, filename)
                print(str(datetime.now()), flush=True)
                print(filename + ': ' + str(round(time.time()-checkpoint, 2)) + " Sek." + '\n', flush=True)
            else:
                last_skipped = filename
                skipped += 1
    log_file.close()

def main():
    my_path = os.getcwd()
    data_path = os.path.dirname(my_path) + '\\data\\'
    playlist_names = [f for f in listdir(data_path) if not isfile(join(data_path, f))]
    playlist_names.remove('sample')
    for pl_n in playlist_names:
        data_pl_path = data_path + pl_n + '\\mp3'
        extract_info(data_pl_path, pl_n)
        
if __name__ == '__main__':
    main()

#file formats
# vtt
# srt

# txt
# json

# with open("Output.txt", "w") as text_file:
#     text_file.write(result + '\n')
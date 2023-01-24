import json
import datetime

# read the json file
with open("results/large_v2.json", "r") as f:
    data = json.load(f)

for i in range(len(data["segments"])):
    # get the start time
    start = data["segments"][i]["start"]
    # start time from ms to hh:mm:ss,xxx
    start = datetime.datetime.fromtimestamp(start / 1000.0).strftime('%H:%M:%S,%f')
    # get the end time
    end = data["segments"][i]["end"]
    # end time from ms to hh:mm:ss,xxx
    end = datetime.datetime.fromtimestamp(end / 1000.0).strftime('%H:%M:%S,%f')
    # get the text
    text = data["segments"][i]["text"][1:]
    bytes = text.encode('latin-1')
    text = bytes.decode('raw_unicode_escape')
    # write the vtt file
    with open("results/large-v2.vtt", "a") as f:
        f.write(str(i) + "\n")
        f.write(str(start) + " --> " + str(end) + "\n")
        f.write(str(text) + "\n\n")
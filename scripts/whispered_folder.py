import yaml
import os
import sys
import bnw_tools
# 
# from importlib.util import find_spec
# bnw_tools_spec = find_spec('bnw_tools')

# if bnw_tools_spec is None:
    # sys.path.append(os.getcwd())
    # import bnw_tools

# import bnw_tools

# todo: make this import cleaner
# sys.path.append(os.getcwd())
# sys.path.append(os.path.join(os.getcwd(), "bnw_tools"))

from bnw_tools.extract import util_pytube
from bnw_tools.publish.Obsidian import nlped_whispered_folder
from bnw_tools.publish import util_wordcloud
from bnw_tools.extract.nlp import util_nlp
from bnw_tools.extract import util_whisper


queue = [
    # {"folder": "D:/workspace/Zotero/pipelines",
    #  "language": "en"},
    # {"folder": "D:/workspace/Zotero/SE2A-B4-2",
    #  "language": "en"},
    # "language": "de"},
    {"folder": "D:/workspace/raw (MP3)/HoP",
     "image": "D:/workspace/raw (MP3)/HoP/mask/ab67656300005f1fcabcff3dcfa8fbd5f5b0fa04.jpeg",
     "language": "en"}
]


channels = {
    # "UCwBT6zl54_cP0mOrVPFH-qg": "BorgNetzWerk",
    # "UCoYvhMd-3LbORHvBVkC0hSw": "orkg7258",
    # "cinematherapysolutions": "CinemaTherapyShow",
    # "UCyHDQ5C6z1NDmJ4g6SerW8g": "maiLab",
    # "inanutshell": "kurzgesagt",
    # "sciphi635": "sciphi635",
    # "unbubble": "unbubble",
    # "georgiadow": "GeorgiaDow",
    # "LegalEagle": "LegalEagle",
    # "coldmirror": "coldmirror",
    # "UCPtUzxTfdaxAmr4ie9bXZVA": "MathebyDanielJung",
    # "ROCKETBEANSTV": "ROCKETBEANSTV",
}

YT_root = "D:/workspace/YouTube"
config = {
    # https://matplotlib.org/stable/users/explain/colors/colormaps.html
    "wordcloud": {
        "width": 1300,
        "height": 370,
        "max_words": 100,
        "background_color": "white",
        "colormap": "Dark2",
        "force": True,
    },
}

for channel_id, channel_name in channels.items():
    entry = {"folder": os.path.join(YT_root, channel_name),
             "channel_id": channel_id,
             "channel_name": channel_name}
    queue.append(entry)

# Extract
# Transcribe (Whisper)
nlptools = util_nlp.NLPTools()
for do in queue:
    folder_path = do["folder"]
    language = None
    if language in do:
        language = do["language"]
    old_stdout = sys.stdout
    # todo: make this clearer
    parent = os.path.basename(os.path.dirname(folder_path))
    if parent == "raw (MP3)":
        util_whisper.extract_info(folder_path)
    elif parent == "Zotero":
        # todo: make this productive
        pass
    elif parent == "YouTube":
        channel_id = do["channel_id"]
        channel_name = do["channel_name"]
        res = util_pytube.do_channels(YT_root, channel_id, channel_name)
        if res and "language" in res:
            language = res["language"]
        else:
            language = "en"
        pass
        # todo: make this productive

    sys.stdout = old_stdout
    # NLP (Flair and SpaCy)
    folder = util_nlp.Folder(
        folder_path, nlptools=nlptools, language=language)

    # Wordcloud
    if folder.media_resources:
        cloud_config = None
        if config and "wordcloud" in config:
            cloud_config = config["wordcloud"]

        util_wordcloud.generate_wordcloud(
            folder.bag_of_words.get(), os.path.join(folder_path, "00_bag_of_words"), config=cloud_config)
        util_wordcloud.generate_wordcloud(
            folder.named_entities.get_frequencies(), os.path.join(folder_path, "00_named_entities"), config=cloud_config)
        mask_path = folder.get_image()
        if mask_path:
            mask = util_wordcloud.generate_mask(mask_path)
            util_wordcloud.generate_wordcloud_mask(
                folder.bag_of_words.get(), mask, os.path.join(folder_path, "00_bag_of_words_mask"))
            util_wordcloud.generate_wordcloud_mask(folder.named_entities.get_frequencies(
            ), mask, os.path.join(folder_path, "00_named_entities_mask"))

        # Obsidian
        nlped_whispered_folder.folder(folder, force=True)

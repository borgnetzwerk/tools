import os
import sys
import json
from pytube import Channel
from pytube import Playlist
from pytube import YouTube

OVERWRITE = True

noFileChars = '":\<>*?/|,#.\'$^;~%'


def subtitle_clean(subtitle_text):
    subtitle_text = subtitle_text.split('\n\n')
    sent_num = 1

    result = ""
    for i in range((len(subtitle_text) - 1) // 2):
        _, temp_time, temp_text = subtitle_text[i * 2].split('\n')
        temp_start = temp_time.strip().split(' --> ')[0]
        _, next_time, _ = subtitle_text[(i + 1) * 2].split('\n')
        temp_end = next_time.strip().split(' --> ')[0]
        result += str(sent_num) + '\n'
        result += temp_start + ' --> ' + temp_end + '\n'
        result += temp_text.strip() + '\n'
        result += '\n'
        sent_num += 1

    rest = subtitle_text[-1].split('\n')
    _ = rest[0]
    temp_time = ""
    if len(rest) > 1:
        temp_time = rest[1]
    temp_text = ""
    if len(rest) > 2:
        temp_text = rest[2]

    result += str(sent_num) + '\n'
    result += temp_time + '\n'
    result += temp_text.strip() + '\n'
    return result

# Infos


class YouTubeInfo:
    def __init__(self, path: str = None, json_data: dict[str, str] = None):
        if path:
            if os.path.exists(path):
                if not json_data:
                    json_data = {}
                with open(path, "r", encoding="utf-8") as json_file:
                    json_data.update(json.load(json_file))

        self.video_id = json_data['videoDetails']['videoId'] if json_data else None
        self.title = json_data['videoDetails']['title'] if json_data else None
        self.length_seconds = json_data['videoDetails']['lengthSeconds'] if json_data else None
        self.channel_id = json_data['videoDetails']['channelId'] if json_data else None
        self.short_description = json_data['videoDetails']['shortDescription'] if json_data else None
        self.view_count = json_data['videoDetails']['viewCount'] if json_data else None
        self.author = json_data['videoDetails']['author'] if json_data else None
        self.publish_date = json_data['videoDetails']['publish_date'] if json_data else None

        self.cap_codes = json_data['cap_codes'] if json_data and "cap_codes" in json_data else {
        }

        self.thumbnail_urls = []
        if json_data and 'videoDetails' in json_data and 'thumbnail' in json_data['videoDetails']:
            for thumbnail in json_data['videoDetails']['thumbnail']['thumbnails']:
                self.thumbnail_urls.append(thumbnail['url'])

    def get_transcript(self):
        score = {
            "": 0,
            "a.de": 1,
            "a.en": 2,
            "de": 3,
            "en": 4,
        }

        def get_accepted(candidate):
            candidate = candidate.replace("a.", "")
            if len(candidate) > 2:
                if candidate[:2] in score:
                    return candidate[:2]
            return candidate
        best = ["", 0]

        for candidate in self.cap_codes.keys():
            c_score = 1
            key = candidate
            candidate = get_accepted(candidate)
            if key in score:
                c_score = score[key]
            elif candidate in score:
                c_score = score[candidate]
            # Todo: support more than german and english
            # elif "a." in candidate:
            #     c_score = c_score / 2
            else:
                continue
            if c_score > best[1]:
                best = [key, c_score]

        res_language = get_accepted(best[0])

        res_text = self.cap_codes[best[0]] if best[0] in self.cap_codes else ""
        if not res_language:
            print("Supported languages: " + ", ".join(score.keys()))
            print("Given languages: " + ", ".join(self.cap_codes.keys()))
        return res_text, res_language


def print_infos(video, infos_dir):

    # TODO: check if file already exists
    'D:/AVC/BorgNetzWerk/audio/Über 70 Tage in unter 70 Minuten: 9000 Seiten auf Knopfdruck.json'
    filename = video.title
    for char in noFileChars:
        filename = filename.replace(char, "")
    file_path = os.path.join(infos_dir, filename) + ".json"
    if not OVERWRITE and os.path.isfile(file_path):
        return

    # https://github.com/pytube/pytube/issues/1085

    infos = {}
    not_interesting = [
        "responseContext",
        "playabilityStatus",
        "streamingData",
        "playbackTracking",
        "playerConfig",
        "storyboards",
        "trackingParams",
        "attestation",
        "adBreakParams",
        "playerSettingsMenuData",
        "endscreen",
    ]
    for key, value in video.vid_info.items():
        if key in not_interesting:
            continue
        infos[key] = value

    # publish time not known, just date
    # https://github.com/pytube/pytube/issues/1269
    infos['videoDetails'].update(
        {'publish_date': video.publish_date.isoformat()})

    for cap in video.captions:
        code = cap.code
        caption = video.captions[code]
        # Auto generation findable, but not used yet.
        # todo: Idea: Add Whisper transcript here as "w.de" or whatever.
        # auto_generated = False
        # if code.startswith("a."):
        #     auto_generated = True
        try:
            c1 = caption.generate_srt_captions()
            c2 = subtitle_clean(c1)
            if "cap_codes" not in infos:
                infos["cap_codes"] = {}
            infos["cap_codes"][code] = c2
        except Exception as e:
            print(f"\t\tError doing the {code} captions for: " + filename)
            print(e, flush=True)

    with open(file_path, 'w', encoding='utf8') as json_file:
        json.dump(infos, json_file, ensure_ascii=False, indent=4)

    return


def print_audio(video, audio_dir):
    test = video.title
    for char in noFileChars:
        test = test.replace(char, "")
    test += ".mp4"
    if not os.path.exists(os.path.join(audio_dir, test)):
        print("\t" + test)
        video.streams.get_audio_only().download(output_path=audio_dir)

    return

# TODO: Test https://www.youtube.com/user/coldmirror/videos
# TODO: Test https://www.youtube.com/@coldmirror/videos


def print_channel(c, channel_dir):
    filename = c.channel_name
    for char in noFileChars:
        filename = filename.replace(char, "")
    file_path = os.path.join(channel_dir, filename) + ".json"
    not_interesting = [
        "html",
        "ytcfg",
        # "initial_data",
    ]
    infos = {}
    object_methods = []
    object_values = []
    for method_name in dir(c):
        if method_name.startswith("_"):
            continue
        # if method_name.startswith('__'):
        #     continue
        if method_name.endswith("_html"):
            continue
        if method_name in not_interesting:
            continue
        try:
            if callable(getattr(c, method_name)):
                object_methods.append(method_name)
            else:
                object_values.append(method_name)
        except:
            pass
    for method_name in object_values:
        v = getattr(c, method_name)
        if method_name == "initial_data":
            v = v['metadata']
            del v['channelMetadataRenderer']['availableCountryCodes']
            method_name = "metadata"
        try:
            json.dumps(v)
        except:
            continue
        infos[method_name] = v
    infos["video_count"] = len(c.video_urls._elements)
    infos["video_urls"] = c.video_urls._elements
    # for idx, key in enumerate(c):
    #     try:
    #         infos[idx] = key
    #     except:
    #         pass
    with open(file_path, 'w', encoding='utf8') as json_file:
        json.dump(infos, json_file, ensure_ascii=False, indent=4)


def do_channels(root_path, channel_id, channel_name):

    # Check whether the specified path exists or not
    channel_dir = os.path.join(root_path, channel_name)
    audio_dir_old = os.path.join(channel_dir, "audio")
    audio_dir = os.path.join(channel_dir, "00_audios")
    if os.path.exists(audio_dir_old):
        os.rename(audio_dir_old, audio_dir)

    infos_dir_old = os.path.join(channel_dir, "infos")
    infos_dir = os.path.join(channel_dir, "00_infos")
    if os.path.exists(infos_dir_old):
        os.rename(infos_dir_old, infos_dir)

    paths = [channel_dir, audio_dir, infos_dir]
    for path_ in paths:
        if not os.path.exists(path_):
            os.makedirs(path_)
    os.chdir(channel_dir)

    try_this = [
        f"c/{channel_name}",
        f"channel/{channel_id}",
        f"u/{channel_name}",
        f"user/{channel_id}",

        f"c/{channel_id}",
        f"channel/{channel_name}",
        f"u/{channel_id}",
        f"user/{channel_name}",
        f"@{channel_id}",
        f"@{channel_name}"
    ]

    found = ""
    for this in try_this:
        try:
            # link = f'https://www.youtube.com/{this}/videos'
            link = f'https://www.youtube.com/{this}'
            c = Channel(link)
            # c = Channel(this)
            # c = Channel('https://www.youtube.com/c/ProgrammingKnowledge/videos')
            if c.videos:
                found = this
                break
        except:
            continue
    print("---")
    if not found:
        print(
            f"https://www.youtube.com/{channel_id} (@{channel_name}) did not work")
        return None
    video_count = len(c.videos)
    print(
        f"Now working on {video_count} videos from {channel_name} at {found}", flush=True)
    # TODO: methods to skip a channel
    # like:
    # check if newest video is already in files (what if you lost some other or an older got unblocked or sth)
    # check if video_count == filecount in both audio and info folder (what if an older got delted, but a new one came out)
    info_count = len(os.listdir(infos_dir))
    audio_count = len(os.listdir(audio_dir))
    if video_count == info_count:
        print(
            f"We already have all {info_count} infos & {audio_count} audios.")
    # if video_count == audio_count and video_count == info_count:
        # print(f"We already have {video_count} infos & audios.")
        return None
    else:
        print(f"We currently have {info_count} infos & {audio_count} audios.")
    print_channel(c, channel_dir)
    # prios = [1935]
    for idx, video in enumerate(c.videos):
        # TODO: Quick fix to skip what has been done already.
        # If files are missing (many reasons for that), remove this
        # TODO: make a dict of: filenames that exist : (their respective URLs)
        # if idx < info_count and idx not in prios:
        #     continue
        try:
            if idx % 50 == 0:
                print(f"Videos checked:\t{idx}/{video_count}", flush=True)
            print_infos(video, infos_dir)
            # print_audio(video, audio_dir)
        except Exception as e:
            print(f"\t\tError at {idx}:")
            try:
                print("\t\t" + video.title)
            except Exception as e2:
                print(e2, flush=True)
            print(e, flush=True)
    print('Download is complete')
    return True
    # todo: Make it so same named files do not overwrite eachother

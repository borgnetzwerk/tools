from core import helper

from PyPDF2 import PdfReader
import pandas as pd
import numpy as np
import math
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import codecs
import inspect

"""
    PUNISH_SEMIMATCH = 0.2
    PUNISH_NOMATCH = PUNISH_SEMIMATCH / 2
    cfg['WEAKEN_WORDCOUNT'] = 0.01
    FLAT_SCORE_BOOST = 10
}
"""


def decode_hex(hex_encoded_text):
    if not "/x" in hex_encoded_text:
        return hex_encoded_text

    # try:
    #     return bytes.fromhex(no_x_text).decode()
    # except:
    #     try:
    #         return bytes.fromhex(no_x_text).decode('latin-1')
    #     except:
    lines = hex_encoded_text.split("\n")
    line_list = []
    for text in lines:
        no_x_blocks = text.split(' ')
        blocks = []
        for block in no_x_blocks:
            if "/x" not in block or "http" in block or "www" in block:
                blocks.append(block)
                continue
            try:
                block = block.replace('/x', "")
                byte_block = bytes.fromhex(block)
            except Exception as e:
                print(f"{block}: {e}")
                try:
                    blocks.append(str(block))
                except:
                    blocks.append(" ")
                continue
            try:
                # if "\x" in block:
                try:
                    block_clean = byte_block.decode()
                    while "\\x" in block_clean:
                        block_clean = byte_block.decode('latin-1')
                        if "\\x" in block_clean:
                            print(f"couldn't resolve {block} to {block_clean}")
                # else:
                except:
                    block_clean = byte_block.decode('latin-1')
                    # blocks.append(byte_block.decode())
            except:
                block_clean = str(byte_block)[2:-1]
            blocks.append(block_clean)
        line_list.append(" ".join(blocks))
    return "\n".join(line_list)


def get_text(reader):
    fulltext = ""
    for page in reader.pages:
        text = page.extract_text()
        # some files are weirdly compiled as hex
        # That means we will decode any actual hex code in the file as well
        text = decode_hex(text)
        if fulltext:
            fulltext += "\n"
        fulltext += text
    if fulltext.count(' ') == 0:
        # todo: backup method to catch files like:
        # \files\58\Springer-TheNURBSBook.pdf
        return ""
    return fulltext


def calculate_score(entry_dict, fulltext, cfg):
    header = {'zotero_ID': entry_dict['ID']}
    scores = {}
    group_scores = {}
    appendix = {}
    total_score = 1
    wordcount = fulltext.count(" ")
    wordcount_weight = wordcount * cfg['WEAKEN_WORDCOUNT']
    for g_name, group in cfg['keywords'].items():
        scores.update({word: fulltext.count(word) for word in group})
        semimatches = []
        group_score = 0
        for word, weight in group.items():
            if not scores[word]:
                # attempt to find words otherwise
                fragments = word.split(" ")
                subscores = {fulltext.count(fragment)
                             for fragment in fragments}
                scores[word] = min(subscores) * cfg['PUNISH_SEMIMATCH']
                if scores[word] > 0:
                    semimatches.append(word)
            if scores[word] > 0:
                group_score += (scores[word]) * weight
        group_scores[g_name+"_score"] = group_score

    gsl = list(group_scores.values())
    for idx, score in enumerate(gsl):
        if score > 0:
            gsl[idx] = score/wordcount_weight
        else:
            gsl[idx] = cfg['PUNISH_NOMATCH']/wordcount_weight
    total_score = cfg['FLAT_SCORE_BOOST'] + math.log10(np.prod(gsl))
    # else:
    #     total_score = total_score/pow(wordcount, 3)
    header["total_score"] = total_score
    header.update(group_scores)
    header["wordcount"] = wordcount
    appendix["semimatches"] = ";".join(semimatches)
    entry_dict["k_score"] = header | scores | appendix
    return entry_dict


def read_pdf(filepath, entry_dict, cfg):
    try:
        reader = PdfReader(filepath)
    except Exception as e:
        print(e)
        return entry_dict
    fulltext = get_text(reader)
    if not fulltext:
        return entry_dict

    entry_dict = calculate_score(entry_dict, fulltext, cfg)
    return entry_dict
# read_pdf("", {})


def write_to_file(score_dict, path, cfg):
    # others
    helper.write_to_py(inspect.getsource(calculate_score),
                       os.path.join(path, "calculate_score.py"))
    # todo: make this go to yamls file
    helper.dict2json(cfg, "cfg", path)
    # CSV:
    score_dict = dict(sorted(score_dict.items(), key=lambda item: float(
        item[1]['total_score']), reverse=True))
    columns = list(list(score_dict.values())[0].keys())
    # df = pd.DataFrame([score_dict.values()], columns=columns, index=[score_dict.keys()])
    helper.write_to_csv(columns, list(score_dict.values()),
                        os.path.join(path, "k_score.csv"))

from PyPDF2 import PdfReader
import pandas as pd
import numpy as np
import math
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import helper
import codecs

keywords = {
    "modeling": {
        "Ontology simulation": 6,
        "modeling": 1,
        "engineering models": 2,
        "ontology coupled models": 5,
    },
    "engineering": {
        "structural": 1,
        "aerodynamic": 1,
        "thermodynamic": 1,
    },
    "multifidelity": {
        "multifidelity approach": 5,
        "variable fidelity simulation data": 3,
        "multidisciplinary design optimization": 3,
        "exchange of geometry information": 2,
    }
}

PUNISH_SEMIMATCH = 0.2
PUNISH_NOMATCH = PUNISH_SEMIMATCH / 2
WEAKEN_WORDCOUNT = 0.01
FLAT_SCORE_BOOST = 10

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


def read_pdf(filepath, entry_dict):
    # filepath = "H:\\Meine Ablage\\TIB_Obsidian\\Zotero\\Meine Bibliothek\\files\\134\\Sun et al. - 2009 - A framework for automated finite element analysis .pdf"
    try:
        reader = PdfReader(filepath)
    except Exception as e:
        print(e)
        return entry_dict
    fulltext = ""
    for page in reader.pages:
        text = page.extract_text()
        # some files are weirdly compiled as hex
        # That means we will decode any actual hex code in the file as well
        text = decode_hex(text)
        if fulltext:
            fulltext += "\n"
        fulltext += text
    if not fulltext or fulltext.count(' ') == 0:
        # todo: backup method to catch files like:
        # \files\58\Springer-TheNURBSBook.pdf
        return entry_dict
    filepath_new = filepath.replace(".pdf", "_extract.txt")
    # with open(filepath_new, "w", encoding="utf8") as f:
    #     f.write(fulltext)

    # vectorizer = CountVectorizer()
    # X = vectorizer.fit_transform([fulltext])
    # df_bow_sklearn = pd.DataFrame(X.toarray(),columns=vectorizer.get_feature_names_out())
    # df_bow_sklearn.head()
    # df_bow_sklearn.style

    header = {'zotero_ID': entry_dict['ID']}
    scores = {}
    group_scores = {}
    appendix = {}
    total_score = 1
    wordcount = fulltext.count(" ")
    wordcount_weight = wordcount * WEAKEN_WORDCOUNT
    for g_name, group in keywords.items():
        scores.update({word: fulltext.count(word) for word in group})
        semimatches = []
        group_score = 0
        for word, weight in group.items():
            if not scores[word]:
                # attempt to find words otherwise
                fragments = word.split(" ")
                subscores = {fulltext.count(fragment)
                             for fragment in fragments}
                scores[word] = min(subscores) * PUNISH_SEMIMATCH
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
            gsl[idx] = PUNISH_NOMATCH/wordcount_weight
    total_score = FLAT_SCORE_BOOST + math.log10(np.prod(gsl))
    # else:
    #     total_score = total_score/pow(wordcount, 3)
    header["total_score"] = total_score
    header.update(group_scores)
    header["wordcount"] = wordcount
    appendix["semimatches"] = ";".join(semimatches)
    appendix["total_score_function"] = "prod(group_score+1)/wordcount"
    entry_dict["k_score"] = header | scores | appendix
    return entry_dict
# read_pdf("", {})


def write_to_csv(score_dict, path):
    score_dict = dict(sorted(score_dict.items(), key=lambda item: float(
        item[1]['total_score']), reverse=True))
    columns = list(list(score_dict.values())[0].keys())
    # df = pd.DataFrame([score_dict.values()], columns=columns, index=[score_dict.keys()])
    helper.write_to_csv(columns, list(score_dict.values()), path)

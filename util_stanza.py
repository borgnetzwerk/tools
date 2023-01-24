import stanza
import util_networkx as nx
import util_pdf
import re
import os
# stanza.download('de')       # This downloads the English models for the neural pipeline
# This sets up a default neural pipeline in English
nlp = stanza.Pipeline('de')

try_pages = True
with open("input.txt", encoding="utf8") as f:
    text = f.read()


text = """
Täglich gibt es Forschungsergebnisse, die unmittelbar für die Menschen relevant sind, aber auch andere, deren Wert sich erst nach Jahrzehnten erschließt.
Die Wissenschaft durchdringt fast alle Bereiche des Lebens.
"""

pdf_name = "factory_wisskomm_publikation"
# pdf_path = "G:/.shortcut-targets-by-id/1Sxc0Ojy1-WTltHt2m2l2h-pHM7ToyAsc/ORKG/Proposals/2023-03-01_wit/"
# text_pages = util_pdf.get(pdf_name, pdf_path)
# # Täglich gibt es Forschungsergebnisse, die unmittelbar für die Menschen relevant sind, aber auch andere, deren Wert sich erst nach Jahrzehnten erschließt.
# # """
# text_pages.append("\n\n".join(text_pages))
# doc = nlp("Barack Obama was born in Hawaii.  He was elected president in 2008.")


def connect_words(text, page_id, doc):
    data = []
    data_set = set()
    love = ["root", "obj", "csubj", "amod", "conj", "nsubj"]
    hate = ["punct", "det", "case", "cc"]

    for sent in doc.sentences:
        for word in sent.words:
            id = word.id
            lemma = word.lemma
            text = word.text
            if not re.search(r".*[a-zA-Z].*", text):
                continue
            head_id = word.head
            head = sent.words[word.head-1].text if word.head > 0 else "root"
            deprel = word.deprel
            if deprel in hate:
                continue
            head_lemma = "root"
            s_head_id = head_id
            distance_to_root = 0
            while s_head_id:
                distance_to_root += 1
                s_head_id = sent.words[s_head_id-1].head
            if distance_to_root > 0 and distance_to_root < 4:
                pre = sent.words[word.head-1]
                if pre.deprel not in hate:
                    head_lemma = pre.lemma
                    data_set.add(f'"{lemma}"')
                    data_set.add(f'"{head_lemma}"')
                    data.append([f'"{lemma}"', f'"{head_lemma}"'])
    filename = f"{page_id}_{pdf_name}.dot"
    # if page_id == len(text_pages)-1:
    #     filename == f"{pdf_name}_full.dot"
    directory = "output/"
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(directory + filename, "w", encoding="utf8") as f:
        f.write("strict digraph  {\n")
        for lem in data_set:
            f.write(f"{lem}\n")
        for pair in data:
            f.write(f"{pair[0]} -> {pair[1]}\n")
        f.write("}\n")
    nx.dot_plot(filename, directory)

    # nx.graph_from_list(data)


def find_followers(leader, words):
    temp = {}
    for word in words:
        if word.head == leader:
            temp.update({word.id: find_followers(word.id, words)})
    return temp


def print_order(follower, words, ind=0):
    for leader in follower:
        pre = ""
        for i in range(ind):
            pre += "\t"
        print(pre + words[leader-1].text)
        print_order(follower[leader], words, ind+1)


def create_kg(text, page_id, doc):
    # data = []
    # data_set = set()
    # love = ["root", "obj", "csubj", "amod", "conj", "nsubj"]
    # hate = ["punct", "det", "case", "cc"]

    for sent in doc.sentences:
        subject = []
        predicate = []
        object = []

        for word in sent.words:
            if "obj" in word.deprel:
                object.append(word.id)
            elif "subj" in word.deprel:
                subject.append(word.id)
            elif "root" in word.deprel:
                predicate.append(word.id)

            # id = word.id
            # lemma = word.lemma
            # text = word.text
            # if not re.search(r".*[a-zA-Z].*", text):
            #     continue
            # head_id = word.head
            # head = sent.words[word.head-1].text if word.head > 0 else "root"
            # deprel = word.deprel
            # if deprel in hate:
            #     continue
            # head_lemma = "root"
            # s_head_id = head_id
            # distance_to_root = 0
            # while s_head_id:
            #     distance_to_root += 1
            #     s_head_id = sent.words[s_head_id-1].head
            # if distance_to_root > 0 and distance_to_root < 4:
            #     pre = sent.words[word.head-1]
            #     if pre.deprel not in hate:
            #         head_lemma = pre.lemma
            #         data_set.add(f'"{lemma}"')
            #         data_set.add(f'"{head_lemma}"')
            #         data.append([f'"{lemma}"', f'"{head_lemma}"'])
        if len(subject) > 1:
            pass
            # handle somehow
        if len(object) > 1:
            pass
            # handle somehow
        if len(predicate) > 1:
            pass
            # handle somehow
        subject = subject[0]
        object = object[0]
        predicate = predicate[0]
        leader = -1
        for word in sent.words:
            if word.head == 0:
                leader = word.id
                break
        follower = {
            leader : {}
        }
        follower[leader].update(find_followers(leader, sent.words))
        print_order(follower, sent.words)
        pass

    filename = f"{page_id}_{pdf_name}.dot"
    # if page_id == len(text_pages)-1:
    #     filename == f"{pdf_name}_full.dot"
    directory = "output/"
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(directory + filename, "w", encoding="utf8") as f:
        f.write("strict digraph  {\n")
        for lem in data_set:
            f.write(f"{lem}\n")
        for pair in data:
            f.write(f"{pair[0]} -> {pair[1]}\n")
        f.write("}\n")
    nx.dot_plot(filename, directory)

    # nx.graph_from_list(data)


def handle_text(text, page_id=0):
    doc = nlp(text)
    print(str(page_id))
    # doc.sentences[0].print_dependencies()

    print(*[f'id: {word.id}\tword: {word.text}\thead id: {word.head}\thead: {sent.words[word.head-1].text if word.head > 0 else "root"}\tdeprel: {word.deprel}' for sent in doc.sentences for word in sent.words], sep='\n')
    # connect_words(text, page_id, doc)
    create_kg(text, page_id, doc)


if try_pages:
    text_pages = re.split(r" \d{1,2}\n\d{1,2} ", text)
    for page_id, text in enumerate(text_pages):
        handle_text(text, page_id)
else:
    handle_text(text)

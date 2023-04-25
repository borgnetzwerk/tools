# controllers.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extract.nlp.util_nlp import Folder
from core import helper

import os
import json
import re


LIMIT_BAG_OF_WORDS = 10
LIMIT_NAMED_ENTITIES = 5
SIM_THRESHOLD = 0.05


class ObsidianNote:
    def __init__(self, path=None, name=None, text=None, simVec=None):
        self.path = path
        self.name = name
        self.text = text or None
        self.related_note_ids = None
        if path and text is None:
            self.fromfile(path)
        # if not self.iscomplete() and text:
        #     self.complete(text)
        if simVec:
            self.get_related_note_ids(simVec)

    def fromfile(self, path):
        """
        Load transcript from the given path.

        Args:
            path (str): Path to the transcript file.
        """
        self.path = path
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf8') as f:
                    self.text = f.read()
        except Exception as e:
            print(e)

    def iscomplete(self):
        if self.text and self.path:
            return True
        return False

    def save(self, path=None):
        if path is None:
            path = self.path

        with open(path, 'w', encoding='utf8') as f:
            f.write(self.text)

    def get_name(self, filename=None, fallback=None):
        if self.name and not filename:
            return self.name
        if self.path or filename:
            name = filename or os.path.basename(self.path)
        elif fallback:
            name = fallback
        else:
            raise Exception("This Obsidian note cannot find a name")

        if os.path.splitext(name) != ".md":
            name += ".md"
        self.name = helper.get_clean_title(name, obsidian=True)
        return self.name

    def get_path(self, parent_path=None):
        if parent_path:
            self.path = os.path.join(parent_path, self.get_name())
        return self.path

    def build_note(self, text, highlights=None, links=None, name=None, related_notes=None, files=None, additional_meta_data=None):
        title = name or self.get_name()
        metadata = ""
        if links:
            for link_name, words in links.items():
                metadata += f"{link_name}:: {', '.join('[[{}]]'.format(w) for w in words)}\n"
        if highlights:
            for highlight_name, words in highlights.items():
                metadata += f"{highlight_name}:: {', '.join('**{}**'.format(w) for w in words)}\n"

        if related_notes:
            metadata += f"Related Notes:: {', '.join('[[{}]]'.format(n) for n in related_notes)}\n"

        # todo: append more info here
        # if additional_meta:
            # metadata += f""

        corpus = ""
        for type, path in files.items():
            path = path.replace("\\", "/")
            corpus += f"## {type}\n![[{path}]]\n\n"

        # Replace first occurrence of each word in text with a link if it's in links or highlights
        if text:
            for word in text.split():
                if word in links:
                    text = text.replace(word, f"[[{word}]]", 1)
                elif word in highlights:
                    text = text.replace(word, f"**{word}**", 1)
            corpus += f"## Transcript\n{text}\n\n"

        fin_meta = ""
        if additional_meta_data:
            fin_meta += f"%%\n"
            for key, value in additional_meta_data.items():
                if value == "" or value is None:
                    continue
                if isinstance(value, str):
                    value = value.replace("\\", "/")
                fin_meta += f"{key}:: {value}\n"
            if fin_meta != f"%%\n":
                fin_meta += f"%%\n"
            else:
                fin_meta = ""

        self.text = f"""%%
{metadata}
%%

# {title}

{corpus}{fin_meta}
"""


def folder(folder: Folder, limit_ns=LIMIT_BAG_OF_WORDS, limit_ne=LIMIT_NAMED_ENTITIES, force=False):
    # loop over each file in the directory
    # build Entry Node
    # Sort all files into subfolders

    for idr, mr in enumerate(folder.media_resources):
        if not mr.obsidian_note:
            mr.add_obsidian_note()
        mr.obsidian_note.get_name(mr.original_name, fallback=mr.basename)
        mr.obsidian_note.get_path(folder.notes.path)

        # Create the Obsidian directory if it does not exist,

        bag_of_words = list(mr.nlp_analysis.bag_of_words.tf_idf.keys())[
            :LIMIT_BAG_OF_WORDS + LIMIT_NAMED_ENTITIES]
        named_entities = list(mr.nlp_analysis.named_entities.get().keys())[
            :LIMIT_NAMED_ENTITIES]

        for name in named_entities:
            lookfor = set([name.lower()]).union(name.lower().split())
            for word in lookfor:
                if word in bag_of_words:
                    bag_of_words.remove(word)
        bag_of_words = bag_of_words[:LIMIT_BAG_OF_WORDS]

        links = {}
        highlights = {}

        if named_entities:
            links["named_entities"] = named_entities

        if bag_of_words:
            highlights["bag_of_words"] = bag_of_words

        files = {}
        if mr.audio_file:
            files["Audio"] = os.path.basename(mr.audio_file.path)
        if mr.pdf:
            files["PDF"] = os.path.relpath(mr.pdf.path, folder.path)

        simVec = folder.sim_matrix[idr]
        top_indices = simVec.argsort()[-6:-1]
        related_notes = []
        for i in top_indices:
            # check if similarity is high enough
            if simVec[i] < SIM_THRESHOLD:
                break
            cr = folder.media_resources[i]
            related_notes.append(cr.obsidian_note.get_name(cr.original_name))
        text = None
        if mr.transcript:
            text = mr.transcript.text

        meta = {}
        if mr.pdf and mr.pdf.metadata:
            meta.update(mr.pdf.metadata)
        if mr.info:
            block = mr.info.__dict__
            del block['thumbnail_urls']
            del block['cap_codes']
            meta.update(block)
        try:
            if folder.rq:
                for id_rq, rq in enumerate(folder.rq.research_questions):
                    tag = helper.get_clean_title(
                        rq.title, obsidian=True).replace(" ", "_")
                    meta.update({tag: round(folder.rq_sim_mat[idr][id_rq], 3)})
        except Exception as e:
            print(e)

        mr.obsidian_note.build_note(
            text, links=links, highlights=highlights, name=mr.original_name, related_notes=related_notes, files=files, additional_meta_data=meta)

        # create the markdown file
        mr.obsidian_note.save()

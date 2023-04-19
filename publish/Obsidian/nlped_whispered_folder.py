import os
import json
import re

from extract.nlp import util_nlp
from core import helper

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

    def build_note(self, text, highlights=None, links=None, name=None, related_notes=None, audio=None):
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

        corpus = ""
        if audio:
            corpus += f"## Audio\n![[{audio}]]\n\n"

        # Replace first occurrence of each word in text with a link if it's in links or highlights
        if text:
            for word in text.split():
                if word in links:
                    text = text.replace(word, f"[[{word}]]", 1)
                elif word in highlights:
                    text = text.replace(word, f"**{word}**", 1)
            corpus += f"## Transcript\n{text}\n\n"

        self.text = f"""%%
{metadata}
%%

# {title}

{corpus}
"""


def folder(folder, limit_ns=LIMIT_BAG_OF_WORDS, limit_ne=LIMIT_NAMED_ENTITIES, force=False):
    # loop over each file in the directory
    # build Entry Node
    # Sort all files into subfolders

    for idr, mr in enumerate(folder.media_resources):
        mr.obsidian_note.get_name(mr.original_name, fallback=mr.basename)
        mr.obsidian_note.get_path(folder.notes.path)

        # Create the Obsidian directory if it does not exist,

        bow = list(mr.nlp_analysis.bag_of_words.tf_idf.keys())[
            :LIMIT_BAG_OF_WORDS+LIMIT_NAMED_ENTITIES]
        nen = list(mr.nlp_analysis.named_entities.get().keys())[
            :LIMIT_NAMED_ENTITIES]

        for name in nen:
            lookfor = set([name.lower()]).union(name.lower().split())
            for word in lookfor:
                if word in bow:
                    bow.remove(word)
        bow = bow[:LIMIT_BAG_OF_WORDS]

        links = {
            "named_entities":  nen
        }

        highlights = {
            "bag_of_words":  bow
        }

        audio_name = os.path.basename(mr.audio_file.path)

        simVec = folder.sim_matrix[idr]
        top_indices = simVec.argsort()[-6:-1]
        related_notes = []
        for i in top_indices:
            # check if similarity is high enough
            if simVec[i] < SIM_THRESHOLD:
                break
            cr = folder.media_resources[i]
            related_notes.append(cr.obsidian_note.get_name(cr.original_name))
        mr.obsidian_note.build_note(
            mr.transcript.text, links=links, highlights=highlights, name=mr.original_name, related_notes=related_notes, audio=audio_name)

        # create the markdown file
        mr.obsidian_note.save()

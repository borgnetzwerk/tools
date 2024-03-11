from __future__ import annotations
import argparse
import os
import json
import spacy
from spacy.cli.download import download
from flair.data import Sentence, Token
from flair.models import SequenceTagger
from flair.embeddings import WordEmbeddings, DocumentPoolEmbeddings
from collections import defaultdict
from typing import List, Dict, Union, Optional
import inspect
import numpy as np
import math
import re
import urllib.request
from mutagen.easyid3 import EasyID3
import importlib
from termcolor import colored
from pathlib import Path
import warnings


from ...review import similarity
from ...core import helper
from ...publish import util_wordcloud
from ...publish.Obsidian import nlped_whispered_folder
from ...extract import util_pdf
from ...extract import util_zotero
from ...extract import util_pytube
from ...extract.nlp.my_stop_words import MY_STOP_WORDS



def get_json_data(path):
    if os.path.exists(path) and os.path.splitext(path)[1] == ".json":
        try:
            with open(path, 'r', encoding='utf8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Could not load {path}: {str(e)}")
            return None


def dump_json(path, output_dict):
    with open(path, 'w', encoding='utf-8') as output_file:
        json.dump(output_dict, output_file, indent=4, ensure_ascii=False)


def data_to_attributes(instance, data, do_named_entities=True):
    if not isinstance(data, dict):
        return None
    words = None
    stops = None
    for key, value in data.items():
        if key == "bag_of_words":
            words = value
            continue
        elif key == "stop_words":
            stops = value
            continue
        if hasattr(instance, key):
            if key == "named_entities":
                if do_named_entities:
                    setattr(instance, key, NamedEntities(value))
                else:
                    setattr(instance, key, NamedEntities())
            else:
                setattr(instance, key, value)
    if words or stops:
        setattr(instance, "bag_of_words", BagOfWords(words=words, stops=stops))


class NLPTools:
    naming_conventions = {
        "en": {"spacy": "en_core_web_sm", "SequenceTagger": "ner", "WordEmbeddings": "glove"},
        "de": {"spacy": "de_core_news_sm", "SequenceTagger": "flair/ner-german", "WordEmbeddings": "de"},
        # add more languages and their naming conventions as needed
    }

    def __init__(self):
        self.STOP_WORDS = {}
        self.spacy = {}
        self.WordEmbeddings = {}
        self.DocumentPoolEmbeddings = {}
        self.SequenceTagger = {}

    def get_STOP_WORDS(self, language):
        if language in self.STOP_WORDS:
            return self.STOP_WORDS[language]
        stop_words_module = importlib.import_module(
            f"spacy.lang.{language}.stop_words")
        self.STOP_WORDS[language] = MY_STOP_WORDS[language].union(
            stop_words_module.STOP_WORDS)
        # TODO: Idea to allways include the english stop-words, since sometimes other languages use english as well
        return self.STOP_WORDS[language]

    def get_spacy(self, language):
        if language in self.spacy:
            return self.spacy[language]
        try:
            nlp_model = self.naming_conventions.get(
                language, {}).get("spacy", f"{language}_core_news_sm")
            try:
                self.spacy[language] = spacy.load(nlp_model)
            except OSError:
                download(model=nlp_model)
                self.spacy[language] = spacy.load(nlp_model)

            stop_words = self.get_STOP_WORDS(language)
            self.spacy[language].Defaults.stop_words |= set(stop_words)

            for word in self.get_STOP_WORDS(language):
                # todo: this does not seem to be enoguh, words with the same lemma get through
                # thought: this may be intended and will be left like this for now.
                for w in (word, word[0].capitalize(), word.upper()):
                    lex = self.spacy[language].vocab[w]
                    lex.is_stop = True
            return self.spacy[language]
        except Exception as e:
            print(f"Error loading spacy: {str(e)}")
            return None

    def get_WordEmbeddings(self, language):
        if language in self.WordEmbeddings:
            return self.WordEmbeddings[language]
        try:
            word_embeddings_model = self.naming_conventions.get(
                language, {}).get("WordEmbeddings", language)
            self.WordEmbeddings[language] = WordEmbeddings(
                word_embeddings_model)
            return self.WordEmbeddings[language]
        except Exception as e:
            print(f"Error loading WordEmbeddings for {language}: {str(e)}")
            return None

    def get_DocumentPoolEmbeddings(self, language):
        if language in self.DocumentPoolEmbeddings:
            return self.DocumentPoolEmbeddings[language]
        try:
            self.DocumentPoolEmbeddings[language] = DocumentPoolEmbeddings(
                [self.get_WordEmbeddings(language)])
            return self.DocumentPoolEmbeddings[language]
        except Exception as e:
            print(
                f"Error loading DocumentPoolEmbeddings for {language}: {str(e)}")
            return None

    def get_SequenceTagger(self, language):
        if language in self.SequenceTagger:
            return self.SequenceTagger[language]
        try:
            sequence_tagger_model = self.naming_conventions.get(
                language, {}).get("SequenceTagger", f"flair/ner-{language.lower()}")
            self.SequenceTagger[language] = SequenceTagger.load(
                sequence_tagger_model)
            return self.SequenceTagger[language]
        except Exception as e:
            print(f"Error loading SequenceTagger for {language}: {str(e)}")
            return None


class BagOfWords:
    def __init__(self, words: Dict[str, int] = None, stops: Dict[str, int] = None, tf: Dict[str, float] = None, tf_idf: Dict[str, float] = None, text=None, nlptools=None, language=None):
        self.words = words or defaultdict(int)
        self.stops = stops or defaultdict(int)
        self.tf = tf or {}
        self.tf_idf = tf_idf or {}

        if self.words and language:
            self.update_stops(language, nlptools)

        if text:
            self.from_nlp_text(text, language, nlptools)

    def __len__(self):
        return len(self.words)

    def calc_tf(self):
        total = sum(self.words.values())
        self.tf = {word: count / total for word, count in self.words.items()}
        self.sort(do_words=False, do_tf=True)
        return self.tf

    def calc_tf_idf(self, idf: Dict[str, float]):
        self.tf_idf = {word: frequency * idf[word]
                       for word, frequency in self.get_tf().items()}
        self.sort(do_words=False, do_tf_idf=True)
        return self.tf_idf

    def get_tf(self):
        if not self.tf:
            return self.calc_tf()
        return self.tf

    def get_tf_idf(self, idf: Dict[str, float] = None):
        if not self.tf_idf and idf:
            return self.calc_tf_idf(idf)
        return self.tf_idf

    def sort(self, do_words=True, do_tf=False, do_tf_idf=False):
        if do_words:
            if len(self.words):
                # self.words = {k: v for k, v in sorted(self.words.items(),
                #   key=lambda x: x[1], reverse=True)}
                self.words = dict(
                    sorted(self.words.items(), key=lambda x: (-x[1], x[0])))

            if len(self.stops):
                # self.stops = {k: v for k, v in sorted(self.stops.items(),
                #   key=lambda x: x[1], reverse=True)}
                self.stops = dict(
                    sorted(self.stops.items(), key=lambda x: (-x[1], x[0])))
        if do_tf:
            if len(self.tf):
                self.tf = dict(
                    sorted(self.tf.items(), key=lambda x: (-x[1], x[0])))
        if do_tf_idf:
            if len(self.tf_idf):
                self.tf_idf = dict(
                    sorted(self.tf_idf.items(), key=lambda x: (-x[1], x[0])))

    def get(self):
        return self.words

    def add(self, other):
        for word, count in other.words.items():
            if word in self.words:
                self.words[word] += count
            else:
                self.words[word] = count

    def from_nlp_text(self, nlp_text, language=None, nlpTools=None):
        for token in nlp_text:
            if token.is_alpha:
                word = token.lemma_.lower()
                if token.is_stop:
                    self.stops[word] += 1
                else:
                    self.words[word] += 1
        self.update_stops(language=language, nlptools=nlpTools)
        self.sort()

    def update_stops(self, language, nlptools: NLPTools = None):
        def special_stop_rules(key, vocab):
            if len(key) < 2:
                return True
            if not key.isalpha() and key not in vocab:
                if len(re.findall('[a-zA-Z\d]', key)) < 2:
                    return True
            # way to harsh, not every word is in (that language's) vocab
            # if key not in vocab:
            #     return True
            return False

        nlptools = nlptools or NLPTools()
        to_stop = []
        to_bag = []
        vocab = nlptools.get_spacy(language).vocab
        for key in self.words.keys():
            if key in vocab and vocab[key].is_stop:
                to_stop.append(key)
            elif special_stop_rules(key, vocab):
                to_stop.append(key)
        for key in self.stops.keys():
            if key in vocab and not vocab[key].is_stop:
                to_bag.append(key)
        for key in to_stop:
            self.stops[key] = self.words.pop(key)
        for key in to_bag:
            self.words[key] = self.stops.pop(key)
        self.sort()
        return len(to_bag) + len(to_stop)

    # bag_of_words = {k: v for k, v in sorted(bag_of_words.items(), key=lambda item: item[1], reverse=True)}


class NamedEntities:
    def __init__(self, entities: Dict[str, List[str]] = None, text=None,):
        self.entities = entities or {}

        if text:
            self.from_nlp_text(text)

    def __len__(self):
        return len(self.entities)

    def sort(self):
        if not self.entities:
            return
        val = list(self.entities.values())[0]
        if isinstance(val, list):
            self.entities = {k: v for k, v in sorted(
                self.entities.items(), key=lambda item: len(item[1]), reverse=True)}
        if isinstance(val, int):
            self.entities = {k: v for k, v in sorted(
                self.entities.items(), key=lambda item: item[1], reverse=True)}

    def add(self, other, path=None):
        for key, value in other.entities.items():
            if path:
                path = os.path.basename(path)
                value = [f"{path}: {x}" for x in value]
            if key in self.entities:
                self.entities[key] += value
            else:
                self.entities[key] = value

    def update(self):
        move_to = {}
        for key in self.entities.keys():
            if key.lower() == key:
                for other_key in self.entities.keys():
                    if other_key != key and other_key.lower() == key:
                        move_to[key] = other_key
                        break
        for source, dest in move_to.items():
            if isinstance(self.entities[dest], list):
                self.entities[dest] += self.entities[source]
            else:
                self.entities[dest].update(self.entities[source])
            del self.entities[source]

    def get(self):
        return self.entities

    def get_frequencies(self):
        return {k: len(v) for k, v in self.entities.items()}

    def from_nlp_text(self, sentence):
        for entity in sentence.get_spans('ner'):
            rep = f"Span[{entity.start_position}:{entity.end_position}]: {entity.tag} ({round(entity.score, 2)})"
            if entity.text in self.entities:
                self.entities[entity.text].append(rep)
            else:
                self.entities[entity.text] = [rep]
        self.sort()

# File classes


class Transcript:
    def __init__(self, path=None, text=None, segments=None, language=None):
        """
        A class representing a transcript.

        Args:
            text (str): Text content of the transcript.
            path (str): Path to the transcript file.

        Attributes:
            text (str): Text content of the transcript.
            path (str): Path to the transcript file.
        """
        self.path: str = path
        self.text: str = text
        # todo: eventually have a "clean_text" variable
        self.language: str = language
        self.segments: Dict[str, str] = segments
        if path:
            self.from_file()

    def get_manageable_text_sizes(self):
        text = self.text
        pieces = []
        jump = 50000

        if len(text) < jump * 2:
            pieces = [text]
        else:
            # Break text into smaller chunks so we have enough memory to solve it
            # FIXME: doesn't properly break
            candidates = ["\n\n", "\n", ".", "!", "?", ",", " "]

            begin = 0
            end = jump
            while end < len(text):
                next_stop = 0
                for fi in candidates:
                    pos = text[begin + jump:end + jump].find(fi)
                    if pos >= 0 and pos <= jump * 2:
                        next_stop = pos
                        break
                end = begin + jump + next_stop + 1
                pieces.append(text[begin:end])
                begin = end
            pieces.append(text[begin:])
        return pieces

    def from_file(self, path=None):
        """
        Load transcript from the given path.

        Args:
            path (str): Path to the transcript file.
        """
        if path is None:
            path = self.path
        else:
            self.path = path
        if not path:
            print("need path to load Transcript")
            return None
        data = get_json_data(path)
        data_to_attributes(self, data)

    def iscomplete(self):
        if self.path and self.text:
            return True
        return False

    def complete(self, path=None):
        if not self.iscomplete() and path:
            self.from_file(path)
        else:
            print("missing path to load transcript")
        return self.iscomplete()

    def get_dict(self):
        return {
            'text': self.text,
            'segments': self.segments,
            'language': self.language
        }

    def get(self, attr: str):
        if attr == "dict":
            return self.get_dict()
        elif hasattr(self, attr):
            return getattr(self, attr)

    def clean(self):
        if self.text and self.text.startswith("1\n00:00:"):
            # is vtt transcript
            # make sure empty vtt lines are not "truly" emtpy
            self.text = self.text.replace("\n\n\n", "\n \n\n")
            segments = self.text.split("\n\n")
            sentences = [s.split("\n")[2] for s in segments]
            # todo: detect when speaker is given like "Speaker a: ..."
            speaker_splitter = [":", "]"]
            for s_c in speaker_splitter:
                openings = defaultdict(int)
                for sentence in sentences:
                    pieces = sentence.split(s_c)
                    if len(pieces) > 1:
                        openings[pieces[0]] += 1

                speakers = False
                # see if there are regular speakers:
                for opening, count in openings.items():
                    if count > 5:
                        speakers = True
                if speakers:
                    for idx, sentence in enumerate(sentences):
                        pieces = sentence.split(s_c)
                        if len(pieces) > 1:
                            pieces.pop(0)
                        sentences[idx] = s_c.join(pieces)
            sentences = [s for s in sentences if s.count(" ") != len(s)]
            self.text = " ".join(sentences)

        elif "\n" in self.text:
            self.text = self.text.replace("-\n", "")
            self.text = self.text.replace("\n", " ")


class Audio:
    def __init__(self, path=None, metadata=None):
        self.path = path
        self.metadata = metadata
        if self.path:
            try:
                self.metadata = EasyID3(path)
            except:
                pass

    def get(self, arg=None):
        if arg == "path":
            return self.path
        elif arg == "title":
            return os.path.splitext(os.path.basename(self.path))[0]
        elif arg:
            return self.metadata.get(arg)
        else:
            return self.metadata

    def get_dict(self):
        return self.metadata.items()


class NLPFeatureAnalysis:
    def __init__(self, path=None, bag_of_words=None, named_entities=None, nlptools: NLPTools = None, transcript: Transcript = None, do_named_entities=True):
        """
        A class representing NLP feature analysis.

        Args:
            bag_of_words (dict): A dictionary representing bag of words.
            named_entities (list): A list of named entities.
            tf_idf (dict): A dictionary representing tf-idf values.

        Attributes:
            bag_of_words (dict): A dictionary representing bag of words.
            named_entities (list): A list of named entities.
            tf_idf (dict): A dictionary representing tf-idf values.
        """
        self.path: str = path
        self.bag_of_words: BagOfWords = bag_of_words or BagOfWords()
        self.named_entities: NamedEntities = named_entities or NamedEntities()
        if path:
            self.from_file(path, do_named_entities=do_named_entities)
        if transcript and transcript.text:
            self.complete(transcript, nlptools,
                          do_named_entities=do_named_entities)

    def from_file(self, path: str = None, do_named_entities: bool=True) -> None:
        """
        Load transcript from the given path.

        Args:
            path (str): Path to the transcript file.
        """
        if path is None:
            path = self.path
        else:
            self.path = path
        data = get_json_data(path)
        data_to_attributes(self, data, do_named_entities)

    def iscomplete(self) -> bool:
        if self.bag_of_words.get() and self.named_entities.get():
            return True
        return False

    def complete(self, transcript: Transcript, nlptools: NLPTools = None, do_named_entities: bool = True) -> bool:
        """Processes a JSON file containing text and returns a Document object.

        Args:
            json_path (str): The path to the input JSON file.

        Returns:
            Document: The Document object representing the input text.
        """
        nlptools = nlptools or NLPTools()

        changes = False
        if not self.iscomplete():
            changes = True
        if not transcript or not transcript.text:
            print("No Text in: " + self.path)
            return False
        transcript.clean()
        if do_named_entities:
            self.fill_named_entities(transcript, nlptools)
        self.fill_bag_of_words(transcript, nlptools)

        # create a Document object and return it
        entity_change = self.named_entities.update()
        BagOfWords_change = self.bag_of_words.update_stops(
            transcript.language, nlptools)
        if changes or BagOfWords_change or entity_change:
            self.save(should_have_nen=do_named_entities)
        return self.iscomplete()

    def fill_bag_of_words(self, transcript: Transcript, nlptools: NLPTools = None) -> Union[BagOfWords, bool]:
        if not self.bag_of_words.get():
            nlptools = nlptools or NLPTools()
            if not transcript.iscomplete():
                print("You need a text in a known language to complete " + self.path)
                return False
            # create a Sentence object from the text

            bow = BagOfWords()

            for text in transcript.get_manageable_text_sizes():
                doc = nlptools.get_spacy(transcript.language)(text)

                bow.add(BagOfWords(
                    text=doc, nlptools=nlptools, language=transcript.language))

            # get the bag of words and non-stop-words
            self.bag_of_words = bow
            return self.bag_of_words
        else:
            self.bag_of_words.update_stops(
                language=transcript.language, nlptools=nlptools)
            return False

    def fill_named_entities(self, transcript: Transcript, nlptools: NLPTools = None) -> Union[NamedEntities, bool]:
        if not self.named_entities.get():
            nlptools = nlptools or NLPTools()
            if not transcript.iscomplete():
                print("You need a text in a known language to complete " + self.path)
                return False

            nen = NamedEntities()

            for text in transcript.get_manageable_text_sizes():
                sentence = Sentence(text)

                nlptools.get_DocumentPoolEmbeddings(
                    transcript.language).embed(sentence)

                # get the named entities
                # todo: Worked
                nlptools.get_SequenceTagger(
                    transcript.language).predict(sentence)
                nen.add(NamedEntities(text=sentence))
            self.named_entities = nen
            return self.named_entities
        else:
            return False

    def get_dict(self) -> dict:
        # Todo: consider writing 'tf' to file as well.
        return {
            'bag_of_words': self.bag_of_words.words,
            'tf_idf': self.bag_of_words.get_tf_idf(),
            'named_entities': self.named_entities.get(),
            'stop_words': self.bag_of_words.stops
        }

    def save(self, path: Optional[str] = None, should_have_nen: bool = True) -> None:
        if path is None:
            path = self.path
        output_dict = self.get_dict()

        if len(self.bag_of_words.words) == 0:
            print(f"No {colored('words', 'red')} in file: " + path)
        elif len(self.named_entities) == 0 and should_have_nen:
            print(f"No {colored('named entities', 'red')} in file: " + path)
        dump_json(path, output_dict)


class ResearchQuestion:
    def __init__(self, title: str = None, path: str = None, keywords: dict[str, int] = None, queries: dict[str, str] = None):
        self.path: str = None
        self.title: str = title
        self.keywords: dict[str, int] = keywords
        self.queries: dict[str, str] = queries
        self.tag: str = None

    def from_file(self, path: str = None):
        if path is None:
            path = self.path
        else:
            self.path = path
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines or not lines[0].startswith("RQ::"):
                return None
        while "\n" in lines:
            lines.remove("\n")
        while "```\n" in lines:
            lines.remove("```\n")
        self.title = lines.pop(0).strip().split("::")[1].strip()

        # self.tag = helper.get_clean_title(
        #     self.title, obsidian=True).replace(" ", "_")
        self.tag = Path(path).stem
        for char in [" ", ":", ",", ";", "."]:
            self.tag = self.tag.replace(char, "_")

        tag_found = False

        self.keywords = {}
        self.queries = {}
        in_keywords = False
        in_queries = False
        current_name = ""
        current_group = {}
        current_query = ""

        for line in lines:
            if self.tag in line:
                tag_found = True
            if line.startswith("## "):
                if in_keywords:
                    if current_name:
                        self.keywords[current_name] = current_group
                        current_name = ""
                        current_group = {}
                    in_keywords = False
                    in_queries = True
                elif in_queries:
                    if current_name:
                        self.queries[current_name] = current_query
                        current_name = ""
                        current_query = ""
                    in_queries = False
                    # whatever_comes_next = True
                else:
                    in_keywords = True
            elif in_keywords:
                if line.startswith("### "):

                    if current_name:
                        self.keywords[current_name] = current_group
                        current_name = ""
                        current_group = {}
                    current_name = line.strip().split(
                        "::")[0].split("### ")[1].lower()
                else:
                    keyword, weight = line.strip().split("::")
                    current_group[keyword.lower().strip()] = int(
                        weight.strip())
            elif in_queries:
                if line.startswith("### "):
                    if current_name:
                        self.queries[current_name] = current_query
                        current_name = ""
                        current_query = ""
                    current_name = line.strip().split("::")[0].split("### ")[1]
                else:
                    current_query += line.strip()

        if not tag_found:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"""
# Results
```dataview
Table
notes_for_{self.tag} as "Notes for {self.tag}"
from "03_notes"
where notes_for_{self.tag}
SORT notes_for_{self.tag} DESC
LIMIT 100
```
    
# Files
```dataview
Table
{self.tag} as "Fit"
from "03_notes"
SORT {self.tag} DESC
LIMIT 100
```
""")
        if current_name:
            self.queries[current_name] = current_query
            current_name = ""
            current_query = ""
        # creation successful
        return True

    def get_total_note(research_questions):
        pieces = []
        tags = []
        for i, key in enumerate(research_questions):
            tags.append(key.tag)
            pieces.append(f"{key.tag} as RQ{i+1}")
        rq_sum = " + ".join(tags)
        pieces.append(f"round({rq_sum},3) as \"Sum\"")
        total_cols = ", ".join(pieces)
        total_sort = f"SORT {rq_sum} desc"

        note = f"""## Research Questions
```dataview
Table
RQ as "RQ"
where RQ
SORT file.name
```

## Done
```dataview
Table
{total_cols}
From "03_notes"
{total_sort}
WHERE !contains(file.tasks.completed,false)
LIMIT 100
```

## Modified
```dataview
Table
{total_cols}
From "03_notes"
{total_sort}
WHERE contains(file.tasks.completed,true) AND contains(file.tasks.completed,false)
LIMIT 100
```

## Best Candidates
```dataview
Table
{total_cols}
From "03_notes"
{total_sort}
WHERE !contains(file.tasks.completed,true)
LIMIT 100
```
"""
        return note


class MediaResource:
    """
    A class representing a media resource.

    Args:
        audio_file (Audiofile): An instance of Audiofile.
        transcript (Transcript): An instance of Transcript.
        nlp_analysis (NLPFeatureAnalysis): An instance of NLPFeatureAnalysis.

    Attributes:
        audio_file (Audiofile): An instance of Audiofile.
        transcript (Transcript): An instance of Transcript.
        nlp_analysis (NLPFeatureAnalysis): An instance of NLPFeatureAnalysis.
    """

    def __init__(self, nlptools: NLPTools = None):
        self.audio_file: Audio = None
        self.transcript: Transcript = None

        self.pdf: util_pdf.PDFDocument = None

        # todo: make this an actual class
        self.image: str = None
        self.info: util_pytube.YouTubeInfo = None

        self.nlp_analysis: NLPFeatureAnalysis = None

        self.obsidian_note: nlped_whispered_folder.ObsidianNote = None

        self.basename: str = None
        self.original_name: str = None
    
    def is_duplicate(self, mr:MediaResource):
        common_fields = ["basename", "original_name"]
        pdf_fields = ["title", "author", "year"]

        common_equals = sum(mr.get(field) == self.get(field) for field in common_fields)
        pdf_equals = sum(mr.pdf.get(field, None_if_not_found=True) == self.pdf.get(field, None_if_not_found=True) for field in pdf_fields)

        if common_equals >= 2:
            return True
        elif pdf_equals >= 3:
            return True
        elif common_equals >= 1 + pdf_equals >= 2:
            return True
        return False

    def add_audio(self, path: str = None, file: Audio = None):
        if file:
            self.audio_file = file
        elif path:
            self.audio_file = Audio(path)
        self.search_original_name()

    def add_transcript(self, path: str = None, file: Transcript = None):
        if file:
            self.transcript = file
        elif path:
            self.transcript = Transcript(path)

    def add_info(self, path: str = None, file: util_pytube.YouTubeInfo = None):
        if file:
            self.info = file
        elif path:
            self.info = util_pytube.YouTubeInfo(path=path)

    def add_pdf(self, path: str = None, file: util_pdf.PDFDocument = None):
        if file:
            self.pdf = file
        elif path:
            self.pdf = util_pdf.PDFDocument(path)
        self.search_original_name()

    def add_NLPFeatureAnalysis(self, path: str = None, file: NLPFeatureAnalysis = None, nlptools: NLPTools = None, do_named_entities=True):
        if file:
            self.nlp_analysis = file
        elif path:
            if self.pdf:
                text_container = self.pdf
            elif self.transcript:
                text_container = self.transcript
            else:
                print(
                    f"Lacking text basis, can't add NLPFeatureAnalysis for file {self.basename}")
                return None
            self.nlp_analysis = NLPFeatureAnalysis(
                path, nlptools=nlptools, transcript=text_container, do_named_entities=do_named_entities)

    def add_image(self, path: str = None):
        if path:
            self.image = path

    def add_obsidian_note(self, path: str = None, file: nlped_whispered_folder.ObsidianNote = None):
        if file:
            self.obsidian_note = file
        elif path:
            self.obsidian_note = nlped_whispered_folder.ObsidianNote(path)
        else:
            self.obsidian_note = nlped_whispered_folder.ObsidianNote()

    def search_original_name(self, force=False):
        if self.original_name and not force:
            return self.original_name
        candidates = []
        if self.pdf:
            candidates.append(self.pdf.get("title"))
        if self.audio_file:
            candidates.append(self.audio_file.get("title"))
        if candidates:
            self.original_name = candidates[0]
            return self.original_name

    def iscomplete(self):
        return self.transcript.iscomplete() and self.nlp_analysis.iscomplete()

    def complete(self, nlptools: NLPTools = None, do_named_entities=True):
        """Processes a JSON file containing text and returns a Document object.

        Args:
            json_path (str): The path to the input JSON file.

        Returns:
            Document: The Document object representing the input text.
        """
        nlptools = nlptools or NLPTools()

        self.transcript.complete()
        self.nlp_analysis.complete(
            nlptools, do_named_entities=do_named_entities)

    def get_dict(self):
        # TODO: check if this throws errors, else revert
        # return dict(self.audio_file.get_dict()) | self.transcript.get_dict() | self.nlp_analysis.get_dict()
        result_dict = {}
        for key in self.__dict__:
            attr = getattr(self, key)
            try:
                # todo: remove all get_dicts
                if hasattr(attr, 'get_dict'):
                    result_dict |= attr.get_dict()
                elif hasattr(attr, 'get') and callable(attr.get):
                    result_dict |= attr.get('dict')
            except:
                continue
        return result_dict

    def get(self, parameter):
        if parameter == 'text':
            if self.pdf is not None:
                return self.pdf.get("text")
            elif self.transcript is not None:
                return self.transcript.get("text")
            else:
                return None
        elif parameter == 'url':
            return self.url
        elif parameter == 'dict':
            return self.get_dict()
        elif parameter == 'basename':
            if self.basename:
                return self.basename
            else:
                path = None
                if self.nlp_analysis:
                    path = self.nlp_analysis.path
                elif self.pdf:
                    path = self.pdf.path
                elif self.audio_file:
                    # todo: check if this was ment to be called "self.audio_file.path"
                    path = self.audio_file.path
                elif self.info:
                    path = self.info.path
                if path:
                    self.basename = os.path.splitext(os.path.basename(path))[0]
                    return self.basename
                else:
                    warnings.warn("Could not build basename")
                    return None
        elif parameter == 'type':
            return self.__class__.__name__
        elif hasattr(self, parameter):
            return getattr(self, parameter)
        else:
            raise ValueError(f"Invalid parameter '{parameter}'")


class Subfolder:
    folder_formats = {
        "blank": [],
        # 00 Input
        "00_PDFs": [".pdf"],
        "00_audios": [".mp3", ".mp4"],
        "00_images": [".png", ".jpg", ".jpeg"],
        "00_infos": [".json"],
        "00_RQs": [".md", ".json"],
        # 01 Extract
        "01_whisper": [".json"],  # todo: vtt
        # 02 Analyse
        # todo: renaming from _processed
        "02_nlp": [".json", "_processed.json"],
        # 03 Publish
        "03_notes": [".md"],
    }

    def __init__(self, folder_path, type="blank"):
        self.path = os.path.join(folder_path, type)
        os.makedirs(self.path, exist_ok=True)
        self.type = type
        self.endings = self.folder_formats[type]
        if type == "00_PDFs":
            self.BibResources = util_zotero.BibResources(folder_path)
        if type == "00_RQs":
            self.research_questions: list[ResearchQuestion] = None
            self.get("research_questions")
            
    def lookfor(self, filename):
        path_found = []
        path_suggested = []
        basename = os.path.basename(filename)
        stem = os.path.splitext(basename)[0]
        for ending in self.endings:
            path = os.path.join(self.path, stem + ending)
            if os.path.exists(path):
                path_found.append(path)
            else:
                path_suggested.append(path)
        best_fit = path_found[0] if path_found else path_suggested[0] if path_suggested else None
        return best_fit
        # return found, not_found

    def get(self, arg: str = None):
        if arg.lower() == "rqs" or arg.lower() == "research_questions":
            if self.research_questions:
                return self.research_questions
            files = self.get("files")
            if not files:
                return None
            else:
                non_RQ = []
                if not self.research_questions:
                    self.research_questions: list[ResearchQuestion] = []
                for file in self.get("files"):
                    rq = ResearchQuestion()
                    if rq.from_file(os.path.join(self.path, file)):
                        self.research_questions.append(rq)
                    else:
                        non_RQ.append(file)
                for file in non_RQ:
                    if file.startswith("Total"):
                        with open(os.path.join(self.path, file), "w", encoding="utf8") as f:
                            f.write(ResearchQuestion.get_total_note(
                                self.research_questions))
                return self.research_questions
        elif arg == "files":
            return os.listdir(self.path)


class Folder:
    """A class to represent a folder containing multiple Document instances.

    Attributes:
        documents (List[Document]): A list of Document instances contained in the folder.
        stop_words (defaultdict(int)): A defaultdict with stop words as keys and their total count across
            all documents as values.
        bag_of_words (defaultdict(int)): A defaultdict with words as keys and their total count across all
            documents as values.
        named_entities (Dict[str, List[str]]): A dictionary with named entities as keys and their occurrences in
            the documents as values.
        paths (Dict[str, str]): A dictionary of paths to subfolders.

    Methods:
        add_document(document: Document) -> None: Adds a Document instance to the folder.
        populate() -> None: Populates the stop_words, bag_of_words and named_entities attributes by aggregating
            the counts and occurrences of the respective attributes in all documents.
        save(output_path: str) -> None: Saves the Folder instance to a JSON file at the specified output path.
    """

    # Define paths as a class-level property

    def __init__(self, folder_path, nlptools=None, language=None, media_resources: List[MediaResource] = None, publish=False):
        self.path = folder_path

        self.audio = Subfolder(folder_path, "00_audios")
        self.pdf = Subfolder(folder_path, "00_PDFs")
        self.image = Subfolder(folder_path, "00_images")
        self.infos = Subfolder(folder_path, "00_infos")
        self.rq = Subfolder(folder_path, "00_RQs")
        self.whisper = Subfolder(folder_path, "01_whisper")
        self.analyse = Subfolder(folder_path, "02_nlp")
        self.notes = Subfolder(folder_path, "03_notes")

        self.media_resources: List[MediaResource] = media_resources or []
        self.added_docs = set()
        # todo: if media_resources, maybe fill set?

        self.bag_of_words = BagOfWords()
        self.named_entities = NamedEntities()

        self.df = defaultdict(int)
        self.idf = defaultdict(int)
        self.sim_matrix = None
        self.statdict = {}
        
        if nlptools:
            self.process(nlptools)
        if publish:
            self.publish()

    def get_image(self):
        candidates = []
        if self.image and self.image.path:
            candidates = os.listdir(self.image.path)
        if candidates:
            return os.path.join(self.image.path, candidates[0])

        for mr in self.media_resources:
            if mr.image:
                if os.path.exists(mr.image):
                    return mr.image
            if mr.info:
                if mr.info.thumbnail_urls:
                    # handle "if not mr.image"
                    file_path = mr.image
                    urllib.request.urlretrieve(
                        mr.info.thumbnail_urls[-1], file_path)

                    return file_path

    def calc_sim_matrix(self):
        # bag_sim_mat = similarity.compute_similarity_matrix(
        #     [doc.bag_of_words.get() for doc in self.documents], self.bag_of_words.get())

        bag_sim_mat = similarity.compute_similarity_matrix(
            [mr.nlp_analysis.bag_of_words.tf_idf for mr in self.media_resources], self.bag_of_words.get())

        # todo: option to eventually weigh named entities differently
        # nam_sim_mat = similarity.create_word_vectors(
        #     [doc.named_entities.get() for doc in self.documents], self.named_entities)
        self.sim_matrix = bag_sim_mat
        similarity.print_sim_matrix(self.sim_matrix, self.path)
        for mr in self.media_resources:
            should_have_nen = True
            if not mr.transcript:
                should_have_nen = False
            mr.nlp_analysis.save(should_have_nen=should_have_nen)

    def calc_rq_sim(self):
        if not self.rq.research_questions:
            return None

        def get_min_match(words: list[str], match_dict: dict[str, float]):
            found = []
            for word in words:
                if "-" in word:
                    value = 0
                    if word in mr.nlp_analysis.bag_of_words.tf:
                        value += mr.nlp_analysis.bag_of_words.tf[word]
                    synonyms = [
                        word.replace("-", " "),
                        word.replace("-", "")
                    ]
                    for syn in synonyms:
                        if syn in mr.nlp_analysis.bag_of_words.tf:
                            value += mr.nlp_analysis.bag_of_words.tf[syn]
                    splits = word.split("-")
                    value += get_min_match(splits, match_dict)
                    if value:
                        found.append(value)
                    else:
                        found = None
                        break
                else:
                    if word in mr.nlp_analysis.bag_of_words.tf:
                        found.append(
                            mr.nlp_analysis.bag_of_words.tf[word])
                    else:
                        found = None
                        break
            if found:
                return min(found)
            else:
                return 0

        relevant_keys = set()
        for rq in self.rq.get("rqs"):
            for group in rq.keywords.values():
                # todo: see
                relevant_keys.update(group)
                # for keyword in group:
                # relevant_keys.update(keyword.split(" "))
        reduced_research_questions = []
        for rq in self.rq.get("rqs"):
            res = {}
            ungrouped = {}
            for group in rq.keywords.values():
                ungrouped.update(group)
            for key in relevant_keys:
                value = 0
                if key in ungrouped:
                    # todo: utilize weight
                    value = ungrouped[key]
                    # value = 1
                res[key] = value
            reduced_research_questions.append(res)

        reduced_media_resources = []
        for mr in self.media_resources:
            res = {}
            for key in relevant_keys:
                # Todo: synonyms / related words
                key = key.lower()
                if key in mr.nlp_analysis.bag_of_words.tf:
                    res[key] = mr.nlp_analysis.bag_of_words.tf[key]
                else:
                    if " " in key:
                        subwords = key.split(" ")
                    else:
                        subwords = [key]
                    res[key] = get_min_match(
                        subwords, mr.nlp_analysis.bag_of_words.tf)
            reduced_media_resources.append(res)
        # TODO: calculate once per group, then again over all groups
        self.rq_sim_mat = similarity.compute_weighed_similarity(
            reduced_media_resources, reduced_research_questions)

        similarity.print_rq([mr.get("basename") for mr in self.media_resources], self.rq_sim_mat,
                            self.path, filename="RQ", additional_info=self.rq.research_questions)

    def add_media_resource(self, media_resource: MediaResource):
        if media_resource:
            self.media_resources.append(media_resource)

    def calc_idf(self):
        self.idf = {word: math.log(len(self.media_resources) / (frequency))
                    for word, frequency in self.df.items()}
        return self.idf

    def get_idf(self):
        if self.idf:
            return self.idf
        return self.calc_idf()

    def populate(self):
        for mr in self.media_resources:
            if mr.nlp_analysis.path not in self.added_docs:
                self.bag_of_words.add(mr.nlp_analysis.bag_of_words)
                self.named_entities.add(
                    mr.nlp_analysis.named_entities, mr.nlp_analysis.path)
                self.added_docs.add(mr.nlp_analysis.path)
                # document frequency
                for word in mr.nlp_analysis.bag_of_words.get().keys():
                    self.df[word] += 1

        for mr in self.media_resources:
            mr.nlp_analysis.bag_of_words.calc_tf_idf(self.get_idf())
        # self.bag_of_words.update_stops()
        self.named_entities.update()
        self.bag_of_words.sort()
        self.named_entities.sort()

    def get_dict(self):
        return {
            'bag_of_words': self.bag_of_words.words,
            'idf': self.idf,
            'named_entities': self.named_entities.get(),
            'stop_words': self.bag_of_words.stops,
            'documents': [os.path.basename(mr.nlp_analysis.path) for mr in self.media_resources]
        }

    def save(self, output_path=None, do_named_entities=True):
        if output_path is None:
            output_path = os.path.join(self.path, "rep_Folder")
        output_dict = self.get_dict()

        relevant = [len(self.media_resources), len(self.bag_of_words)]
        if do_named_entities:
            relevant.append(len(self.named_entities))

        if any(count == 0 for count in relevant):
            print("Error on Folder: " + output_path)
        dump_json(output_path, output_dict)

    def save_summary(self, output_path, do_named_entities=True):
        if not len(self.media_resources):
            print(f"No Documents found in folder: {output_path}")
            return None
        threshold = min(
            int(list(self.bag_of_words.get().values())[0] / 100), 10)
        threshold = max(threshold, 3)
        output_dict = {
            'bag_of_words': {k: v for k, v in list(self.bag_of_words.words.items())[:1000] if v >= threshold},
            'stop_words': {k: v for k, v in list(self.bag_of_words.stops.items())[:1000] if v >= threshold},
            'named_entities': {k: len(v) for k, v in list(self.named_entities.get().items())[:1000] if len(v) >= threshold},
            'documents': [os.path.basename(doc.nlp_analysis.path) for doc in self.media_resources]
        }

        relevant = [len(self.media_resources), len(self.bag_of_words)]
        if do_named_entities:
            relevant.append(len(self.named_entities))

        if any(count == 0 for count in relevant):
            print("Error on Folder: " + output_path)
        dump_json(output_path, output_dict)

    def process(self, nlptools=None):
        if nlptools is None:
            nlptools = NLPTools()
        audios = [os.path.join(self.audio.path, f)
                  for f in os.listdir(self.audio.path)]
        pdfs = self.pdf.BibResources.pdfs
        do_named_entities = False
        if audios:
            do_named_entities = True
            for idx, path in enumerate(audios):
                mr = MediaResource()
                mr.add_audio(path=path)
                mr.add_transcript(path=self.whisper.lookfor(path))
                mr.add_info(path=self.infos.lookfor(path))
                if not mr.transcript.text:
                    mr.transcript.text, mr.transcript.language = mr.info.get_transcript()
                mr.add_image(path=self.image.lookfor(path))
                # todo: eventually load thumbnails here
                mr.add_NLPFeatureAnalysis(
                    path=self.analyse.lookfor(path), nlptools=nlptools)

                mr.add_obsidian_note(path=self.notes.lookfor(path))
                self.add_media_resource(mr)
        if pdfs:
            for idx, path in enumerate(pdfs):
                mr = MediaResource()
                mr.add_pdf(path=path)
                metadata = mr.pdf.get_metadata()
                # TODO: Decide what is required here. For now, adding it without metadata.
                # if metadata == -1:
                #     # There was an error with the file
                #     continue
                mr.pdf.add_metadata(metadata)
                # # check if the file has already been added
                # checking here is to intensive
                mr.add_NLPFeatureAnalysis(path=self.analyse.lookfor(
                    path), nlptools=nlptools, do_named_entities=False)
                mr.add_obsidian_note(path=self.notes.lookfor(path))
                self.add_media_resource(mr)
                if idx % 100 == 99:
                    print(f"{idx+1} out of {len(pdfs)} added.")
            print(f"All {len(pdfs)} PDFs added.")

        # check if the file has already been added
        duplicates = set()
        for x, mir in enumerate(self.media_resources):
            if x in duplicates:
                continue
            for y in range(x+1, len(self.media_resources)):
                if y in duplicates:
                    continue
                if mir.is_duplicate(self.media_resources[y]):
                    print(f"Duplicates: {mir.basename}\n{mir.pdf.path}\n{self.media_resources[y].pdf.path}")
                    duplicates.add(y)
        # sort duplicates from highest to lowest
        duplicates = sorted(duplicates, reverse=True)
        for idx in duplicates:
            self.media_resources.pop(idx)
        print(f"Removed {len(duplicates)} duplicates.")

        if self.media_resources:
            self.populate()
            self.calc_sim_matrix()
            self.calc_rq_sim()
            self.save(os.path.join(self.path, "00_Folder.json"),
                      do_named_entities=do_named_entities)
            self.save_summary(os.path.join(
                self.path, "00_Folder_summary.json"), do_named_entities=do_named_entities)
            self.analyse_metadata()

    def analyse_metadata(self):

        class Stats:
            # Reward many high score media resources
            # Factor of 1 just adds the scores, 2 squares them, 3 cubes them, etc.
            # A higher factor rewards high scores more
            RANK_FACTOR = 2

            # Skip these in printing
            skip = ["rq_scores", "rq_score_list", "RANK_FACTOR", "skip"]


            def __init__(self, folder:Folder = None, mr_id:int = None):
                self.media_names = {}
                # create np array for rq scores with no length
                # create np array for rq scores with no length
                self.rq_score_list = []
                self.rq_scores = np.array([[]])
                self.rq_rank = 0
                self.media_num = 0
                if folder and mr_id:
                    self.update(folder, mr_id)
            
            # TypeError: Object of type Stats is not JSON serializable
            def to_dict(self):
                res_dict = {}
                for attr in dir(self):
                    if not attr.startswith('__') and not callable(getattr(self, attr)):
                        # TypeError: Object of type ndarray is not JSON serializable
                        if attr in Stats.skip:
                            continue
                        value = getattr(self, attr)
                        if isinstance(value, np.ndarray):
                            res_dict[attr] = value.tolist()
                        else:
                            res_dict[attr] = value
                return res_dict
            
            def to_csv(self, separator=";"):
                sub_separtor = ","
                if separator == ",":
                    sub_separtor = ";"
                res_list = []
                for attr in dir(self):
                    if not attr.startswith('__') and not callable(getattr(self, attr)):
                        if attr in Stats.skip:
                            continue
                        value = getattr(self, attr)
                        if isinstance(value, np.ndarray):
                            value = value.tolist()
                        if isinstance(value, list):
                            # res_list.append("'" + f"' {sub_separtor} '".join(value) + "'")
                            res_list.append("'" + f"' {sub_separtor} '".join(str(v) for v in value) + "'")
                            # res_list.append(str(value))
                        elif isinstance(value, dict):
                            if attr == "media_names":
                                res_list.append("'" + f"' {sub_separtor} '".join([str(v) for v in value.values()]) + "'")
                            else:
                                res_list.append(json.dumps(value))
                        else:
                            res_list.append(str(value))
                # convert to string and join with separator
                return separator.join(res_list)
            
            def __str__(self):
                return str(self.to_dict())

            def update(self, folder:Folder, mr_id:int):
                self.media_names[mr_id] = folder.media_resources[mr_id].basename
                # update the self.rq_scores np array with the new rq scores
                self.media_num += 1
                # update the self.rq_scores np array with the new rq scores
                
                self.rq_score_list.append(folder.rq_sim_mat[mr_id])

                ## Reward many high score media resources
                new_mean = np.mean(folder.rq_sim_mat[mr_id])
                self.rq_rank += new_mean**Stats.RANK_FACTOR

            def calc(self):
                # calculate the self.rq_averages over all rq_scores columns
                self.rq_scores = np.array(self.rq_score_list)

                # calculate the self.rq_averages over all rq_scores columns
                self.rq_averages = np.mean(self.rq_scores, axis=0)
                self.rq_sums = np.sum(self.rq_scores, axis=0)
                self.rq_maxs = np.max(self.rq_scores, axis=0)
                self.rq_mins = np.min(self.rq_scores, axis=0)
                self.rq_stds = np.std(self.rq_scores, axis=0)
                self.rq_medians = np.median(self.rq_scores, axis=0)
                self.rq_variances = np.var(self.rq_scores, axis=0)

                # calculate the single values for averages, sumes, etc.
                self.rq_average = np.mean(self.rq_averages)
                self.rq_sum = np.sum(self.rq_sums)
                self.rq_max = np.max(self.rq_maxs)
                self.rq_min = np.min(self.rq_mins)                
                # # Those don't make sense:
                # self.rq_std = np.std(self.rq_stds)
                # self.rq_median = np.median(self.rq_medians)
                # self.rq_variance = np.var(self.rq_variances)
                
                # calculate a "rank" score that rewards high averages and quantities of media resources

        
        # # TODO: Why does this not work?
        # statdict:Dict[str,Dict[str,Stats]] = {
        statdict = {
            "year" : defaultdict(Stats),
            "author" : defaultdict(Stats),
            "journal" : defaultdict(Stats),
            # "language" : defaultdict(Stats),
            "ENTRYTYPE" : defaultdict(Stats),
        }
        synoyms = {
            "author" : ["authors"],
            "journal" : ["journaltitle", "venue", "booktitle"],
        }
        not_found = {}
        for key in statdict.keys():
            not_found[key] = set()
        for mr_id, mr in enumerate(self.media_resources):
            # Create a list of all authors / venues / years and their statistics
            if mr.pdf and mr.pdf.metadata:
                for key, stats in statdict.items():
                    stat_key = mr.pdf.metadata.get(key)
                    if not stat_key:
                        for syn in synoyms.get(key, []):
                            stat_key = mr.pdf.metadata.get(syn)
                            if stat_key:
                                break
                    if stat_key:                        
                        if key == "author":
                            authors = stat_key.split(" and ")
                            for author in authors:
                                stats[author].update(self, mr_id)
                        else:
                            stats[stat_key].update(self, mr_id)
                    else:
                        not_found[key].update(list(mr.pdf.metadata.keys()))

        for key, stats in statdict.items():
            for name, stat in stats.items():
                stat.calc()
        
        for key, values in not_found.items():
            ignore = list(statdict.keys())
            ignore = ignore + ["file", "url", "urldate", "ID", "title"]
            for ignore_key in ignore:
                if ignore_key in values:
                    values.remove(ignore_key)
            print(f"No {colored(key, 'red')} in metadata, but found:\n{values}")

        for key, stats in statdict.items():
            # sort stats by rq_rank
            statdict[key] = dict(sorted(stats.items(), key=lambda x: x[1].rq_rank, reverse=True))
        
        # print statdict to json and csv
        for category, entry_dict in statdict.items():
            res_dict = {}
            for name, stat in entry_dict.items():
                res_dict[name] = stat.to_dict()
            dump_json(os.path.join(self.path, f"metadata_stats_{category}.json"), res_dict)
        
        for category, entry_dict in statdict.items():
            first_stat = list(entry_dict.values())[0]
            headers = [attr for attr in dir(first_stat) if not attr.startswith('__') and not callable(getattr(first_stat, attr))]
            for header in Stats.skip:
                if header in headers:
                    headers.remove(header)
            headers = ["name"] + headers

            with open(os.path.join(self.path, f"metadata_stats_{category}.csv"), "w", encoding="utf8") as f:
                # Write headers to file
                f.write(";".join(headers) + "\n")

                for name, stat in entry_dict.items():
                    # Write data to file
                    f.write(f"{name};{stat.to_csv()}\n")

        # print the top 10 of each category to console, along with their rank, number of media resources and average rq score
        for key, stats in statdict.items():
            print(f"{key}:\t name,\t rq_rank,\t # of media_resources,\t rq_average")
        for i, (name, stat) in enumerate(list(stats.items())[:10]):
            print(f"{i+1}. {name}:\t {round(stat.rq_rank, 3)} \t- {len(stat.media_names)} \t- {round(stat.rq_average,3)}")

        self.statdict = statdict

    def publish(self):
        if self.media_resources:
            try:
                self.wordcloud()
            except:
                print("Publish to Wordcloud failed")
            # Obsidian
            try:
                nlped_whispered_folder.folder(self, force=True)
            except:
                print("Publish to Obsidian failed")


    # Wordcloud
    def wordcloud(self):
        util_wordcloud.generate_wordcloud(
            self.bag_of_words.get(), os.path.join(self.path, "00_bag_of_words"))
        util_wordcloud.generate_wordcloud(
            self.named_entities.get_frequencies(), os.path.join(self.path, "00_named_entities"))
        found, not_found = self.image.lookfor("Folder")
        if found:
            mask = found[0]
            not_found = not_found[0]
        mask = util_wordcloud.generate_mask()
        util_wordcloud.generate_wordcloud_mask(
            self.bag_of_words.get(), mask, os.path.join(self.path, "00_bag_of_words_mask"))
        util_wordcloud.generate_wordcloud_mask(
            self.named_entities.get_frequencies(), mask, os.path.join(self.path, "00_named_entities"))


def main(input_path, output_path=None):
    if os.path.isfile(input_path):
        # process single file
        return MediaResource(paths={"transcript_file_path": input_path})
    elif os.path.isdir(input_path):
        # process all files in directory
        return Folder(input_path)
    else:
        print('Invalid input path.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process JSON files and extract document features.')
    parser.add_argument(
        'input', help='path to JSON file or folder of JSON files')
    parser.add_argument(
        '-o', '--output', help='path to output file or folder (default: derived from input path)')
    args = parser.parse_args()

    main(args.input, args.output)

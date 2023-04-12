import argparse
import os
import json
import spacy
from flair.data import Sentence, Token
from flair.models import SequenceTagger
from flair.embeddings import WordEmbeddings, DocumentPoolEmbeddings
from collections import defaultdict
from typing import List, Dict
import inspect
import review.similaritiy as similarity
import core.helper as helper
import numpy as np
import math
from termcolor import colored
from publish import util_wordcloud
from publish.Obsidian import nlped_whispered_folder

from mutagen.easyid3 import EasyID3
import importlib

from extract.nlp.my_stop_words import MY_STOP_WORDS

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


def data_to_attributes(instance, data):
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
                setattr(instance, key, NamedEntities(value))
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

        if text:
            self.from_nlp_text(text, language, nlptools)

    def __len__(self):
        return len(self.words)

    def calc_tf(self):
        total = sum(self.words.values())
        self.tf = {word: count/total for word, count in self.words.items()}
        self.sort(do_words=False, do_tf=True)
        return self.tf

    def calc_tf_idf(self, idf: Dict[str, float]):
        self.tf_idf = {word: frequency*idf[word]
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
                self.words = dict(sorted(self.words.items(), key=lambda x: (-x[1], x[0])))

            if len(self.stops):
                # self.stops = {k: v for k, v in sorted(self.stops.items(),
                                                    #   key=lambda x: x[1], reverse=True)}
                self.stops = dict(sorted(self.stops.items(), key=lambda x: (-x[1], x[0])))
        if do_tf:
            if len(self.tf):
                self.tf = dict(sorted(self.tf.items(), key=lambda x: (-x[1], x[0])))
        if do_tf_idf:
            if len(self.tf_idf):
                self.tf_idf = dict(sorted(self.tf_idf.items(), key=lambda x: (-x[1], x[0])))

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
        nlptools = nlptools or NLPTools()
        to_stop = []
        to_bag = []
        for key in self.words.keys():
            vocab = nlptools.get_spacy(language).vocab
            if key in vocab and vocab[key].is_stop:
                to_stop.append(key)
        for key in self.stops.keys():
            if key in vocab and not vocab[key].is_stop:
                to_bag.append(key)
        for key in to_stop:
            self.stops[key] = self.words.pop(key)
        for key in to_bag:
            self.words[key] = self.stops.pop(key)
        self.sort()
        return len(to_bag)+len(to_stop)

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

    def merge(self, other, path=None):
        for key, value in other.entities.items():
            if path:
                path = os.path.basename(path)
                value = [f"{path}: {x}" for x in value]
            if key in self.entities:
                self.entities[key] += value
            else:
                self.entities[key] = value

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
        self.path = path
        self.text = text
        self.language = language
        self.segments = segments
        if path:
            self.fromfile()

    def fromfile(self, path=None):
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
        if not self.iscomplete():
            self.fromfile(path)
        return self.iscomplete()

    def get_dict(self):
        return {
            'text': self.text,
            'segments': self.segments,
            'language': self.language
        }


class Audio:
    def __init__(self, path=None, metadata=None):
        self.path = path
        self.metadata = metadata or EasyID3(path)
    
    def get(self, arg=None):
        if arg == "path":
            return self.path
        elif arg:
            return self.metadata.get(arg)
        else:
            return self.metadata
    
    def get_dict(self):
        return self.metadata.items()

class NLPFeatureAnalysis:
    def __init__(self, path=None, bag_of_words=None, named_entities=None, nlptools: NLPTools = None, transcript: Transcript = None):
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
        self.path = path
        self.bag_of_words = bag_of_words or BagOfWords()
        self.named_entities = named_entities or NamedEntities()
        if path:
            self.fromfile(path)
        if transcript:
            self.complete(transcript, nlptools)

    def fromfile(self, path):
        """
        Load transcript from the given path.

        Args:
            path (str): Path to the transcript file.
        """
        self.path = path
        data = get_json_data(path)
        data_to_attributes(self, data)

    def iscomplete(self):
        if self.bag_of_words.get() and self.named_entities.get():
            return True
        return False

    def complete(self, transcript: Transcript, nlptools: NLPTools = None):
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

        self.fill_named_entities(transcript, nlptools)
        self.fill_bag_of_words(transcript, nlptools)

        # create a Document object and return it
        if changes or self.bag_of_words.update_stops(transcript.language, nlptools):
            self.save()
        return self.iscomplete()

    def fill_bag_of_words(self, transcript: Transcript, nlptools: NLPTools = None):
        if not self.bag_of_words.get():
            nlptools = nlptools or NLPTools()
            if not transcript.iscomplete():
                print("You need a text in a known language to complete " + self.path)
                return False
            # create a Sentence object from the text

            doc = nlptools.get_spacy(transcript.language)(transcript.text)

            # get the bag of words and non-stop-words
            self.bag_of_words = BagOfWords(
                text=doc, nlptools=nlptools, language=transcript.language)
            return self.bag_of_words
        else:
            return False

    def fill_named_entities(self, transcript: Transcript, nlptools: NLPTools = None):
        if not self.named_entities.get():
            nlptools = nlptools or NLPTools()
            if not transcript.iscomplete():
                print("You need a text in a known language to complete " + self.path)
                return False
            sentence = Sentence(transcript.text)

            # embed the sentence using the WordEmbeddings
            document_embeddings = DocumentPoolEmbeddings(
                [nlptools.get_WordEmbeddings(transcript.language)])
            document_embeddings.embed(sentence)

            # get the named entities
            nlptools.get_SequenceTagger(transcript.language).predict(sentence)
            self.named_entities = NamedEntities(text=sentence)
            return self.named_entities
        else:
            return False

    def get_dict(self):
        return {
            'bag_of_words': self.bag_of_words.words,
            'tf_idf': self.bag_of_words.get_tf_idf(),
            'named_entities': self.named_entities.get(),
            'stop_words': self.bag_of_words.stops
        }

    def save(self, path=None):
        if path is None:
            path = self.path
        output_dict = self.get_dict()

        if len(self.bag_of_words.words) == 0:
            print(f"No {colored('words', 'red')} in file: " + path)
        elif len(self.named_entities) == 0:
            print(f"No {colored('named entities', 'red')} in file: " + path)
        dump_json(path, output_dict)


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

    def __init__(self, audio_file_path=None, transcript_file_path=None, image_file_path=None, nlp_analysis_file_path=None, nlptools: NLPTools = None, ):
        self.audio_file = Audio(audio_file_path)
        # todo: check if no audiofile
        self.transcript = Transcript(transcript_file_path)
        self.nlp_analysis = NLPFeatureAnalysis(
            nlp_analysis_file_path, nlptools=nlptools, transcript=self.transcript)
        self.obsidian_note = nlped_whispered_folder.ObsidianNote()
        # todo: make this an actual class
        self.image = image_file_path

        self.basename = next((item for item in [audio_file_path, transcript_file_path, image_file_path, nlp_analysis_file_path] if item is not None), None)
        self.original_name = None
        
        self.search_original_name()

    def search_original_name(self, force=False):
        if self.original_name and not force:
            return self.original_name
        candidates = self.audio_file.get("title")
        if candidates:
            self.original_name = candidates[0] 
            return self.original_name

    def iscomplete(self):
        return self.transcript.iscomplete() and self.nlp_analysis.iscomplete()

    def complete(self, nlptools: NLPTools = None):
        """Processes a JSON file containing text and returns a Document object.

        Args:
            json_path (str): The path to the input JSON file.

        Returns:
            Document: The Document object representing the input text.
        """
        nlptools = nlptools or NLPTools()

        self.transcript.complete()
        self.nlp_analysis.complete(nlptools)
        # todo: complete from here
        # Check what needs to be done:

    def get_dict(self):
        return dict(self.audio_file.get_dict()) | self.transcript.get_dict() | self.nlp_analysis.get_dict()


class Subfolder:
    folder_formats = {
        "blank": [],
        # 00 Input
        "00_audios": [".mp3", ".mp4"],
        "00_images": [".png", ".jpg", ".jpeg"],
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
        self.type = type
        self.endings = self.folder_formats[type]
        os.makedirs(self.path, exist_ok=True)

    def lookfor(self, filename):
        found = []
        not_found = []
        basename = os.path.basename(filename)
        stem = os.path.splitext(basename)[0]
        for ending in self.endings:
            path = os.path.join(self.path, stem+ending)
            if os.path.exists(path):
                found.append(path)
            else:
                not_found.append(path)

        return found, not_found


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

    def __init__(self, folder_path, nlptools=None, language=None, media_resources: List[MediaResource] = None):
        self.path = folder_path
        self.audio = Subfolder(folder_path, "00_audios")
        self.image = Subfolder(folder_path, "00_images")
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

        if nlptools:
            self.process(nlptools)

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
            mr.nlp_analysis.save()

    def add_media_resource(self, media_resource: MediaResource):
        if media_resource:
            self.media_resources.append(media_resource)

    def calc_idf(self):
        self.idf = {word: math.log(len(self.media_resources)/(frequency))
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

    def save(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.path, "rep_Folder")
        output_dict = self.get_dict()

        if any(len(attr) == 0 for attr in [self.media_resources, self.bag_of_words, self.named_entities]):
            print("Error on Folder: " + output_path)
        dump_json(output_path, output_dict)

    def save_summary(self, output_path):
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

        if any(len(attr) == 0 for attr in [self.media_resources, self.bag_of_words, self.named_entities]):
            print("Error on Folder: " + output_path)
        dump_json(output_path, output_dict)

    def process(self, nlptools=None):
        if nlptools is None:
            nlptools = NLPTools()

        for audio_file in os.listdir(self.audio.path):
            audio_file_path = os.path.join(self.audio.path, audio_file)
            i_found, i_not = self.image.lookfor(audio_file)
            w_found, w_not = self.whisper.lookfor(audio_file)
            a_found, a_not = self.analyse.lookfor(audio_file)
            # todo: notes
            # todo: make work when multiple are found
            image = i_found[0] if i_found else i_not[0] if i_not else None
            whisper = w_found[0] if w_found else w_not[0] if w_not else None
            analyse = a_found[0] if a_found else a_not[0] if a_not else None
            mr = MediaResource(audio_file_path=audio_file_path, image_file_path=image, transcript_file_path=whisper,
                               nlp_analysis_file_path=analyse, nlptools=nlptools)
            self.add_media_resource(mr)
        self.populate()
        self.calc_sim_matrix()
        self.save(os.path.join(self.path, "00_Folder.json"))
        self.save_summary(os.path.join(
            self.path, "00_Folder_summary.json"))
        
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
        return MediaResource(transcript_file_path=input_path)
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

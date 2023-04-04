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
import numpy as np

import importlib

# from spacy.lang.en.stop_words import STOP_WORDS as STOP_WORDS_en
# from spacy.lang.de.stop_words import STOP_WORDS as STOP_WORDS_de


# todo: create a class of nlp thing that holds all solvers, etc.
# so you can change language on this
class NLPTools:
    naming_conventions = {
        "en": {"spacy": "en_core_web_sm", "flair": "ner"},
        "de": {"spacy": "de_core_news_sm", "flair": "flair/ner-german"},
        "zh": {"spacy": "zh_core_web_sm", "flair": "flair/ner-chinese"},
        # add more languages and their naming conventions as needed
    }

    MY_STOP_WORDS = {
        "en": {},
        "de": {
            "mal",
            "einfach",
            "sagen",
            "eigentlich",
            "finden",
            "genau",
            "quasi",
            "halt",
            "hey",
            "irgendwie",
            "bisschen",
            "bissch"
        }
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
        self.STOP_WORDS[language] = NLPTools.MY_STOP_WORDS[language].union(
            stop_words_module.STOP_WORDS)
        return self.STOP_WORDS[language]

    def get_spacy(self, language):
        if language in self.spacy:
            return self.spacy[language]
        try:
            nlp_model = self.naming_conventions.get(
                language, {}).get("spacy", f"{language}_core_news_sm")
            self.spacy[language] = spacy.load(nlp_model)

            for word in self.get_STOP_WORDS(language):
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
                language, {}).get("flair", f"{language}_fasttext")
            return WordEmbeddings(word_embeddings_model)
        except Exception as e:
            print(f"Error loading WordEmbeddings for {language}: {str(e)}")
            return None

    def get_SequenceTagger(self, language):
        if language in self.SequenceTagger:
            return self.SequenceTagger[language]
        try:
            sequence_tagger_model = self.naming_conventions.get(
                language, {}).get("flair", f"ner-{language.lower()}")
            return SequenceTagger.load(sequence_tagger_model)
        except Exception as e:
            print(f"Error loading SequenceTagger for {language}: {str(e)}")
            return None


class BagOfWords:
    def __init__(self, words: Dict[str, int] = None):
        self.words = words or {}
        self.sort()

    def __len__(self):
        return len(self.words)

    def sort(self):
        self.words = {k: v for k, v in sorted(self.words.items(),
                                              key=lambda x: x[1], reverse=True)}

    def get(self):
        return self.words

    def add(self, other):
        for word, count in other.words.items():
            if word in self.words:
                self.words[word] += count
            else:
                self.words[word] = count

    @ classmethod
    def from_nlp_text(cls, nlp_text):
        bag_of_words = defaultdict(int)
        stop_words = defaultdict(int)
        for token in nlp_text:
            if token.is_alpha:
                word = token.lemma_.lower()
                if token.is_stop:
                    stop_words[word] += 1
                else:
                    bag_of_words[word] += 1
        return cls(bag_of_words), cls(stop_words)

    # bag_of_words = {k: v for k, v in sorted(bag_of_words.items(), key=lambda item: item[1], reverse=True)}


class NamedEntities:
    def __init__(self, entities: Dict[str, List[str]] = None):
        self.entities = entities or {}
        self.sort()

    def __len__(self):
        return len(self.entities)

    def sort(self):
        self.entities = {k: v for k, v in sorted(
            self.entities.items(), key=lambda item: len(item[1]), reverse=True)}

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
        result = self.entities.copy()
        for key, value in other.entities.items():
            if path:
                path = os.path.basename(path)
                value = [f"{path}: {x}" for x in value]
            if key in result:
                result[key] += value
            else:
                result[key] = value
        return NamedEntities(result)

    def get(self):
        return self.entities

    def get_frequencies(self):
        return {k: len(v) for k, v in self.entities.items()}

    @ classmethod
    def from_nlp_text(cls, sentence):
        named_entities = {}
        for entity in sentence.get_spans('ner'):
            rep = f"Span[{entity.start_position}:{entity.end_position}]: {entity.tag} ({round(entity.score, 2)})"
            if entity.text in named_entities:
                named_entities[entity.text].append(rep)
            else:
                named_entities[entity.text] = [rep]
        return cls(named_entities)


class Document:
    """A class to represent a document.

    Attributes:
        text (str): The full text of the document.
        bag_of_words (dict): A dictionary containing the frequency count of each word in the document.
        stop_words (list): A list of all non-stop words in the document.
        named_entities (dict): A dictionary containing the named entities in the document, where the keys are
            the entity types and the values are lists of `Span` objects representing each occurrence of that entity type.
    """

    json_names = [
        'file_path',
        'text',
        'bag_of_words',
        'stop_words',
        'named_entities'
    ]

    def __init__(self, file_path=None, text=None, bag_of_words=None, stop_words=None, named_entities=None, language=None):
        self.language = language
        self.path = file_path
        self.text = text
        self.bag_of_words = bag_of_words
        self.stop_words = stop_words
        self.named_entities = named_entities

    def from_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for key, value in data.items():
                    if hasattr(self, key):
                        if key == "named_entities":
                            value = NamedEntities(value)
                        elif key == "bag_of_words" or key == "stop_words":
                            value = BagOfWords(value)
                        setattr(self, key, value)
            self.path = path
        except Exception as e:
            print(f"Could not proceed on {path}: {str(e)}")
            return None

    def get_dict(self):
        return {
            'bag_of_words': self.bag_of_words.get(),
            'stop_words': self.stop_words.get(),
            'named_entities': self.named_entities.get(),
            'text': self.text
        }

    def save(self, output_path):
        output_dict = self.get_dict()

        if any(len(attr) == 0 for attr in [self.stop_words, self.bag_of_words, self.named_entities]):
            print("Error on file: " + output_path)
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(output_dict, output_file, indent=4, ensure_ascii=False)

    def iscomplete(self):
        # https://www.geeksforgeeks.org/how-to-get-a-list-of-class-attributes-in-python/
        for i in inspect.getmembers(self):
            # to remove private and protected functions
            if not i[0].startswith('_'):
                # To remove other methods that does not start with a underscore
                if not inspect.ismethod(i[1]):
                    if i[1] is None:
                        return False
        return True

    def update_stops(self, nlp=None):
        to_stop = []
        to_bag = []
        for key in self.bag_of_words.words.keys():
            if key in nlp.vocab and nlp.vocab[key].is_stop:
                to_stop.append(key)
        for key in self.stop_words.words.keys():
            if key in nlp.vocab and not nlp.vocab[key].is_stop:
                to_bag.append(key)
        for key in to_stop:
            self.stop_words.words[key] = self.bag_of_words.words.pop(key)
            self.stop_words.sort()
        for key in to_bag:
            self.bag_of_words.words[key] = self.stop_words.words.pop(key)
            self.bag_of_words.sort()
        return len(to_bag)+len(to_stop)


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

    Methods:
        add_document(document: Document) -> None: Adds a Document instance to the folder.
        populate() -> None: Populates the stop_words, bag_of_words and named_entities attributes by aggregating
            the counts and occurrences of the respective attributes in all documents.
        save(output_path: str) -> None: Saves the Folder instance to a JSON file at the specified output path.
    """

    def __init__(self, folder_path, documents: List[Document] = None):
        self.path = folder_path
        self.documents = documents or []
        self.stop_words = BagOfWords()
        self.bag_of_words = BagOfWords()
        self.named_entities = NamedEntities()
        self.added_docs = set()
        self.sim_matrix = None

    def calc_sim_matrix(self):
        bag_sim_mat = similarity.create_word_vectors(
            [doc.bag_of_words.get() for doc in self.documents], self.bag_of_words.get())

        # todo: option to eventually weigh named entities differently
        # nam_sim_mat = similarity.create_word_vectors(
        #     [doc.named_entities.get() for doc in self.documents], self.named_entities)

        self.sim_matrix = bag_sim_mat

    def add_document(self, document: Document):
        if document:
            self.documents.append(document)

    def populate(self):
        for doc in self.documents:
            if doc.path not in self.added_docs:
                self.stop_words.add(doc.stop_words)
                self.bag_of_words.add(doc.bag_of_words)
                self.named_entities.add(doc.named_entities, doc.path)
                self.added_docs.add(doc.path)
        self.stop_words.sort()
        self.bag_of_words.sort()
        self.named_entities.sort()

    def save(self, output_path):
        output_dict = {
            'stop_words': self.stop_words.get(),
            'bag_of_words': self.bag_of_words.get(),
            'named_entities': self.named_entities.get(),
            'documents': [os.path.basename(doc.path) for doc in self.documents]
        }

        if any(len(attr) == 0 for attr in [self.documents, self.stop_words, self.bag_of_words, self.named_entities]):
            print("Error on Folder: " + output_path)
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(output_dict, output_file, indent=4, ensure_ascii=False)

    def save_summary(self, output_path):
        if not len(self.documents):
            print(f"No Documents found in folder: {output_path}")
            return None
        threshold = min(
            int(list(self.stop_words.get().values())[0] / 100), 10)
        threshold = max(threshold, 3)
        output_dict = {
            'bag_of_words': {k: v for k, v in list(self.bag_of_words.get().items())[:1000] if v >= threshold},
            'stop_words': {k: v for k, v in list(self.stop_words.get().items())[:1000] if v >= threshold},
            'named_entities': {k: len(v) for k, v in list(self.named_entities.get().items())[:1000] if len(v) >= threshold},
            'documents': [os.path.basename(doc.path) for doc in self.documents]
        }

        if any(len(attr) == 0 for attr in [self.documents, self.stop_words, self.bag_of_words, self.named_entities]):
            print("Error on Folder: " + output_path)
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(output_dict, output_file, indent=4, ensure_ascii=False)


def get_output_path(input_path, filename=None, output_folder=None):
    if '_processed.json' in input_path:
        return input_path
    if output_folder:
        return os.path.join(output_folder, filename.replace('.json', '_processed.json'))
    else:
        return input_path.replace('.json', '_processed.json')


def process_folder(input_folder, output_folder=None, language="en"):
    nlptools = NLPTools()
    if output_folder:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

    folder = Folder(input_folder)
    audio_path = os.path.join(input_folder, "audio")
    extract_path = os.path.join(input_folder, "01_extract")
    analyse_path = os.path.join(input_folder, "02_analyse")
    for filename in os.listdir(extract_path):
        if filename.endswith('.json') and not filename.endswith('_processed.json'):
            input_path = os.path.join(audio_path, filename)
            output_path = get_output_path(audio_path, filename, analyse_path)
            folder.add_document(process_json_file(input_path, output_path,
                                                  nlptools, language=language))
    folder.populate()
    folder.calc_sim_matrix()
    folder.save(os.path.join(input_folder, "00_Folder.json"))
    folder.save_summary(os.path.join(input_folder, "00_Folder_summary.json"))
    return folder


def process_json_file(json_path, output_path, nlptools: NLPTools, language="en"):
    """Processes a JSON file containing text and returns a Document object.

    Args:
        json_path (str): The path to the input JSON file.

    Returns:
        Document: The Document object representing the input text.
    """

    rep = Document(language=language)

    if output_path is None:
        output_path = get_output_path(json_path)
    elif os.path.exists(output_path):
        rep.from_file(output_path)
    elif rep.from_file(json_path) is None:
        return None

    # Check what needs to be done:

    if rep.iscomplete():
        if rep.update_stops(nlptools.get_spacy(language)):
            rep.save(output_path)
        return rep

    if rep.path is None:
        rep.path = json_path

    if rep.bag_of_words is None or rep.stop_words is None:
        # create a Sentence object from the text
        sentence = Sentence(rep.text)

        # embed the sentence using the WordEmbeddings
        document_embeddings = DocumentPoolEmbeddings(
            [nlptools.get_WordEmbeddings(language)])
        document_embeddings.embed(sentence)

        doc = nlptools.get_spacy(language)(rep.text)

        # get the bag of words and non-stop-words
        rep.bag_of_words, rep.stop_words = BagOfWords.from_nlp_text(doc)

    rep.update_stops(nlptools.get_spacy(language))

    if rep.named_entities is None:
        # get the named entities
        nlptools.get_SequenceTagger(language).predict(sentence)
        rep.named_entities = NamedEntities.from_nlp_text(sentence)

    # create a Document object and return it
    rep.save(output_path)
    return rep


def main(input_path, output_path=None):
    if os.path.isfile(input_path):
        # process single file
        document = process_json_file(input_path)
    elif os.path.isdir(input_path):
        # process all files in directory
        process_folder(input_path, output_path)
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

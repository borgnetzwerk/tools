import argparse
import os
import json
import spacy
from flair.data import Sentence, Token
from flair.models import SequenceTagger
from flair.embeddings import WordEmbeddings, DocumentPoolEmbeddings
from collections import defaultdict
from typing import List, Dict


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

    @classmethod
    def from_nlp_text(cls, nlp_text, allow_stop=True):
        bag_of_words = defaultdict(int)
        for token in nlp_text:
            if token.is_alpha:
                word = token.lemma_.lower()
                if allow_stop or not token.is_stop:
                    bag_of_words[word] += 1
        return cls(bag_of_words)

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

    @classmethod
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
        non_stop_words (list): A list of all non-stop words in the document.
        named_entities (dict): A dictionary containing the named entities in the document, where the keys are
            the entity types and the values are lists of `Span` objects representing each occurrence of that entity type.
    """

    def __init__(self, file_path, text, bag_of_words, non_stop_words, named_entities):
        self.path = file_path
        self.text = text
        self.bag_of_words = bag_of_words
        self.non_stop_words = non_stop_words
        self.named_entities = named_entities

    @classmethod
    def from_file(cls, path):
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return cls(path, data['text'], BagOfWords(data['bag_of_words']), BagOfWords(data['non_stop_words']), NamedEntities(data['named_entities']))

    def get_dict(self):
        return {
            'non_stop_words': self.non_stop_words.get(),
            'bag_of_words': self.bag_of_words.get(),
            'named_entities': self.named_entities.get(),
            'text': self.text
        }

    def save(self, output_path):
        output_dict = self.get_dict()

        if any(len(attr) == 0 for attr in [self.non_stop_words, self.bag_of_words, self.named_entities]):
            print("Error on file: " + output_path)
            with open(output_path, 'w', encoding='utf-8') as output_file:
                json.dump(output_dict, output_file, indent=4)


class Folder:
    """A class to represent a folder containing multiple Document instances.

    Attributes:
        documents (List[Document]): A list of Document instances contained in the folder.
        non_stop_words (defaultdict(int)): A defaultdict with non-stop words as keys and their total count across
            all documents as values.
        bag_of_words (defaultdict(int)): A defaultdict with words as keys and their total count across all
            documents as values.
        named_entities (Dict[str, List[str]]): A dictionary with named entities as keys and their occurrences in
            the documents as values.

    Methods:
        add_document(document: Document) -> None: Adds a Document instance to the folder.
        populate() -> None: Populates the non_stop_words, bag_of_words and named_entities attributes by aggregating
            the counts and occurrences of the respective attributes in all documents.
        save(output_path: str) -> None: Saves the Folder instance to a JSON file at the specified output path.
    """

    def __init__(self, folder_path, documents: List[Document] = None):
        self.path = folder_path
        self.documents = documents or []
        self.non_stop_words = BagOfWords()
        self.bag_of_words = BagOfWords()
        self.named_entities = NamedEntities()
        self.added_docs = set()

    def add_document(self, document: Document):
        if document:
            self.documents.append(document)

    def populate(self):
        for doc in self.documents:
            if doc.path not in self.added_docs:
                self.non_stop_words.add(doc.non_stop_words)
                self.bag_of_words.add(doc.bag_of_words)
                self.named_entities.add(doc.named_entities, doc.path)
                self.added_docs.add(doc.path)
        self.non_stop_words.sort()
        self.bag_of_words.sort()
        self.named_entities.sort()

    def save(self, output_path):
        output_dict = {
            'non_stop_words': self.non_stop_words.get(),
            'bag_of_words': self.bag_of_words.get(),
            'named_entities': self.named_entities.get(),
            'documents': [os.path.basename(doc.path) for doc in self.documents]
        }

        if any(len(attr) == 0 for attr in [self.documents, self.non_stop_words, self.bag_of_words, self.named_entities]):
            print("Error on Folder: " + output_path)
            with open(output_path.replace(".json", "error.json"), 'w', encoding='utf-8') as output_file:
                json.dump(output_dict, output_file, indent=4)
        else:
            with open(output_path, 'w', encoding='utf-8') as output_file:
                json.dump(output_dict, output_file, indent=4)


def initialize_dependencies(nlp=None, word_embeddings=None, tagger=None, spacy_model='en_core_web_sm', word_embeddings_model='glove', sequence_tagger_model='ner'):
    if nlp is None:
        try:
            nlp = spacy.load(spacy_model)
        except Exception as e:
            print(f"Error loading spacy: {str(e)}")
            return None, None, None

    # initialize the WordEmbeddings
    if word_embeddings is None:
        try:
            word_embeddings = WordEmbeddings(word_embeddings_model)
        except Exception as e:
            print(f"Error loading WordEmbeddings: {str(e)}")
            return None, None, None

    if tagger is None:
        try:
            tagger = SequenceTagger.load(sequence_tagger_model)
        except Exception as e:
            print(f"Error loading SequenceTagger: {str(e)}")
            return None, None, None
    return nlp, word_embeddings, tagger


def get_output_path(input_path, filename=None, output_folder=None):
    if '_processed.json' in input_path:
        return input_path
    if output_folder:
        return os.path.join(output_folder, filename.replace('.json', '_processed.json'))
    else:
        return input_path.replace('.json', '_processed.json')


def process_folder(input_folder, output_folder=None):
    if output_folder:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

    nlp, word_embeddings, tagger = initialize_dependencies()
    if nlp is None:
        return None
    folder = Folder(input_folder)
    for filename in os.listdir(input_folder):
        if filename.endswith('.json') and not filename.endswith('_processed.json'):
            input_path = os.path.join(input_folder, filename)
            output_path = get_output_path(input_path, filename, output_folder)
            folder.add_document(process_json_file(input_path, output_path,
                                                  nlp, word_embeddings, tagger))
    folder.populate()
    folder.save(os.path.join(input_folder, "00_Folder.json"))
    return folder


def process_json_file(json_path, output_path=None, nlp=None, word_embeddings=None, tagger=None):
    """Processes a JSON file containing text and returns a Document object.

    Args:
        json_path (str): The path to the input JSON file.

    Returns:
        Document: The Document object representing the input text.
    """

    if output_path is None:
        output_path = get_output_path(json_path)
    elif os.path.exists(output_path):
        return Document.from_file(output_path)

    nlp, word_embeddings, tagger = initialize_dependencies(
        nlp, word_embeddings, tagger)
    if nlp is None:
        return None
    
    try:
        with open(json_path, encoding='utf-8') as json_file:
            json_data = json.load(json_file)
            text = json_data['text']
    except Exception as e:
        print(f"Could not proceed on {json_path}: {str(e)}")
        return None
    # create a Sentence object from the text
    sentence = Sentence(text)

    # embed the sentence using the WordEmbeddings
    document_embeddings = DocumentPoolEmbeddings([word_embeddings])
    document_embeddings.embed(sentence)

    doc = nlp(text)

    # get the bag of words and non-stop-words
    bag_of_words = BagOfWords.from_nlp_text(doc)
    non_stop_words = BagOfWords.from_nlp_text(doc, allow_stop=False)

    # get the named entities
    tagger.predict(sentence)
    named_entities = NamedEntities.from_nlp_text(sentence)

    # create a Document object and return it
    rep = Document(json_path, text, bag_of_words,
                   non_stop_words, named_entities)
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

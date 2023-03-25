import argparse
import os
import json
import spacy
from flair.data import Sentence, Token
from flair.models import SequenceTagger
from flair.embeddings import WordEmbeddings, DocumentPoolEmbeddings
from collections import defaultdict


class Document:
    """A class to represent a document.

    Attributes:
        text (str): The full text of the document.
        bag_of_words (dict): A dictionary containing the frequency count of each word in the document.
        non_stop_words (list): A list of all non-stop words in the document.
        named_entities (dict): A dictionary containing the named entities in the document, where the keys are
            the entity types and the values are lists of `Span` objects representing each occurrence of that entity type.
    """

    def __init__(self, text, bag_of_words, non_stop_words, named_entities):
        self.text = text
        self.bag_of_words = bag_of_words
        self.non_stop_words = non_stop_words
        self.named_entities = named_entities


def save_document(document, output_path):
    output_dict = {
        'text': document.text,
        'bag_of_words': document.bag_of_words,
        'non_stop_words': document.non_stop_words,
        'named_entities': document.named_entities
    }

    with open(output_path, 'w') as output_file:
        json.dump(output_dict, output_file)


def initialize_dependencies(nlp, word_embeddings, tagger, spacy_model='en_core_web_sm', word_embeddings_model='glove', sequence_tagger_model='ner'):
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
    if output_folder:
        return os.path.join(output_folder, filename)
    elif filename:
        return os.path.join(input_path, filename.replace('.json', '_processed.json'))
    else:
        return input_path.replace('.json', '_processed.json')


def process_folder(input_folder, output_folder=None):
    if output_folder:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

    nlp, word_embeddings, tagger = initialize_dependencies()
    if nlp is None:
        return None
    documents = []
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_path = os.path.join(input_folder, filename)
            output_path = get_output_path(input_path, filename, output_folder)
            if not os.path.exists(output_path):
                documents.append(process_json_file(input_path, output_path,
                                                   nlp, word_embeddings, tagger))
    # todo: do sth with the documents
    return documents


def process_json_file(json_path, output_path=None, nlp=None, word_embeddings=None, tagger=None):
    """Processes a JSON file containing text and returns a Document object.

    Args:
        json_path (str): The path to the input JSON file.

    Returns:
        Document: The Document object representing the input text.
    """

    nlp, word_embeddings, tagger = initialize_dependencies(
        nlp, word_embeddings, tagger)
    if nlp is None:
        return None

    with open(json_path) as json_file:
        json_data = json.load(json_file)
        text = json_data['text']

    # create a Sentence object from the text
    sentence = Sentence(text)

    # embed the sentence using the WordEmbeddings
    document_embeddings = DocumentPoolEmbeddings([word_embeddings])
    document_embeddings.embed(sentence)

    doc = nlp(text)

    # get the bag of words and non-stop-words
    bag_of_words = defaultdict(int)
    non_stop_words = defaultdict(int)
    for token in doc:
        if token.is_alpha:
            word = token.lemma_.lower()
            bag_of_words[word] += 1
            if not token.is_stop:
                non_stop_words[word] += 1

    bag_of_words = {k: v for k, v in sorted(
        bag_of_words.items(), key=lambda item: item[1], reverse=True)}
    non_stop_words = {k: v for k, v in sorted(
        non_stop_words.items(), key=lambda item: item[1], reverse=True)}

    # get the named entities
    tagger.predict(sentence)
    named_entities = {}
    for entity in sentence.get_spans('ner'):
        if entity.text in named_entities:
            named_entities[entity.text].append(entity)
        else:
            named_entities[entity.text] = [entity]
    named_entities = {k: v for k, v in sorted(
        named_entities.items(), key=lambda item: len(item[1]), reverse=True)}

    # create a Document object and return it
    if output_path is None:
        output_path = get_output_path(json_path)
    save_document(Document, output_path)
    return Document(text, bag_of_words, non_stop_words, named_entities)


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

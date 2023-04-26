# controllers.py
from __future__ import annotations
from typing import TYPE_CHECKING

import os
import numpy as np
import pandas as pd
from typing import List, Dict
import matplotlib
# If you want to debug:
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial import distance
if TYPE_CHECKING:
    from extract.nlp.util_nlp import ResearchQuestion
from wordfreq import word_frequency

MAX_LABELS = 15

# todo: https://towardsdatascience.com/a-glance-at-text-similarity-52e607bfe920
# TF-IDF (term frequency-inverse document frequency)

# Word embeddings are vector representations of words that capture the semantic relationships between them.
#   Instead of comparing the frequency of individual words, you can compare the similarity of their
#   vector representations. This can provide a more nuanced understanding of the meaning of the texts.


def create_word_vectors(dictionaries: List[Dict[str, int]], sum_dict: Dict[str, int] = None):
    """
    Create episode vectors from a list of dictionaries.

    Args:
        dictionaries (List[Dict[str, int]]): A list of dictionaries, where each dictionary represents
            the word frequencies for an episode.

    Returns:
        np.ndarray: A 2D numpy array where each row represents the word vector for an episode.
    """
    if sum_dict:
        unique_words = set(word for word in sum_dict.keys())
    else:
        unique_words = set(word for d in dictionaries for word in d.keys())
    vector_size = len(unique_words)
    word_indices = {word: i for i, word in enumerate(unique_words)}
    vectors = np.zeros((len(dictionaries), vector_size))
    for i, d in enumerate(dictionaries):
        for word, count in d.items():
            index = word_indices[word]
            vectors[i][index] = count
    return vectors


def normalize(vectors):
    max_values = np.max(vectors, axis=0)
    vectors /= max_values
    return vectors


# def compute_similarity_matrix(vectors):
#     # todo: Include weighed cosine similarity
#     return cosine_similarity(vectors)


def compute_similarity_from_vectors(vector_a: List[Dict[str, int]], vector_b: List[Dict[str, int]]):
    np_vectors_a = create_word_vectors(vector_a)
    np_vectors_a = normalize(np_vectors_a)

    np_vectors_b = create_word_vectors(vector_b)
    sim_matrix = cosine_similarity(np_vectors_a, np_vectors_b)
    return sim_matrix


def compute_weighed_similarity(vector_a: List[Dict[str, int]], vector_b: List[Dict[str, int]]):
    np_vectors_a = create_word_vectors(vector_a)
    np_vectors_a = normalize(np_vectors_a)

    np_vectors_b = create_word_vectors(vector_b)
    sim_matrix = np.zeros((len(np_vectors_a), len(np_vectors_b)))
    target = np.ones(len(np_vectors_b[0]))
    for c_a, vector_a in enumerate(np_vectors_a):
        for c_b, weight in enumerate(np_vectors_b):
            if sum(vector_a * weight) == 0:
                sim_matrix[c_a][c_b] = 0
            else:
                sim_matrix[c_a][c_b] = 1 - \
                    distance.cosine(vector_a, target, weight)
    return sim_matrix


def compute_similarity_matrix(dictionaries: List[Dict[str, int]], sum_dict: Dict[str, int] = None):
    vectors = create_word_vectors(dictionaries, sum_dict)
    sim_matrix = cosine_similarity(vectors)
    return sim_matrix


def print_rq(names: list[str], sim_matrix, path, prefix="", filename="", suffix="_similarity_matrix", xlabel='Documents', ylabel='Documents', dpi=300, vmin=None, vmax=None, cmap=None, additional_info: list[ResearchQuestion] = None):
    n_documents, n_questions = sim_matrix.shape

    fig, ax = plt.subplots()
    bottom = np.zeros(n_documents)

    # every_nth_x = max(1, n_documents // MAX_LABELS)

    for i, rq in enumerate(additional_info):
        name = rq.title
        p = ax.bar(names, sim_matrix[:, 0], label=name, bottom=bottom)
        bottom += sim_matrix[:, 0]
        if n_documents < MAX_LABELS:
            ax.bar_label(p, label_type='center')

    # ax.set_xticklabels(range(1, n_documents + 1, every_nth_x), rotation=90)
    ax.set_xlabel(xlabel)

    ax.set_title('Importance to our Research question')
    ax.legend()

    # Save heatmap as PNG
    filename = prefix + filename + suffix
    png_file = os.path.join(path, filename) + '.png'
    plt.savefig(png_file, dpi=dpi)

    # Save similarity matrix as CSV
    csv_file = os.path.join(path, filename) + '.csv'
    pd.DataFrame(sim_matrix).to_csv(csv_file, index=False,
                                    header=False, sep=";", decimal=",")

    # ax.legend()

    print(f"Similarity matrix saved as {png_file} and {csv_file}.")


def print_sim_matrix(sim_matrix, path, prefix="", filename="", suffix="_similarity_matrix", xlabel='Documents', ylabel='Documents', dpi=300, vmin=None, vmax=None, cmap=None, additional_info: ResearchQuestion = None):
    # If i want to see the figure:
    # fig, ax = plt.subplots()
    fig, ax = plt.subplots()
    # plt.show()
    len_y, len_x = sim_matrix.shape
    if len_x == len_y:
        np.fill_diagonal(sim_matrix, np.nan)

    # todo: fix

    if vmin is None:
        vmin = np.nanmin(sim_matrix)
    if vmax is None:
        vmax = np.nanmax(sim_matrix)
    if cmap is None:
        cmap = 'Greens'
    im = ax.imshow(sim_matrix * 100, cmap=cmap, vmin=vmin, vmax=vmax)
    # if len(sim_matrix) < 10:
    #     ax.set_xticks(range(len(sim_matrix)))
    #     ax.set_yticks(range(len(sim_matrix)))
    #     ax.set_xticklabels(range(1, len(sim_matrix)+1), rotation=90)
    #     ax.set_yticklabels(range(1, len(sim_matrix)+1), rotation=90)
    every_nth_x = max(1, len_x // MAX_LABELS)
    every_nth_y = max(1, len_y // MAX_LABELS)
    ax.set_xticks(range(0, len_x, every_nth_x))
    ax.set_yticks(range(0, len_y, every_nth_y))
    ax.set_xticklabels(range(1, len_x + 1, every_nth_x), rotation=90)
    ax.set_yticklabels(range(1, len_y + 1, every_nth_y), rotation=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title('Cosine Similarity Matrix')
    cbar = plt.colorbar(im, format='%.1f%%')
    cbar.ax.set_ylabel('Similarity (%)')
    # Save heatmap as PNG
    filename = prefix + filename + suffix
    png_file = os.path.join(path, filename) + '.png'
    plt.savefig(png_file, dpi=dpi)

    # Save similarity matrix as CSV
    csv_file = os.path.join(path, filename) + '.csv'
    pd.DataFrame(sim_matrix).to_csv(csv_file, index=False,
                                    header=False, sep=";", decimal=",")

    print(f"Similarity matrix saved as {png_file} and {csv_file}.")

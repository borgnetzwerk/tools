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
from wordfreq import word_frequency

if TYPE_CHECKING:
    from ..extract.nlp.util_nlp import ResearchQuestion

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


def normalize(vectors, log_level=False, sqrt_level=2, config=None):
    """
    Normalize a list of vectors and reward higher word counts logarithmically.

    Parameters:
    ----------
    vectors : numpy.ndarray
        A 2D numpy array of shape (n_samples, n_features) containing the vectors to normalize.
    log : bool, optional (default=True)
        Whether to apply logarithmic scaling to the values in the input array.

    Returns:
    -------
    numpy.ndarray
        A 2D numpy array of shape (n_samples, n_features) containing the normalized vectors.

    Notes:
    -----
    This function normalizes each element in the input array by dividing it by its maximum value in its column.
    If the `log` argument is True, it applies logarithmic scaling to the values in the input array by scaling up the
    values by a large constant (9999 in this case) to avoid negative values, adding 1 to each element to avoid taking
    the logarithm of 0 or negative numbers, and applying logarithmic scaling using base 10, before dividing by 4
    to reduce the magnitude of the resulting values.

    Examples:
    --------
    >>> vectors = np.array(
63        [[0.010,  0.03,   0.004], 
285        [0.14,   0.002,  0.005], 
max        [0.232,  0.118,  0.242]])
    >>> normalize(vectors, log_level=0)
    array([[0.427,  0.262,  0.018], 
285        [0.613,  0.017,  0.023], 
           [1.0,    1.0,    1.0]])
    >>> normalize(vectors, log_level=5)
    array([[0,908,  0.855, 0.564],
           [0,947,  0.555, 0.591],
           [1.0,    1.0,    1.0]])
    """
    # check if vectors is List[Dict[str, int]]
    if isinstance(vectors[0], dict):
        vectors = create_word_vectors(vectors)

    if config:
        log_level = config.get("log_level", log_level)
        sqrt_level = config.get("sqrt_level", sqrt_level)



    max_values = np.max(vectors, axis=0)
        
    if not np.isscalar(max_values):
        # max_values is a vector.
        indices_zero = max_values == 0
        max_values[indices_zero] = 1  # replacing 0s with 1s
    vectors /= max_values

    if log_level:
        # Recommended: False, not fully tested.
        # If used: ~5, between 2 and 10
        vectors *= 10 ** (log_level - 1)
        vectors += 1
        vectors = np.log10(vectors) / (log_level - 1)
    if sqrt_level:
        vectors = np.sqrt(vectors)

    # TODO: Reduce the reward of long documents
    return vectors

# def compute_similarity_matrix(vectors):
#     # todo: Include weighed cosine similarity
#     return cosine_similarity(vectors)

# # TODO: does not seem to be used anymore
def compute_similarity_from_vectors(vector_a: List[Dict[str, int]], vector_b: List[Dict[str, int]], config=None):
    np_vectors_a = create_word_vectors(vector_a)
    np_vectors_a = normalize(np_vectors_a, config=config)

    np_vectors_b = create_word_vectors(vector_b)
    sim_matrix = cosine_similarity(np_vectors_a, np_vectors_b)
    return sim_matrix


def compute_weighed_similarity(vector_a: List[Dict[str, int]], vector_b: List[Dict[str, int]], config=None):
    np_vectors_a = create_word_vectors(vector_a)
    np_vectors_a = normalize(np_vectors_a, config=config)

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
    plt.close()


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
        vmax = np.nanmax(sim_matrix) * 100
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
    plt.close()

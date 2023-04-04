import os
import numpy as np
import pandas as pd
from typing import List, Dict
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity

from wordfreq import word_frequency

print(word_frequency('The', 'en'))

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


def compute_similarity_matrix(vectors):
    return cosine_similarity(vectors)


def compute_similarity_matrix(dictionaries: List[Dict[str, int]], sum_dict: Dict[str, int] = None):
    vectors = create_word_vectors(dictionaries, sum_dict)
    sim_matrix = cosine_similarity(vectors)
    return sim_matrix


def print_sim_matrix(sim_matrix, path, prefix="", filename="", suffix="_similarity_matrix", xlabel='Documents', ylabel='Documents', dpi=300):
    fig, ax = plt.subplots()
    np.fill_diagonal(sim_matrix, np.nan)
    im = ax.imshow(sim_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    if len(sim_matrix) < 10:
        ax.set_xticks(range(len(sim_matrix)))
        ax.set_yticks(range(len(sim_matrix)))
        ax.set_xticklabels(range(1, len(sim_matrix)+1), rotation=90)
        ax.set_yticklabels(range(1, len(sim_matrix)+1), rotation=90)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title('Cosine Similarity Matrix')
    plt.colorbar(im)

    # Save heatmap as PNG
    filename = prefix + filename + suffix
    png_file = os.path.join(path, filename) + '.png'
    plt.savefig(png_file, dpi=dpi)

    # Save similarity matrix as CSV
    csv_file = os.path.join(path, filename) + '.csv'
    pd.DataFrame(sim_matrix).to_csv(csv_file, index=False,
                                    header=False, sep=";", decimal=",")

    print(f"Similarity matrix saved as {png_file} and {csv_file}.")

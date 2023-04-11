import os
import numpy as np
import pandas as pd
from typing import List, Dict
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity

from wordfreq import word_frequency

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
    # todo: Include weighed cosine similarity
    return cosine_similarity(vectors)


def compute_similarity_matrix(dictionaries: List[Dict[str, int]], sum_dict: Dict[str, int] = None):
    vectors = create_word_vectors(dictionaries, sum_dict)
    sim_matrix = cosine_similarity(vectors)
    return sim_matrix


def print_sim_matrix(sim_matrix, path, prefix="", filename="", suffix="_similarity_matrix", xlabel='Documents', ylabel='Documents', dpi=300, vmin=None, vmax=None, cmap=None):
    fig, ax = plt.subplots()
    np.fill_diagonal(sim_matrix, np.nan)
    if vmin is None:
        vmin = np.nanmin(sim_matrix)
    if vmin is None:
        vmax = np.nanmax(sim_matrix)
    if cmap is None:
        # cmap = 'coolwarm'
        cmap = 'Greens'
        # cmap = 'Blues'
        # Options:
        # 'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r',
        # 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r',
        # 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r',
        # 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn',
        # 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r',
        # 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
        # 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r',
        # 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r',
        # 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr',
        # 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix',
        # 'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat',
        # 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r',
        # 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r',
        # 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral',
        # 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r',
        # 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10',
        #  'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r',
        # 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis',
        # 'viridis_r', 'winter', 'winter_r'
    im = ax.imshow(sim_matrix*100, cmap=cmap, vmin=vmin, vmax=vmax)
    if len(sim_matrix) < 10:
        ax.set_xticks(range(len(sim_matrix)))
        ax.set_yticks(range(len(sim_matrix)))
        ax.set_xticklabels(range(1, len(sim_matrix)+1), rotation=90)
        ax.set_yticklabels(range(1, len(sim_matrix)+1), rotation=90)
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

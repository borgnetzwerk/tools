import numpy as np
from typing import List, Dict
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity


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
    vectors = []
    for d in dictionaries:
        vector = np.zeros(vector_size)
        for word, count in d.items():
            index = word_indices[word]
            vector[index] = count
        vectors.append(vector)
    return np.array(vectors)


def compute_similarity_matrix(vectors):
    """
    Compute the cosine similarity matrix between a list of vectors.

    Args:
        vectors (np.ndarray): A 2D numpy array where each row represents a vector.

    Returns:
        np.ndarray: A square 2D numpy array where each element [i,j] represents the cosine similarity
            between the ith and jth vectors.
    """
    def cosine_similarity(x, y):
        dot_product = np.dot(x, y)
        norm_x = np.linalg.norm(x)
        norm_y = np.linalg.norm(y)
        return dot_product / (norm_x * norm_y)

    num_vectors = vectors.shape[0]
    sim_matrix = np.zeros((num_vectors, num_vectors))
    for i in range(num_vectors):
        for j in range(i+1, num_vectors):
            sim_matrix[i][j] = cosine_similarity(vectors[i], vectors[j])
            sim_matrix[j][i] = sim_matrix[i][j]
    return sim_matrix


def print_sim_matrix(sim_matrix, output_file_prefix):
    # Generate the heatmap plot of the similarity matrix
    fig, ax = plt.subplots(figsize=(10, 10))
    heatmap = ax.pcolor(sim_matrix, cmap='YlGnBu')
    plt.colorbar(heatmap)

    # Set the axis labels and title
    ax.set_xlabel('Episodes')
    ax.set_ylabel('Episodes')
    ax.set_title('Similarity Matrix of Episodes')

    # Save the plot to a PNG file
    output_file_path = output_file_prefix + '.png'
    plt.savefig(output_file_path, dpi=300)

    # Save the similarity matrix to a CSV file
    output_file_path = output_file_prefix + '.csv'
    df = pd.DataFrame(sim_matrix, columns=range(
        len(data)), index=range(len(data)))
    df.to_csv(output_file_path, index=False)

    # Return the similarity matrix
    return sim_matrix

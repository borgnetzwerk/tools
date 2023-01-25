# Work in Progress
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from os import path

# import matplotlib.pyplot as plt

# Define a dictionary that maps words to frequencies


def wordcloud_per_episode():
    with open("data\sample\_lexicon_full_ranked.json", encoding="utf-8") as f:
        word_frequencies = json.load(f)

    for episode, frequency in word_frequencies.items():
        print(episode)
        # filter out words that appear less than 5 times and more than 20 times
        frequency = {k: v for k, v in frequency.items() if v > 5 and v < 20}
        # Create a wordcloud object
        wc = WordCloud(
            background_color="white",
            color_func=lambda *args, **kwargs: "black",
            max_font_size=150,
            # random_state=0,
            max_words=200,
        )

        # Generate a wordcloud
        wc.generate_from_frequencies(frequencies=frequency)

        # Save the wordcloud to file or do whatever you want with it
        wc.to_file(
            "data\output\episodes\wordcloud_episode_{}.png".format(episode))

        # Display the word cloud using matplotlib
        # plt.imshow(wordcloud, interpolation="bilinear")
        # plt.axis("off")
        # plt.show()


def remap_JSON():
    # Define a dictionary that maps words to frequencies
    with open("data\sample\_lexicon_ranked.json", encoding="utf-8") as f:
        word_frequencies = json.load(f)

    episode_word_frequencies = {}

    for word, frequencies in word_frequencies.items():
        # Loop over the episodes in the frequency dictionary for the current word
        for episode, frequency in frequencies.items():
            # Add the current word to the episode_word_frequencies dictionary
            # if it doesn't exist yet, or update the frequency if it does
            if episode not in episode_word_frequencies:
                episode_word_frequencies[episode] = {word: frequency}
            else:
                episode_word_frequencies[episode][word] = frequency

    # write the word frequencies to a file
    with open("wordcloud\data\episode_word_frequencies.json", "w", encoding="utf-8") as f:
        json.dump(episode_word_frequencies, f, ensure_ascii=False, indent=4)


def wordcloud_mask():
    import json

    # Define a dictionary that maps words to frequencies
    with open("data\sample\_lexicon.json", encoding="utf-8") as f:
        word_frequencies = json.load(f)

    # cut off the every word with a frequency higher than 100 and lower than 4
    word_frequencies = {k: v for k,
                        v in word_frequencies.items() if v < 20 and v > 10}

    # Load a mask image from a file
    # mask = np.array(Image.open(path.join("PATH\TO\IMAGE\FILE"))) # must be plack and white

    # Create a WordCloud object
    wordcloud = WordCloud(
        height=1024,
        width=4048,
        background_color="white",
        color_func=lambda *args, **kwargs: "black",
        max_font_size=150,
        # random_state=0,
        max_words=200,
        # mask=mask
    )

    # Generate the word cloud from the dictionary of word frequencies
    wordcloud.generate_from_frequencies(word_frequencies)

    # Save the word cloud to a file
    wordcloud.to_file("data\output\wordcloudFinal.png")

    # Display
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()
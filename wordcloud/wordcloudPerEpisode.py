import json
from wordcloud import WordCloud
# import matplotlib.pyplot as plt

# Define a dictionary that maps words to frequencies
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
    wc.to_file("data\output\episodes\wordcloud_episode_{}.png".format(episode))

    # Display the word cloud using matplotlib
    # plt.imshow(wordcloud, interpolation="bilinear")
    # plt.axis("off")
    # plt.show()
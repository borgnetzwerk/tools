import json
from publish.wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from os import path

# Define a dictionary that maps words to frequencies
with open("data\sample\_lexicon.json", encoding="utf-8") as f:
    word_frequencies = json.load(f)

# cut off the every word with a frequency higher than 100 and lower than 4
word_frequencies = {k: v for k, v in word_frequencies.items() if v < 20 and v > 10}

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
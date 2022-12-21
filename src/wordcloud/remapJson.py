import json

# Define a dictionary that maps words to frequencies
with open("wordcloud\data\lexicon_full_ranked.json", encoding="utf-8") as f:
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
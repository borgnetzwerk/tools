import os
import json
import re

LIMIT_NAMED_ENTITIES = 20
LIMIT_BAG_OF_WORDS = 10


def folder(input_path, limit_ns=LIMIT_BAG_OF_WORDS, limit_ne=LIMIT_NAMED_ENTITIES, force=False):
    # loop over each file in the directory

    # build Entry Node
    # Sort all files into subfolders

    for filename in os.listdir(input_path):
        if filename.endswith("_processed.json"):
            # Get the filename without the extension
            # filebase = os.path.splitext(filename)[0]
            filebase = filename.replace("_processed.json", "")

            # Create the Obsidian directory if it does not exist
            obsidian_dir = os.path.join(input_path, "Obsidian")
            transcript_dir = os.path.join(obsidian_dir, "Transcript")
            if not os.path.exists(transcript_dir):
                os.makedirs(transcript_dir)

            output_path = os.path.join(transcript_dir, filebase + ".md")
            if os.path.exists(output_path) and not force:
                continue

            # load the json data
            with open(os.path.join(input_path, filename), encoding="utf8") as f:
                data = json.load(f)

            # extract the non-stop words and named entities
            named_entities = list(data["named_entities"])

            bag_of_words = []
            try:
                ns_candidates = list(data["bag_of_words"])
                counter = 0
                while len(bag_of_words) < limit_ns:
                    candidate = ns_candidates[counter]
                    counter += 1
                    possible = True
                    for ne in named_entities:
                        if candidate == ne.lower():
                            possible = False
                            break
                    if possible:
                        bag_of_words.append(candidate)

                named_entities = named_entities[:limit_ne]
            except Exception as e:
                print(f"Error in file {filename}: {str(e)}")

            # extract the text from the json data
            text = data["text"]

            # create the modified text block for the markdown file
            for word in bag_of_words + named_entities:
                # use word boundaries and escape the word for regex
                if word in named_entities:
                    pattern = r'\b%s\b' % re.escape(word)
                    text = re.sub(pattern, '[[' + word + ']]', text, count=1)
                else:
                    pattern = r'\b%s\b' % re.escape(word)
                    text = re.sub(pattern, '**' + word + '**', text)

            note = f"""%%
named_entities:: {", ".join("[[" + w + "]]" for w in named_entities)}
bag_of_words:: {", ".join("**" + w + "**" for w in bag_of_words)}
%%
# {filebase}

## Text

{text}
"""
            # create the markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(note)

import os
import json
import re

LIMIT_NAMED_ENTITIES = 20
LIMIT_NON_STOP_WORDS = 10


def folder(input_path, limit_ns=LIMIT_NON_STOP_WORDS, limit_ne=LIMIT_NAMED_ENTITIES, force=False):
    # loop over each file in the directory


    # build Entry Node
    # Sort all files into subfolders


    for filename in os.listdir(input_path):
        if filename.endswith("_processed.json"):
            # Get the filename without the extension
            # filebase = os.path.splitext(filename)[0]
            filebase = filename.replace("_processed.json", "")

            # Create the Obsidian directory if it does not exist
            obsidian_dir = os.path.join(input_path, "Obsidian/")
            if not os.path.exists(obsidian_dir):
                os.makedirs(obsidian_dir)

            output_path = os.path.join(obsidian_dir, filebase + ".md")
            if os.path.exists(output_path) and not force:
                continue

            # load the json data
            with open(os.path.join(input_path, filename)) as f:
                data = json.load(f)

            # extract the non-stop words and named entities
            named_entities = list(data["named_entities"])

            non_stop_words = []
            try:
                ns_candidates = list(data["non_stop_words"])
                counter = 0
                while len(non_stop_words) < limit_ns:
                    candidate = ns_candidates[counter]
                    counter += 1
                    possible = True
                    for ne in named_entities:
                        if candidate == ne.lower():
                            possible = False
                            break
                    if possible:
                        non_stop_words.append(candidate)

                named_entities = named_entities[:limit_ne]
            except Exception as e:
                print(f"Error in file {filename}: {str(e)}")

            # extract the text from the json data
            text = data["text"]

            # create the modified text block for the markdown file
            for word in non_stop_words + named_entities:
                # use word boundaries and escape the word for regex
                if word in named_entities:
                    pattern = r'\b%s\b' % re.escape(word)
                    text = re.sub(pattern, '[[' + word + ']]', text, count=1)
                else: 
                    pattern = r'\b%s\b' % re.escape(word)
                    text = re.sub(pattern, '**' + word + '**', text)

            note = f"""%%
named_entities:: {", ".join("[[" + w + "]]" for w in named_entities)}
non_stop_words:: {", ".join("**" + w + "**" for w in non_stop_words)}
%%
# {filebase}

## Text

{text}
"""
            # create the markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(note)

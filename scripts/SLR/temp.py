import pandas as pd
import os
import json
import numpy as np

def csv_to_dict_of_sets(csv_file):
    dict_of_sets = {}
    # try:
    #     df = pd.read_csv(csv_file)
    # except pd.errors.ParserError:
    #     print("Error parsing CSV file. Trying again with 'error_bad_lines=False'")
    df = pd.read_csv(csv_file, on_bad_lines='warn', delimiter=";")
    for column in df.columns:
        dict_of_sets[column] = set(df[column].str.lower())
    # saved_column = df['process'] #you can also use df['column_name']
    # delete all that exists in two or more columns
    for key in dict_of_sets:
        for other_key in dict_of_sets:
            if key != other_key:
                dict_of_sets[key] = dict_of_sets[key].difference(dict_of_sets[other_key])
    return dict_of_sets

def count_occurrences(papers, instances):
    paper_dict = {}

    occurrences = np.zeros((len(papers), len(instances)), dtype=int)

    for p, paperpath in enumerate(papers.values()):
        with open(paperpath, 'r', encoding="utf8") as f:
            paper = json.load(f)
            for i, instance in enumerate(instances):
                present = True
                pieces = instance.split(' ')
                for piece in pieces:
                    if piece.lower() not in paper['bag_of_words']:
                        present = False
                        break
                if present:
                    occurrences[p][i] = 1
    return occurrences

# Usage example
csv_file = 'C:/workspace/borgnetzwerk/tools/scripts/SLR/data.csv'
instances_dicts = csv_to_dict_of_sets(csv_file)

# merge all sets into one set
instances = set()
for key in instances_dicts:
    instances.update(instances_dicts[key])

# drop all non-text instances
instances.discard(np.nan)
# print(result)

paperspath = 'G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR/02_nlp'
paper_nlp_dict = {}
for file in os.listdir(paperspath):
    if file.endswith(".json"):
        paper_nlp_dict[file[:-5]] = os.path.join(paperspath, file)

occurrences = count_occurrences(paper_nlp_dict, instances)


# re-check occurrences based on full text
GAP_TOO_LARGE_THRESHOLD = 1000

# get all text files
directory = 'G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR/00_PDFs'
paper_full_text = {}
for folder in os.listdir(directory):
    folder_path = os.path.join(directory, folder)
    if os.path.isdir(folder_path):
        for file in os.listdir(folder_path):
            if file.endswith(".txt"):
                file_path = os.path.join(folder_path, file)
                paper_full_text[file[:-4]] = file_path
                break

# find all occurrences of instances in text files
pos_in_papaer = {}

for paperID, paper in enumerate(paper_nlp_dict.keys()):
    if paperID % 100 == 0:
        print(f"Processing paper {paperID} of {len(paper_nlp_dict)}")
    if paper in paper_full_text:
        pos_in_papaer[paper] = {}
        with open(paper_full_text[paper], 'r', encoding="utf8") as f:
            text = f.read().lower()
            for i, instance in enumerate(instances):
                # if this instance is not in this document, move on.
                if not occurrences[paperID][i]:
                    continue

                pieces = instance.split(' ')
                for piece in pieces:
                    piece = piece.lower()
                    if piece not in pos_in_papaer[paper]:
                        pos_in_papaer[paper][piece] = []
                        pos = 1
                        while pos > 0:
                            pos = text.find(piece, pos)
                            if pos != -1:
                                pos_in_papaer[paper][piece].append(pos)
                                # make sure this instance cannot be found again
                                pos += 1
                                # Idea: store the sentence in which the instance was found


                                # def find_min_distance_nested(list_of_lists, input_list = []):
#     min_distance = float('inf')
#     candidate_lists = []
#     for value in list_of_lists[0]:
#         new_list = input_list + [value]
#         if len(list_of_lists) > 1:
#             candidate_lists += find_min_distance_nested(list_of_lists[1:], new_list)
#         else:
#             candidate_lists.append(new_list)
#     if input_list:
#         return candidate_lists
#     else:
#         # we are the root:
#         for candidate_list in candidate_lists:
#             distance = max(candidate_list) - min(candidate_list)
#             if distance < min_distance:
#                 min_distance = distance
#         return min_distance
    
def find_min_distance(lists):
    import sys
    
    # Initialize pointers for each of the lists
    pointers = [0] * len(lists)
    min_distance = sys.maxsize
    
    while True:
        # Get the current elements from the lists
        current_elements = [lists[i][pointers[i]] for i in range(len(lists))]
        
        # Calculate the current distance
        current_min = min(current_elements)
        current_max = max(current_elements)
        current_distance = current_max - current_min
        
        # Update the minimum distance
        if current_distance < min_distance:
            min_distance = current_distance
            
        # Check if we can move forward in the list containing the minimum element
        min_index = current_elements.index(current_min)
        
        # If the pointer exceeds its list length, exit the loop
        for i in range(len(lists)):
            if pointers[i] < len(lists[i]) - 1:
                break
        if pointers[min_index] + 1 >= len(lists[min_index]):
            break
        
        # Otherwise, increment the pointer
        pointers[min_index] += 1
    
    return min_distance

# # Test the function with the given lists
# lists = [[1, 2, 3, 2, 1000], [50, 1001], [100, 1002, 10000]]
# print(find_min_distance(lists))




instance_piece_gap = {}

for paperID, paper in enumerate(paper_nlp_dict.keys()):
    # if paperID % 10 == 0:
    print(f"Processing paper {paperID} of {len(paper_nlp_dict)}")
    if paper in paper_full_text:
        for i, instance in enumerate(instances):
            # if this instance is not in this document, move on.
            if not occurrences[paperID][i]:
                continue

            pieces = instance.split(' ')
            if len(pieces) > 1:
                candidate_postions = []
                for piece in pieces:
                    candidate_postions.append(pos_in_papaer[paper][piece])
                min_distance = find_min_distance(candidate_postions)

                # min_distance_nested = find_min_distance_nested(candidate_postions)
                # print(f"{instance}: {min_distance} vs {min_distance_nested}")
                # if min_distance != min_distance_nested:
                #     print(f"Error: {min_distance} != {min_distance_nested}")

                if instance not in instance_piece_gap:
                    instance_piece_gap[instance] = {}
                instance_piece_gap[instance][paper] = min_distance
                if instance_piece_gap[instance][paper] > GAP_TOO_LARGE_THRESHOLD:
                    occurrences[paperID][i] = 0
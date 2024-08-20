# represent a dict
import csv
import os
import json

from .config import Config

def prep_dict(input_dict):
    changes_needed = {}
    # get ONLY THE FIRST key and value
    key, value = next(iter(input_dict.items()))
    key_change = ""
    value_change = ""
    if isinstance(key, frozenset):
        key_change = "str"
    if isinstance(value, set):
        value_change = "list"
    if isinstance(value, dict):
        value_change = prep_dict(value)
    changes_needed[key_change] = value_change
    return changes_needed


def change_dict(input_dict, changes_needed):
    for key, value in changes_needed.items():
        if key == "str" and value == "list":
            input_dict = {str(key): list(value) for key, value in input_dict.items()}
        elif key == "str":
            input_dict = {str(key): value for key, value in input_dict.items()}
        elif value == "list":
            input_dict = {key: list(value) for key, value in input_dict.items()}
        elif key == "str" and value == "dict":
            input_dict = {
                str(key): change_dict(value, changes_needed["str"])
                for key, value in input_dict.items()
            }
        elif value == "dict":
            input_dict = {
                key: change_dict(value, changes_needed[""])
                for key, value in input_dict.items()
            }
    return input_dict


def process_list(config: Config, input_list: list, filename="some_list", path=None):
    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, filename)
    with open(filepath + ".txt", "w", encoding="utf-8") as f:
        for item in input_list:
            f.write(f"{item}\n")


def process_dict(config: Config, input_dict: dict, filename="some_dict", path=None):
    # convert all sets to lists
    changes_needed = prep_dict(input_dict)
    processed_dict = change_dict(input_dict, changes_needed)

    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, filename)
    with open(filepath + ".json", "w", encoding="utf-8") as f:
        json.dump(processed_dict, f, ensure_ascii=False, indent=4)

    # TODO: Only do this for dicts that need statistical analysis
    requires_analysis = False
    value = list(processed_dict.values())[
        0
    ]  # Convert dict_values to list to make it subscriptable
    if isinstance(value, dict):
        value = list(value.values())[
            0
        ]  # Convert dict_values to list to make it subscriptable
        if isinstance(value, int) or isinstance(value, float):
            requires_analysis = True
    if not requires_analysis:
        return

    container = [["Instance", "Min", "Max", "Mean", "Median", "Std"]]

    for instance, papers in input_dict.items():

        # print(f"Instance: {instance}")
        gaps = papers.values()
        # generate all kinds of statistical values
        min_gap = min(gaps)
        max_gap = max(gaps)
        mean_gap = sum(gaps) / len(gaps)
        median_gap = np.median(list(gaps))
        std_gap = np.std(list(gaps))
        container.append([instance, min_gap, max_gap, mean_gap, median_gap, std_gap])

    filepath = os.path.join(path, filename)

    # TODO: Handle CSV separator
    # if not for_git:
    # Function to convert a single value
    # def convert_decimal_delimiter(value, decimal=CSV_DECIMAL):
    #     if isinstance(value, float):
    #         return f"{value}".replace('.', decimal)
    #     return value

    # # Convert all floats in your container to strings with the desired decimal delimiter
    # container = [[convert_decimal_delimiter(value) for value in row] for row in container]

    # write to csv
    with open(filepath + ".csv", "w", newline="") as file:
        writer = csv.writer(file, delimiter=config.csv_separator)
        writer.writerows(container)


def process_dataframe(config: Config, input_df, name="some_df", path=None):
    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, name)

    # convert all froensets to strings
    for col in input_df.columns:
        # input_df[col] = input_df[col].apply(lambda x: "_".join(x))
        first_element_type = input_df[col].apply(type).iloc[0]
        if first_element_type == frozenset:
            input_df[col] = input_df[col].apply(lambda x: " ".join(x))

    input_df.to_csv(
        filepath + ".csv", sep=config.csv_separator, decimal=config.csv_decimal
    )
    try:
        show(input_df)
    except:
        return input_df
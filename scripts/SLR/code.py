# Setup
import os
from __future__ import annotations


class Config:
    def __init__(self, for_git=True):
        self.for_git = for_git
        self.visualize = not for_git
        self.visualize = True
        self.csv_separator = "," if for_git else ";"
        self.csv_decimal = "." if for_git else ","
        self.only_included_papers = True
        self.properties = ["source"]
        self.proximity_mode = "sqrt"  # "log" mode is untested/unsafe, prefer "sqrt"
        self.base_path = "data/"  # Default base path
        self.subset_path = "data_subset/"
        self.visualization_path = "visualization/"
        self.ontology_path = "ontology/"
        self.orkg_path = "ORKG/"
        self.folder_path = "G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR"
        self.papers_path = (
            "G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR/02_nlp"
        )
        self.review_path = (
            "G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR/03_notes"
        )
        self.csv_file = "C:/workspace/borgnetzwerk/tools/scripts/SLR/data.csv"
        self.obsidian_path = "ontology/obsidian/"
        self.gap_too_large_threshold = 1000
        self.savetime_on_fulltext = (
            False  # If True, operations on fulltext will be kept to a minimum
        )
        self.try_to_save_time = False
        self.recalculate_pos_in_paper = (
            False  # while the calculation is inefficient, just load from file
        )
        self.debug = True

        self.wikidata_query_limit = 20

        self.proximity_seed = 17
        self.proximity_k_spring = 18
        self.proximity_min_value = 0.1

    def get_output_path(self, path="", visualization=False):
        """
        Determine the output path based on the configuration and parameters.
        """
        if not path:
            path = self.subset_path if self.only_included_papers else self.base_path
        if visualization and not path.endswith(self.visualization_path):
            path = os.path.join(path, self.visualization_path)
        if not os.path.exists(path):
            os.makedirs(path)
        return path


# Usage
config = Config(for_git=True)

# debug test
import numpy as np
from typing import List, Tuple
import time


def run_debug_test(
    config: Config,
    instances: list[str] = None,
    papers: list[str] = None,
    paper_instance_occurrence_matrix: np.ndarray = None,
):
    if "ikewiki" in instances:
        ike_index = instances.index("ikewiki")
        sum_ikewiki = np.sum(paper_instance_occurrence_matrix[:, ike_index])
        if sum_ikewiki > 1:
            raise Exception(
                f"Only one paper should contain 'ikewiki', but {sum_ikewiki} do."
            )


def time_function(func):
    def wrapper(*args, **kwargs):
        appendix = ""
        # if instances in args:
        if "instances" in kwargs:
            # append len of instances
            appendix = f"({len(kwargs['instances'])} instances"
        if "papers" in kwargs:
            if appendix:
                appendix += ", "
            appendix += f"{len(kwargs['papers'])} papers"
        if appendix:
            appendix += ")"
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds" + appendix)
        return result

    return wrapper


# helpful functions
def index_all(input_list, item):
    return [i for i, x in enumerate(input_list) if x == item]


def split_string(input_string, delimiters=[" ", "-", "_"]):
    for delimiter in delimiters:
        input_string = " ".join(input_string.split(delimiter))
    return input_string.split()


def path_cleaning(text):
    mapping = {
        "\\": "/",
    }
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


# represent a dict
import csv
import os
from itables import init_notebook_mode, show
import json

# better represent dataframes
if not config.for_git:
    init_notebook_mode(all_interactive=True)


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
    show(input_df)

    ## Ontology


import json

from bnw_tools.extract import util_zotero


class KnowledgeGraphEntryFactory:
    @staticmethod
    def create(label=None, properties=None):
        if properties:
            if "instance_of" in properties:
                return Instance(label=label, properties=properties)
            elif "subclass_of" in properties:
                return InstanceType(label=label, properties=properties)
        return KnowledgeGraphEntry(label=label, properties=properties)


class KnowledgeGraphEntry:
    def __init__(self, label=None, properties={}):
        self.label = label

        self.set_properties(properties)

    def set_properties(self, properties, overwrite=False):
        mapping = {
            "name": "label",
            "instance_type": "instance_of",
            "also_known_as": "aliases",
            "uri": "wikidata_uri",
        }

        for prop, value in properties.items():
            if prop in mapping:
                prop = mapping[prop]
            if prop == "wikidata_uri" and isinstance(value, list):
                prop = "wikidata_candidates"
            # if not overwrite and hasattr(self, prop) and getattr(self, prop):
            if hasattr(self, prop):
                if not value:
                    continue
                current = getattr(self, prop)
                if current == value:
                    continue
                if isinstance(current, list):
                    if not isinstance(value, list):
                        value = [value]
                    for v in value:
                        if v not in current:
                            current.append(v)
                    continue
                elif current and not overwrite:
                    continue
            setattr(self, prop, value)

    def get(self, label, default=None):
        if hasattr(self, label):
            return getattr(self, label)
        return default

    def update(self, other: KnowledgeGraphEntry, force=False):
        was_updated = False
        if self.label and other.label and self.label != other.label:
            return False
        for prop, value in other.__dict__.items():
            if not value:
                continue
            if not hasattr(self, prop) or not getattr(self, prop) or force:
                setattr(self, prop, value)
                was_updated = True
        return was_updated


# Class,URI,Label,Laymans Term,Status
## e.g. process,software,data item,data model,data format specification,
class InstanceType(KnowledgeGraphEntry):  # Class

    ## Will be shifted to the individual class instances
    # properties = {
    #     "default": [
    #         "name",
    #         "instance_type",
    #         "uri",
    #         "also_known_as",
    #     ],
    #     "software": [
    #         "data visualization",
    #         "data validation",
    #         "data reasoning",
    #     ],
    #     "format": ["neutral"],
    # }

    def __init__(
        self,
        label=None,
        properties={},
        instance_properties={},
    ):
        self.label: str = label
        self.source: str = None
        self.subclass_of: list[str] = []
        self.aliases: list[str] = []
        self.tags: list[str] = []
        self.wikidata_uri: str = None
        self.orkg_uri: str = None
        self.wikidata_candidates: list[str] = []
        self.orkg_candidates: list[str] = []
        self.instance_properties: dict = instance_properties

        self.set_properties(properties)


class Instance(KnowledgeGraphEntry):
    def __init__(
        self, label=None, instance_type=None, properties={}, properties_from_class={}
    ):
        self.label: str = label
        self.source: str = None
        self.instance_of: list[str] = (
            []
            if not instance_type
            else [instance_type] if isinstance(instance_type, str) else instance_type
        )
        self.aliases: list[str] = []
        self.tags: list[str] = []
        self.wikidata_uri: str = None
        self.orkg_uri: str = None
        self.wikidata_candidates: list[str] = []
        self.orkg_candidates: list[str] = []

        self.set_properties(properties, properties_from_class)

    def set_properties(self, properties, properties_from_class={}, overwrite=False):
        candidates = properties_from_class
        for candidate in candidates:
            if candidate not in properties:
                properties[candidate] = None

        super().set_properties(properties, overwrite)


class Ontology:
    def __init__(self):
        self.classes: dict[str, InstanceType] = {}
        self.instances: dict[str, Instance] = {}
        self.relations: dict[str, dict[str, str]] = {}
        ## TODO: Consider making papers a subclass of instances

        self.instances_by_class = {}

        # if instance_types_dicts:
        #     self.add_instance_types(instance_types_dicts)

    def reorder_classes(self, order):
        reordered_classes = {k: self.classes[k] for k in order}
        for k in self.classes:
            if k not in order:
                reordered_classes[k] = self.classes[k]
        self.classes = reordered_classes
        self.instances_by_class = {k: self.instances_by_class[k] for k in self.classes}

    def add_instances(self, instances):
        if isinstance(instances, list) or isinstance(instances, set):
            # simple list of instances
            for instance in instances:
                self.add_instance(instance=instance)

        elif isinstance(instances, dict):
            for key, value in instances.items():
                if isinstance(value, Instance):
                    # Dict is label: instance
                    self.add_instance(instance=value, instance_label=key)

                elif isinstance(value, list) or isinstance(value, set):
                    # Dict is class : [instance]
                    for instance in value:
                        self.add_instance(instance=instance, instance_type=key)

                elif isinstance(value, dict):
                    # Dict is class : {label: instance}
                    for label, instance in value.items():
                        # Dict is class : {label: instance}
                        self.add_instance(
                            instance=instance, instance_label=label, instance_type=key
                        )

    def add_class(
        self,
        instance_type: InstanceType,
        label=None,
        properties=None,
        instance_properties=None,
        force=False,
    ):
        if isinstance(instance_type, str):
            # instance is just a label
            label = instance_type
            instance = InstanceType(
                label, properties=properties, instance_properties=instance_properties
            )

        elif isinstance(instance_type, dict):
            # instance is still a dict
            properties = instance_type
            label = properties.get("label", label)
            instance = InstanceType(
                label, properties=properties, instance_properties=instance_properties
            )

        if not label:
            label = instance_type.label
        # if not subclasses:
        #     subclasses = instance_type.subclass_of

        if label in self.classes:
            was_added = self.classes[label].update(instance_type, force=force)
            if not was_added:
                return False
        else:
            self.classes[label] = instance_type
        return True

    def add_instance(
        self, instance: Instance, instance_label=None, instance_type=None, force=False
    ):
        if isinstance(instance, str):
            # instance is just a label
            instance_label = instance
            instance = Instance(instance_label, instance_type)

        elif isinstance(instance, dict):
            # instance is still a dict
            properties = instance
            instance_label = properties.get("label", instance_label)
            instance_type = properties.get("instance_of", instance_type)
            instance_properties = self.get_properties_from_class(instance_type)
            instance = Instance(
                instance_label,
                instance_type,
                properties=properties,
                properties_from_class=instance_properties,
            )

        if not instance_label:
            instance_label = instance.label
        if not instance_type:
            instance_type = instance.instance_of

        instance_label = instance_label.strip()

        if instance_label in self.instances:
            was_added = self.instances[instance_label].update(instance, force=force)
            if not was_added:
                return False
        else:
            self.instances[instance_label] = instance
        self.update_maps(instance_label, instance_type)
        return True

    def update_maps(self, instance_label, instance_type):
        # self.instances: dict[str, Instance] = {}
        if isinstance(instance_type, list):
            for it in instance_type:
                self.update_maps(instance_label, it)
            return
        if instance_type not in self.classes:
            self.classes[instance_type] = InstanceType(instance_type)

        # self.instances_by_class = {}
        if instance_type not in self.instances_by_class:
            self.instances_by_class[instance_type] = {}
        self.instances_by_class[instance_type][instance_label] = self.instances[
            instance_label
        ]

    def get_properties_from_class(self, instance_type):
        if instance_type in self.classes:
            return self.classes[instance_type].instance_properties
        else:
            return {}

    # def add_instance_types(self, instance_types_dicts):
    #     for instance_type, instances in instance_types_dicts.items():
    #         if instance_type not in self.classes:
    #             self.classes[instance_type] = InstanceType(instance_type)
    #         for instance_label in instances:
    #             if instance_label not in self.instances:
    #                 instance_properties = self.get_properties_from_class(instance_type)
    #                 instance = Instance(
    #                     instance_label,
    #                     instance_type,
    #                     properties_from_class=instance_properties,
    #                 )
    #                 self.add_instance(instance, instance_label, instance_type)

    def get(self, label):
        if hasattr(self, label):
            if label == "instances_by_class":
                self.update_instance_by_class()
            return getattr(self, label)
        elif label in self.instances:
            return self.instances[label]
        elif label in self.classes:
            return self.classes[label]
        return None

    def update_instance_by_class(self):
        UNKNOWNTYPE = "unknown_instance_type"
        for label, instance in self.instances.items():
            instance_types = instance.instance_of
            if not isinstance(instance_types, list):
                instance_types = [instance_types]
            for instance_type in instance_types:
                if instance_type not in self.instances_by_class:
                    self.instances_by_class[instance_type] = {}
                self.instances_by_class[instance_type][label] = instance
            if not instance_types:
                if UNKNOWNTYPE not in self.instances_by_class:
                    self.instances_by_class[UNKNOWNTYPE] = {}
                self.instances_by_class[UNKNOWNTYPE][label] = instance
        if UNKNOWNTYPE in self.instances_by_class:
            Warning(
                f"Instances without instance_of: {len(self.instances_by_class[UNKNOWNTYPE])}"
            )

    def get_instances_of_type(self, instance_type):
        if self.instances_by_class:
            if instance_type in self.instances_by_class:
                return self.instances_by_class[instance_type]
        return {}
        # updated = False
        # while True:
        #     if self.instances_by_class:
        #         if instance_type in self.instances_by_class:
        #             return self.instances_by_class[instance_type]
        #     if not updated:
        #         self.update_instance_by_types()
        #         updated = True
        #     else:
        #         return {}

    def sort(self):
        # FIXME: This is not working
        Warning("This function is not working")
        pass
        # sort according to the following order:
        # first: all instances that have wikidata_uri and orkg_uri
        # then: all instances that have wikidata_uri
        # then: all instances that have orkg_uri
        # then: all instances that have wikidata_candidates
        # then: all instances that have orkg_candidates
        # self.instances = {
        #     k: self.instances[k]
        #     for k in sorted(
        #         self.instances,
        #         key=lambda x: (
        #             0 if x[1].wikidata_uri and x[1].orkg_uri else 1,
        #             0 if x[1].wikidata_uri else 1,
        #             0 if x[1].orkg_uri else 1,
        #             0 if x[1].wikidata_candidates else 1,
        #             0 if x[1].orkg_candidates else 1,
        #         ),
        #     )
        # }

        # self.instances = {
        #     k: self.instances[k]
        #     for k in sorted(
        #         self.instances,
        #         key=lambda x: (
        #             0
        #             if isinstance(self.instances[x].wikidata_uri, str)
        #             else (
        #                 len(self.instances[x].wikidata_uri)
        #                 if isinstance(self.instances[x].wikidata_uri, list)
        #                 else 99999
        #             )
        #             # len(self.instances[x].uri) if isinstance(self.instances[x].uri, list) else 0
        #         ),
        #     )
        # }

    def save(self, config: Config = None, path=None, name="instances.csv", sort=True):
        # FIXME: Needs to be completely reworked
        Warning("This function is not working")
        pass
        # if not path:
        #     path = config.ontology_path
        # if not name.endswith(".csv"):
        #     name += ".csv"
        # if sort:
        #     self.sort()
        # filepath = os.path.join(path, name)
        # # TODO: make a way that this is generated dynamically
        # cols = [name for sublist in Instance.properties.values() for name in sublist]
        # header = config.csv_separator.join(cols)

        # # backup
        # if os.path.exists(filepath):
        #     try:
        #         temp = Ontology()
        #         temp.load(config, path, name)
        #         # current file is valid, so backup
        #         backup_path = filepath.replace(".csv", "_backup.csv")
        #         if os.path.exists(backup_path):
        #             os.remove(backup_path)
        #         os.rename(filepath, backup_path)
        #     except:
        #         pass

        # with open(filepath, "w", encoding="utf8") as f:
        #     f.write(header + "\n")
        #     for instance in self.instances.values():
        #         line = []
        #         for col in cols:
        #             if hasattr(instance, col):
        #                 entry = getattr(instance, col) or ""
        #                 while isinstance(entry, dict) and list(entry.keys()) == [col]:
        #                     entry = entry[col]
        #                 if isinstance(entry, dict):
        #                     entry = json.dumps(entry)
        #                 elif isinstance(entry, list):
        #                     entry = json.dumps(entry)
        #                 elif isinstance(entry, int):
        #                     entry = str(entry)
        #                 if config.csv_separator in entry:
        #                     entry = f'"{entry}"'
        #                 line.append(entry)
        #             else:
        #                 line.append("")
        #         f.write(config.csv_separator.join(line) + "\n")

    def load(self, config, path=None, name="instances.csv", try_backup=True):
        if not path:
            path = config.ontology_path
        if not name.endswith(".csv"):
            name += ".csv"
        filepath = os.path.join(path, name)

        try:
            with open(filepath, "r", encoding="utf8") as f:
                lines = f.read().splitlines()
            cols = lines[0].split(config.csv_separator)
            for line in lines[1:]:
                data = line.split(config.csv_separator)
                for i in range(len(data)):
                    if i == len(data):
                        break
                    while (
                        data[i].count('"') % 2 == 1
                        or data[i].count("[") != data[i].count("]")
                        or data[i].count("{") != data[i].count("}")
                    ):
                        data[i] += "," + data.pop(i + 1)
                    # has separator
                    if data[i].startswith('"') and data[i].endswith('"'):
                        data[i] = data[i][1:-1]
                    # json
                    if data[i].startswith("{") and data[i].endswith("}"):
                        data[i] = json.loads(data[i])
                    # list
                    if data[i].startswith("[") and data[i].endswith("]"):
                        data[i] = json.loads(data[i])
                    # int
                    if isinstance(data[i], str) and data[i] == "-1":
                        # TODO: Make this more general
                        data[i] = int(data[i])
                if len(data) != len(cols):
                    raise Exception(f"Error: Line {line} has too few columns.")
                instance = Instance(
                    # data[0],
                    # data[1],
                    properties={cols[i]: data[i] for i in range(len(data)) if data[i]},
                    properties_from_class=self.get_properties_from_class(data[1]),
                )
                self.add_instance(instance)
        except Exception as e:
            backup_name = name.replace(".csv", "_backup.csv")
            if try_backup and os.path.exists(os.path.join(path, backup_name)):
                self.load(config, path, backup_name, try_backup=False)
            else:
                raise e

    @time_function
    def get_metadata(self, label, path=None, return_results=False):
        # papers_metadata = {}
        if label in self.classes:
            candidates = self.get_instances_of_type(label)
        elif label in self.instances:
            candidates = {label: self.instances[label]}
        else:
            print(f"{label} not found in instances or classes.")
            return {}

        bib_resources = util_zotero.BibResources(path) if path else None

        counter = 0
        for instance_label, instance in candidates.items():
            for entry in bib_resources.entries:
                if (
                    hasattr(bib_resources.entries[entry], "file")
                    and instance_label in bib_resources.entries[entry].file
                ):
                    instance.set_properties(bib_resources.entries[entry].get_dict())
                    counter += 1
                    del bib_resources.entries[entry]
                    break
        if len(candidates) > 1:
            print(
                f"{counter} out of {len(candidates)} {label} instances have metadata."
            )
        if return_results:
            return candidates


def curate_instances(instances, path=None):
    if not path:
        path = "whitelist.csv"
    if os.path.exists(path):
        with open(path, "r", encoding="utf8") as f:
            whitelist = f.read().splitlines()

    for instance in instances:
        if instance not in whitelist:
            instances.remove(instance)
    return instances


class Director:
    def __init__(self, config: Config):
        self.config = config
        # self.ontology = Ontology()
        # self.ontology.load(config)

        self.builder: dict[str, Builder] = {}
        self.products = {}

    def set(self, key, value):
        setattr(self, key, value)

    def get(self, key):
        return getattr(self, key)

    def run(self):
        # self.extract_papers()
        pass


class PaperInstanceDirector(Director):
    def __init__(self, config: Config, ontology: Ontology = None):
        super().__init__(config)
        self.ontology: Ontology = None

        self.classes: dict[str, InstanceType] = {}
        self.papers: dict[str, Instance] = {}
        self.instances: dict[str, Instance] = {}  # any non-paper instances

        self.included_papers: dict[str, Instance] = {}
        self.excluded_papers: dict[str, Instance] = {}

        # products
        # self.paper_instance_occurrence_matrix: np.ndarray = None

        if ontology:
            self.link_ontology(ontology)
        else:
            self.ontology = Ontology()
            self.ontology.load(config)
            self.link_ontology(self.ontology)

    def link_ontology(self, ontology: Ontology):
        self.ontology = ontology

        # self.classes = {k: v for k, v in ontology.classes.items() if k not in ["paper"]}
        self.classes = {k: v for k, v in ontology.classes.items()}

        for type, dict_ in ontology.get("instances_by_class").items():
            if type == "paper":
                self.papers.update(dict_)
            else:
                self.instances.update(dict_)

        self.reduce_to_reviewed_papers()

    def get_papers(self):
        papers = {}
        for file in os.listdir(self.config.papers_path):
            if file.endswith(".json"):
                papers[file[:-5]] = {
                    "nlp_path": path_cleaning(
                        os.path.join(self.config.papers_path, file)
                    )
                }

        self.ontology.add_instances({"paper": papers})
        self.ontology.get_metadata("paper", config.folder_path)

    def reduce_to_reviewed_papers(self):
        review_path = self.config.review_path
        # todo: sort by review score + average rank
        ## TODO: Make this a function that imports more data from the reivew files
        included_identifier = {
            3: "review_score:: 3",
            4: "review_score:: 4",
            5: "review_score:: 5",
        }
        excluded_identifier = {
            2: "review_score:: 2",
            1: "review_score:: 1",
            0: "review_score:: 0",
        }
        for file in os.listdir(review_path):
            if file.endswith(".md"):
                paper_name = file[:-3]
                if paper_name in self.papers:
                    paper = self.papers[paper_name]
                    if (
                        paper_name in self.included_papers
                        or paper_name in self.excluded_papers
                    ):
                        continue
                    # check if file contains "reviewed"ArithmeticError
                    with open(
                        os.path.join(review_path, file), "r", encoding="utf8"
                    ) as f:
                        content = f.read()
                        for score, text in included_identifier.items():
                            if text in content:
                                paper.review_score = score
                                self.included_papers[paper_name] = paper
                                break
                        for score, text in excluded_identifier.items():
                            if text in content:
                                self.excluded_papers[paper_name] = paper
                                break
        if self.config.only_included_papers:
            self.papers = {k: v for k, v in self.included_papers.items()}
        self.sort_papers()
        if self.included_papers:
            self.included_papers = self.sort_papers(self.included_papers)
        if self.excluded_papers:
            self.excluded_papers = self.sort_papers(self.excluded_papers)

    def sort_papers(self, papers=None):
        saveback = False
        if not papers:
            saveback = True
        papers = papers or self.papers
        # TODO: see if "if" and "else" can be deleted
        papers = {
            x: papers[x]
            for x in sorted(
                papers,
                key=lambda x: (
                    getattr(papers[x], "year", "9999")
                    if hasattr(papers[x], "year")
                    else "9999"
                ),
            )
        }
        if saveback:
            self.papers = papers
        else:
            return papers
        # papers_metadata = self.ontology.get_metadata("paper")
        # papers = sorted(
        #     papers,
        #     key=lambda x: (
        #         getattr(self.papers[x], "year", "9999")
        #         if x in papers_metadata and "year" in papers_metadata[x]
        #         else "9999"
        #     ),
        # )

    def get_instances(self):
        self.builder["InstanceBuilder"] = InstanceBuilder(self)
        instances_by_type = self.builder["InstanceBuilder"].build()
        self.ontology.add_instances(instances_by_type)
        self.ontology.reorder_classes(instances_by_type.keys())
        self.ontology.save(self.config)
        self.link_ontology(self.ontology)

    def update_instance(self, instance, label):
        if "paper" in getattr(instance, "instance_of"):
            return False

        if label not in self.instances:
            print(f"Instance {label} will be newly added to instances.")

        was_added = self.ontology.add_instance(instance, label)
        if was_added:
            if instance.instance_of == "paper":
                self.papers[label] = instance
            else:
                self.instances[label] = instance
        return was_added

    def update_class(self, instance_type, label):
        was_added = self.ontology.add_class(instance_type, label)
        if was_added:
            self.classes[label] = instance_type
        return was_added

    def sync(self, other):
        updates_done = False
        attributes = ["papers", "instances", "classes"]
        for attribute in attributes:
            if hasattr(other, attribute):
                for label, instance in getattr(other, attribute).items():
                    if isinstance(instance, Instance):
                        res = self.update_instance(instance, label)
                    elif isinstance(instance, InstanceType):
                        res = self.update_class(instance, label)
                    if res:
                        updates_done = True
                setattr(other, attribute, getattr(self, attribute))
        if updates_done:
            self.ontology.save(self.config)

    def build_obsidian_folder(self):
        self.builder["ObsidianFolder"] = ObsidianFolderBuilder(self)
        self.sync(self.builder["ObsidianFolder"])
        self.builder["ObsidianFolder"].build()

    ## Sorting of instances

    # def remove_zeros(
    #     self, matrix=None, columns=True, rows=True, row_lists=None, column_lists=None
    # ):
    #     matrix = matrix or self.paper_instance_occurrence_matrix

    #     # remove all columns that are all zeros
    #     if columns:
    #         deleted_columns = np.all(matrix == 0, axis=0)
    #         matrix = matrix[:, ~np.all(matrix == 0, axis=0)]

    #     # remove all rows that are all zeros
    #     if rows:
    #         deleted_rows = np.all(matrix == 0, axis=1)
    #         matrix = matrix[~np.all(matrix == 0, axis=1)]

    #     return matrix, [deleted_columns, deleted_rows]

    # def handle_deletions(self, input, deletions, rows=True):
    #     """
    #     input: list, dict or np.ndarray
    #     deletions: list of bools
    #     rows: if True, deletions[1] is used, else deletions[0]
    #     """
    #     delID = 1 if rows else 0

    #     if deletions[delID].any():
    #         # rows were deleted, in this case: papers
    #         if isinstance(input, list):
    #             input = [
    #                 item for i, item in enumerate(input) if not deletions[delID][i]
    #             ]
    #         elif isinstance(input, dict):
    #             input = {
    #                 key: item
    #                 for i, (key, item) in enumerate(input.items())
    #                 if not deletions[delID][i]
    #             }
    #         elif isinstance(input, np.ndarray):
    #             input = input[~deletions[delID]]
    #     return input

    # def reorder_matrix(self, new_order):
    #     self.paper_instance_occurrence_matrix = self.paper_instance_occurrence_matrix[
    #         :, new_order
    #     ]
    #     self.paper_instance_occurrence_matrix, deletions = self.remove_zeros()
    #     self.papers = self.handle_deletions(self.papers, deletions)

    def sort_instances(self):
        if self.builder["occurrence_matrix"].matrix is None:
            self.setup_occurence_matrix()

        indexed_instances = {
            instance: i for i, instance in enumerate(self.instances.keys())
        }

        instance_occurrences = {}

        for i, instance_label in enumerate(self.instances.keys()):
            instance_occurrences[instance_label] = (
                self.builder["occurrence_matrix"].matrix[:, i].sum()
            )

        sorted_instances = {
            k: float(v)
            for k, v in sorted(
                instance_occurrences.items(), key=lambda item: item[1], reverse=True
            )
            if v > 0
        }

        filepath = os.path.join(self.config.get_output_path(), "instance_occurrences")
        with open(filepath + ".json", "w", encoding="utf-8") as f:
            json.dump(sorted_instances, f, ensure_ascii=False, indent=4)

        sorted_instance_list = list(sorted_instances.keys())

        instance_types_dict = self.ontology.get("instances_by_class")

        type_lists = [[] for _ in range(len(instance_types_dict))]
        for instance in sorted_instance_list:
            for type_ID, instance_type in enumerate(instance_types_dict):
                if instance in instance_types_dict[instance_type]:
                    type_lists[type_ID].append(instance)
        type_sorted_instances = [item for sublist in type_lists for item in sublist]

        new_order = [0] * len(sorted_instance_list)
        sorted_instances = {}
        for i, instance in enumerate(type_sorted_instances):
            new_order[i] = indexed_instances[instance]
            sorted_instances[instance] = self.instances[instance]

        self.instances = sorted_instances

        # sort all matrixes accordingly
        new_order = np.array(new_order)

        self.builder["occurrence_matrix"].reorder_matrix(new_order)
        self.papers = self.builder["occurrence_matrix"].handle_deletions(self.papers)

        self.builder["occurrence_matrix"].instances = self.instances
        self.builder["occurrence_matrix"].papers = self.papers

    def setup_occurence_matrix(self):
        self.builder["occurrence_matrix"] = OccurrenceMatrixBuilder(self)
        self.builder["occurrence_matrix"].build()
        self.builder["occurrence_matrix"].save()
        # self.paper_instance_occurrence_matrix = self.builder["occurrence_matrix"].matrix
        self.sort_instances()

    # def run(self):
    #     self.extract_papers()
    #     self.extract_reviews()
    #     self.extract_ontology()
    #     self.extract_orkg()
    #     self.extract_obsidian()

    # def extract_papers(self):
    #     # Extract papers from the papers folder
    #     pass

    # def extract_reviews(self):
    #     # Extract reviews from the reviews folder
    #     pass

    # def extract_ontology(self):
    #     # Extract ontology from the ontology folder
    #     pass

    # def extract_orkg(self):
    #     # Extract orkg from the orkg folder
    #     pass

    # def extract_obsidian(self):
    #     # Extract obsidian from the obsidian folder
    #     pass


director = PaperInstanceDirector(config)
# director.set("ontology", ontology)


class Builder:
    def __init__(self, director: Director, config: Config = None):
        self.director: Director = director
        self.config = config or director.config

    def build(self):
        pass


class MatrixBuilder(Builder):
    def __init__(self, director: Director):
        super().__init__(director)

        self.matrix: np.ndarray = None
        self.row_labels = []  # papers
        self.col_labels = []  # instances

        self.deletions = [np.array([]), np.array([])]
        # TODO: Likely add more proerties to map from full corpus to reduced corpus

    def save(self, name="some_matrix"):
        self.exporter = MatrixExporter(
            self.director, self.matrix, self.row_labels, self.col_labels, name
        )

    def remove_zeros(self, columns=True, rows=True):
        # remove all columns that are all zeros
        # setup deleted_columns empty at first:
        deleted_columns, deleted_rows = self.deletions
        if columns:
            deleted_columns = np.all(self.matrix == 0, axis=0)
            self.matrix = self.matrix[:, ~np.all(self.matrix == 0, axis=0)]

        # remove all rows that are all zeros
        if rows:
            deleted_rows = np.all(self.matrix == 0, axis=1)
            self.matrix = self.matrix[~np.all(self.matrix == 0, axis=1)]
        self.deletions = [deleted_columns, deleted_rows]

    def handle_deletions(self, input, deletions=None, rows=True):
        """
        input: list, dict or np.ndarray
        deletions: list of bools
        rows: if True, deletions[1] is used, else deletions[0]
        """
        delID = 1 if rows else 0

        if not deletions:
            deletions = self.deletions

        if deletions[delID].any():
            # rows were deleted, in this case: papers
            if isinstance(input, list):
                input = [
                    item for i, item in enumerate(input) if not deletions[delID][i]
                ]
            elif isinstance(input, dict):
                input = {
                    key: item
                    for i, (key, item) in enumerate(input.items())
                    if not deletions[delID][i]
                }
            elif isinstance(input, np.ndarray):
                input = input[~deletions[delID]]
        return input

    def reorder_matrix(self, new_order, cols=True):
        if cols:
            self.matrix = self.matrix[:, new_order]
        else:
            self.matrix = self.matrix[new_order, :]
        self.remove_zeros()
        # this isn't quite right anymore
        # self.papers = self.handle_deletions(self.papers, self.deletions)


class OccurrenceMatrixBuilder(MatrixBuilder):
    def __init__(self, director: PaperInstanceDirector, papers=None, instances=None):
        super().__init__(director)
        self.director: PaperInstanceDirector = director

        self.papers = papers or self.director.papers  # first dimension
        self.instances = instances or self.director.instances  # second dimension

    def count_occurrences(self, papers, instances):
        papers = papers or self.papers
        instances = instances or self.instances

        occurrences = np.zeros((len(papers), len(instances)), dtype=int)

        for p, paperpath in enumerate(papers.values()):
            if isinstance(paperpath, dict) or isinstance(paperpath, Instance):
                paperpath = paperpath.get("nlp_path", None)
            with open(paperpath, "r", encoding="utf8") as f:
                paper = json.load(f)
                for i, instance in enumerate(instances):
                    present = True
                    pieces = split_string(instance)
                    for piece in pieces:
                        if piece.lower() not in paper["bag_of_words"]:
                            present = False
                            break

                    # if instance == "system integration":
                    #     if "Liu und Hu - 2013 - A reuse oriented representation model for capturin" in paperpath:
                    #         print(present)
                    if present:
                        occurrences[p][i] = 1
        return occurrences

    def build(self, papers=None, instances=None):
        self.matrix = self.count_occurrences(papers, instances)
        # process_matrix(
        #     self.config,
        #     self.matrix,
        #     list(self.papers.keys()),
        #     list(self.instances.keys()),
        #     name="paper_instance_occurrence_matrix",
        # )
        # return self.matrix

        # visualize co-occurrences


import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import pandas as pd
from __future__ import annotations


class MatrixExporter(Builder):
    def __init__(
        self,
        director: Director,
        matrix: np.ndarray,
        rows: List[str],
        columns: List[str] = None,
        name: str = "some_matrix",
        format=".png",
        path=None,
    ):
        self.director = director
        self.config = director.config
        self.matrix = matrix
        self.rows = rows
        self.columns = (
            columns or rows
        )  # if columns are not given, assume symmetric matrix
        self.name: str = name
        self.format: str = format
        self.output_path: str = path or self.config.get_output_path()
        self.visualization_path = self.config.get_output_path(visualization=True)
        self.mode = "sqrt"

        self.size_x = None
        self.size_y = None
        self.dpi = None

    def build(self):
        self.to_csv()
        if config.visualize:
            path = config.get_output_path(path, visualization=True)
            self.visualize_matrix()
            self.sankey()
            self.visualize_matrix_graph()

    def to_csv(self):
        df = pd.DataFrame(self.matrix, columns=self.columns, index=self.rows)
        filepath = os.path.join(self.output_path, self.name)
        df.to_csv(
            filepath + ".csv",
            sep=self.config.csv_separator,
            decimal=self.config.csv_decimal,
        )

    def get_figsize(self):
        if self.size_x and self.size_y:
            return self.size_x, self.size_y
        ## Calculate the maximum size of the plot
        dpi = 300
        max_dpi = 600
        if config.for_git:
            dpi = 96
            max_dpi = 200
        max_pixel = 2**16  # Maximum size in any direction
        max_size = max_pixel / dpi  # Maximum size in any direction
        max_size_total = max_size * max_size  # Maximum size in total
        max_size_total *= 0.05  # produce smaller files

        # Experience value of space required per cell
        factor = 0.18
        size_x: float = 2 + len(self.columns) * factor
        size_y: float = 3 + len(self.rows) * 0.8 * factor

        while size_x * size_y < max_size_total and dpi < max_dpi:
            dpi /= 0.95
            max_size_total *= 0.95

        if dpi > max_dpi:
            dpi = max_dpi

        while size_x * size_y > max_size_total:
            dpi *= 0.95
            max_size_total /= 0.95

        self.size_x = size_x
        self.size_y = size_y
        self.dpi = dpi

        return size_x, size_y

    def visualize_matrix(self) -> None:
        """
        Visualizes a matrix as a heatmap.
        matrix: The matrix to visualize
        rows: The labels for the rows
        columns: The labels for the columns
        name: The name of the file to save
        format: The format of the file to save (default: '.png', also accepts '.svg' and '.pdf', also accepts a list of formats)
        """
        # config: Config,
        # matrix: np.ndarray,
        # rows: list[str],
        # columns: list[str] = None,
        # name: str = "some_matrix",
        # format=".png",
        # path=None,

        fig, ax = plt.subplots(figsize=self.get_figsize(), dpi=self.dpi)

        cax = ax.matshow(self.matrix, cmap="viridis")

        # use labels from instance_occurrences
        ax.set_xticks(range(len(self.columns)))
        ax.set_xticklabels(list(self.columns), fontsize=10, rotation=90)
        ax.set_yticks(range(len(self.rows)))
        ax.set_yticklabels(list(self.rows), fontsize=10)

        # # adjust the spacing between the labels
        # plt.gca().tick_params(axis='x', which='major', pad=15)
        # plt.gca().tick_params(axis='y', which='major', pad=15)

        # show the number of co-occurrences in each cell, if greater than 0
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                if self.matrix[i, j] == 0:
                    continue
                # if co_occurrences[i, j] > 100:
                #     continue

                # make sure the text is at most 3 digits and a dot
                decimals = 2
                if self.matrix[i, j] > 99:
                    decimals = 0
                elif self.matrix[i, j] > 9:
                    decimals = 1
                cell_text = round(self.matrix[i, j], decimals)
                if decimals == 0:
                    cell_text = int(cell_text)
                plt.text(
                    j, i, cell_text, ha="center", va="center", color="white", fontsize=4
                )

        # plt.show()
        fig.tight_layout()

        # title
        plt.title(self.name)

        if isinstance(format, list):
            for f in format:
                if f[0] != ".":
                    f = "." + f
                filepath = os.path.join(path, name + f)
                fig.savefig(filepath)
        else:
            if format[0] != ".":
                format = "." + format
            filepath = os.path.join(self.visualization_path, self.name + format)
            fig.savefig(filepath)

    def visualize_matrix_graph(self):
        # config: Config,
        # matrix,
        # instances,
        # instance_types_dicts,
        # name="some_matrix_graph",
        # path=None,
        # node_size_mode="sqrt",
        # raise_mode="prune",
        if not self.instances:
            return

        SEED = config.proximity_seed or 17
        K_SPRRING = config.proximity_k_spring or 18
        MIN_VALUE = config.proximity_min_value or 0.01

        scale = len(instances) * 0.12
        # Create a new figure
        x = scale / 10 * 16
        y = scale / 10 * 9
        fig = plt.figure(figsize=(x, y))

        # normalize the proximity matrix
        matrix = matrix / matrix.max()

        # Make sure the matrix is not completely stretched out
        if matrix.min() < MIN_VALUE:
            if raise_mode == "prune":
                # remove every value that is below MIN_VALUE
                matrix = np.where(matrix < MIN_VALUE, 0, matrix)
            elif raise_mode == "sqrt":
                while np.min(matrix[np.nonzero(matrix)]) < MIN_VALUE:
                    matrix = np.sqrt(matrix)
            else:
                raise ValueError("Unknown raise mode")

        # alternatives are:
        # "linear" - take proximity as is
        # "sqrt" - sqrt(proximity)
        # "log" - log(proximity)
        if node_size_mode == "log":
            # TODO: see how this works with log(1)
            nodesize_map = [
                np.log(matrix[:, i].sum() + 1) for i in range(len(instances))
            ]
        elif node_size_mode == "sqrt":
            nodesize_map = [np.sqrt(matrix[:, i].sum()) for i in range(len(instances))]
        elif node_size_mode == "linear":
            nodesize_map = [matrix[:, i].sum() for i in range(len(instances))]
        else:
            nodesize_map = [matrix[:, i].sum() for i in range(len(instances))]

        # print(max(nodesize_map))
        # print(min(nodesize_map))

        nodesize_map = np.array(nodesize_map) / max(nodesize_map) * 1000

        # print(max(nodesize_map))
        # print(min(nodesize_map))

        # Create a graph from the proximity matrix
        G = nx.from_numpy_array(matrix)

        # Specify the layout
        pos = nx.spring_layout(
            G, seed=SEED, k=K_SPRRING / math.sqrt(G.order())
        )  # Seed for reproducibility

        color_map = []

        color = {
            "process": "#1f77b4",  # muted blue
            "software": "#ff7f0e",  # safety orange
            "data item": "#2ca02c",  # cooked asparagus green
            "data model": "#d62728",  # brick red
            "data format specification": "#9467bd",  # muted purple
            # "interchange format": "#8c564b",  # chestnut brown
            # "source": "#e377c2",  # raspberry yogurt pink
        }

        for instance in instances:
            added = False
            for instance_type in instance_types_dicts:
                if instance in instance_types_dicts[instance_type]:
                    color_map.append(color[instance_type])
                    added = True
                    break
            if not added:
                color_map.append("grey")

        # Draw the graph
        options = {
            "edge_color": "grey",
            "linewidths": 0.5,
            "width": 0.5,
            "with_labels": True,  # This will add labels to the nodes
            "labels": {i: label for i, label in enumerate(instances)},
            "node_color": color_map,
            "node_size": nodesize_map,
            # "edge_color": "white",
            # "alpha": 0.9,
        }

        # print(nx.is_weighted(G))

        # nx.set_edge_attributes(G, values = 1, name = 'weight')

        nx.draw(G, pos, **options, ax=fig.add_subplot(111))

        # Make the graph more spacious
        fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.9)

        # Create a patch for each color
        patches = [mpatches.Patch(color=color[key], label=key) for key in color]

        # Add the legend to the graph
        plt.legend(handles=patches, loc="upper right", fontsize="x-large")

        plt.show()

        # save plot to file
        filepath = os.path.join(path, name)
        fig.savefig(filepath + ".png")
        fig.savefig(filepath + ".svg")

        # nx.get_edge_attributes(G, 'weight')

    def sankey(self):
        # TODO: Implement a method to create one graph per Process
        # if path is None:
        #     path = config.get_output_path(path, visualization=True)
        # Convert the proximity matrix into a list of source nodes, target nodes, and values
        sources = []
        targets = []
        values = []

        x_pos = [0] * len(instances)
        y_pos = [0] * len(instances)
        color_map = [0] * len(instances)

        max_types = len(instance_types_dicts)
        type_positions = [0.1 + (i / max_types) * 0.8 for i in range(max_types)]

        color = {
            "process": "#1f77b4",  # muted blue
            "software": "#ff7f0e",  # safety orange
            "data item": "#2ca02c",  # cooked asparagus green
            "data model": "#d62728",  # brick red
            "data format specification": "#9467bd",  # muted purple
            "interchange format": "#8c564b",  # chestnut brown
            # "source": "#e377c2",  # raspberry yogurt pink
        }
        color = list(color.values())

        space = {}

        for i in range(matrix.shape[0]):
            source_type = None

            for j in range(matrix.shape[1]):
                target_type = None

                for type_depth, type in enumerate(instance_types_dicts):
                    if instances[i] in instance_types_dicts[type]:
                        source_type = type_depth
                    if instances[j] in instance_types_dicts[type]:
                        target_type = type_depth

                # only keep directly forward moving connections
                if target_type - source_type != 1:
                    continue

                # only keep forward moving connections
                if target_type - source_type <= 0:
                    continue

                if source_type not in space:
                    space[source_type] = {}
                if i not in space[source_type]:
                    space[source_type][i] = 0
                space[source_type][i] += matrix[i][j]

                if target_type not in space:
                    space[target_type] = {}
                if j not in space[target_type]:
                    space[target_type][j] = 0
                space[target_type][j] += matrix[i][j]

                x_pos[i] = type_positions[source_type]
                x_pos[j] = type_positions[target_type]
                color_map[i] = color[source_type]
                color_map[j] = color[target_type]
                if matrix[i][j] > 0.0:  # Ignore zero values
                    sources.append(i)
                    targets.append(j)
                    values.append(matrix[i][j])

        for type in space:
            sum_values = sum(space[type].values())
            space[type] = {
                k: v / sum_values
                for k, v in sorted(
                    space[type].items(), key=lambda item: item[1], reverse=True
                )
            }

        # assign each instance a proper y position
        for type in space:
            bottom = 0.1
            for i, instance in enumerate(space[type]):
                y_pos[instance] = bottom
                bottom += space[type][instance] * 0.8

        nodes = dict(
            # pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=instances,
            color=color_map,
            x=x_pos,
            y=y_pos,
            align="right",
        )

        # Create a Sankey diagram
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=nodes, link=dict(source=sources, target=targets, value=values)
                )
            ]
        )

        fig.update_layout(width=1920, height=1080)

        fig.update_layout(title_text="Sankey Diagram", font_size=10)
        # fig.show()

        filepath = os.path.join(self.path, self.name)
        fig.write_image(filepath + ".png")
        fig.write_image(filepath + ".svg")
        fig.write_html(filepath + ".html")

        # Step 1: find occurrences of instances in bag of words of papers


import pandas as pd
import os
import json
import numpy as np


class InstanceBuilder(Builder):
    def __init__(self, director: Director):
        super().__init__(director)

    def build(self):
        instance_types_dicts = {}

        # paper_instance_occurrence_matrix = np.zeros((), dtype=int)

        # TODO: Delete first 2 lines and see why this throws error then
        instance_types_dicts = self.csv_to_dict_of_sets(config.csv_file, config)

        # Extract instance types that are actually property types
        instance_types_dicts, property_types_dicts = self.prune_properties(
            instance_types_dicts, properties_to_prune=self.config.properties
        )

        return instance_types_dicts

    def preprocess_csv(self, csv_file, config: Config, writeback=True):
        with open(csv_file, "r", encoding="utf8") as f:
            lines = f.readlines()

        expected_columns = len(lines[0].split(config.csv_separator))
        processed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if line.count('"') % 2 == 1:
                # if the number of quotes is odd, the line is not complete
                error = True
                for j in range(i + 1, len(lines)):
                    line = line + " " + lines[j].strip()
                    if line.count('"') % 2 == 0:
                        error = False
                        print(f"Merged rows {i} to {j}")
                        i = j + 1
                        break
                if error:
                    raise Exception(
                        f"Error: Lines {i} to {j-1} could not be processed. Odd number of quotes."
                    )
            else:
                i += 1
            if '""' in line:
                # remove quotes from line
                line = line.replace('""', "")
            if line.count('"') % 2 == 0:
                pos1 = line.find('"')
                while pos1 != -1:
                    pos2 = line.find('"', pos1 + 1)
                    if not config.csv_separator in line[pos1:pos2]:
                        line = line[pos1:pos2] + line[pos2 + 1 :]
                    pos1 = line.find('"', pos2 + 1)
            processed_lines.append(line)
        if writeback and len(processed_lines) != len(lines) or lines != processed_lines:
            print(
                f"CSV file improved, found {len(lines) - len(processed_lines)} errors."
            )
            with open(csv_file, "w", encoding="utf8") as f:
                f.write("\n".join(processed_lines))

        return processed_lines

    def csv_to_dict_of_sets(self, csv_file, config: Config, prune_nan=True):
        dict_of_sets = {}
        # try:
        #     df = pd.read_csv(csv_file)
        # except pd.errors.ParserError:
        #     print("Error parsing CSV file. Trying again with 'error_bad_lines=False'")
        # TODO: Specify modular separator and decimal here as well

        self.preprocess_csv(csv_file, config)

        try:
            df = pd.read_csv(
                csv_file,
                on_bad_lines="warn",
                delimiter=config.csv_separator,
                encoding="utf-8",
            )
        except:
            print("Error parsing CSV file. Trying again with 'encoding=ISO-8859-1'")
            df = pd.read_csv(
                csv_file,
                on_bad_lines="warn",
                delimiter=config.csv_separator,
                encoding="ISO-8859-1",
            )
        for column in df.columns:
            if df[column].isnull().all():
                print(f"column {column} is empty")
                dict_of_sets[column] = set([np.nan])
            else:
                dict_of_sets[column] = set(df[column].str.lower())
            if prune_nan and np.nan in dict_of_sets[column]:
                dict_of_sets[column].remove(np.nan)

            # Will be added in next version
            deletes = []
            adds = []
            for original_entry in dict_of_sets[column]:
                entry = original_entry.strip()
                while entry.startswith('"'):
                    entry = entry[1:]
                while entry.endswith('"'):
                    entry = entry[:-1]
                if original_entry != entry:
                    deletes.append(original_entry)
                    if entry not in dict_of_sets[column]:
                        adds.append(entry)
            for entry in deletes:
                dict_of_sets[column].remove(entry)
            dict_of_sets[column].update(adds)

        # saved_column = df['process'] #you can also use df['column_name']
        # delete all that exists in two or more columns
        for key in dict_of_sets:
            for other_key in dict_of_sets:
                if key != other_key:
                    dict_of_sets[key] = dict_of_sets[key].difference(
                        dict_of_sets[other_key]
                    )
        return dict_of_sets

    def prune_properties(
        self,
        instance_types_dicts,
        properties_to_prune=[],
        prune_empty=True,
        prune_x=True,
    ):
        properties = {}

        # merge "interchange format" into "data format specification"
        if "interchange format" in instance_types_dicts:
            pruned = []
            for key in instance_types_dicts["interchange format"]:
                if len(key) > 1:
                    instance_types_dicts["data format specification"].add(key)
                    pruned.append(key)
            for key in pruned:
                instance_types_dicts["interchange format"].remove(key)

        for instance_type in instance_types_dicts:
            prune = False
            if instance_type in properties_to_prune:
                prune = True
            elif prune_empty and len(instance_types_dicts[instance_type]) == 0:
                # prune empty sets
                prune = True
            elif prune_x and len(max(instance_types_dicts[instance_type], key=len)) < 2:
                # prune sets with only one character entries
                prune = True

            if prune:
                properties[instance_type] = instance_types_dicts[instance_type]

        for instance_type in properties:
            instance_types_dicts.pop(instance_type)

        return instance_types_dicts, properties

    # # ---------------------- Variables ----------------------

    # ## instances: A list of all instances, regardless of their type
    # # first all type 1, then all type 2, etc.
    # # if possible, instance sare ordered by their occurrence

    # ## instances_dicts: A dictionary of all different types (columns) of instances
    # #
    # # types:
    # #  - process
    # #  - software
    # #  - data item
    # #  - data model
    # #  - data format specification
    # #  - interchange format
    # #  - source
    # #
    # # instances_dicts['process']: A set of all instances of the type 'process'
    # #

    # instance_types_dicts = {}

    # ## paper_nlp_dict: A dictionary of all papers and their NLP data (as dict)

    # ## occurrences: A matrix of binary occurrences of instances in papers
    # #
    # # rows: papers
    # # columns: instances
    # # cells: 1 if instance is present in paper, 0 otherwise
    # #
    # paper_instance_occurrence_matrix = np.zeros((), dtype=int)

    # # ---------------------- Main ----------------------

    # # Usage example

    # # TODO: Delete first 2 lines and see why this throws error then
    # instance_types_dicts = csv_to_dict_of_sets(config.csv_file, config)

    # # Extract instance types that are actually property types
    # instance_types_dicts, property_types_dicts = prune_properties(
    #     instance_types_dicts, properties_to_prune=config.properties
    # )

    # def get_instances_list(instance_types_dicts):
    #     instances = []
    #     # merge all sets into one set
    #     for instance_type in instance_types_dicts:
    #         instances += instance_types_dicts[instance_type]
    #     return instances

    # # instances = get_instances_list(instance_types_dicts)


director.get_instances()


import requests


class WikiData:
    queries_done = 0
    new_labels = 0
    new_entries = 0

    def print_updates():
        print(f"Queries done: {WikiData.queries_done}")
        print(f"New labels: {WikiData.new_labels}")
        print(f"New entries: {WikiData.new_entries}")

    def __init__(self, config: Config = None):
        self.entries = {}
        self.label_entry_map = {}
        if config:
            self.load(config)

    def save(self, config, path=None, name="wikidata.json"):
        if not path:
            path = config.ontology_path
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(path, name)
        with open(filepath, "w", encoding="utf8") as f:
            data = self.__dict__
            json.dump(data, f)

    def load(self, config, path=None, name="wikidata.json"):
        if not path:
            path = config.ontology_path
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(path, name)
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf8") as f:
            data = json.load(f)
            for key, value in data.items():
                setattr(self, key, value)

    def query_wikidata(
        self, config: Config, label: str, select="label", limit=None, nested=False
    ):
        if select == "label" and not nested:
            if WikiData.queries_done > config.wikidata_query_limit:
                print("Wikidata query limit reached.")
                WikiData.print_updates()
                return False
            else:
                WikiData.queries_done += 1

        def transform_results(results):
            transformed = {}
            for result in results:
                item_uri = result["item"]["value"]
                item_label = result["itemLabel"]["value"]
                # Handle cases where altLabels or description might not be present
                alt_labels = result.get("altLabels", {}).get("value", "")
                description = result.get("description", {}).get("value", "")

                transformed[item_uri] = {
                    "itemLabel": item_label,
                    "altLabels": alt_labels,
                    "description": description,  # Include this line only if descriptions are desired
                }
            return transformed

        if not limit:
            limit = config.wikidata_query_limit
        endpoint_url = "https://query.wikidata.org/sparql"

        selection = {
            "label": f'?item rdfs:label "{label}"@en.',
            "altLabel": f'?item skos:altLabel "{label}"@en.',
        }

        # query = f"""
        # SELECT ?item ?itemLabel (GROUP_CONCAT(DISTINCT ?altLabel; separator = ", ") AS ?altLabels) WHERE {{
        # {selection[select]}
        # SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        # }}
        # GROUP BY ?item ?itemLabel
        # LIMIT {limit}
        # """

        query = f"""
        SELECT ?item ?itemLabel (GROUP_CONCAT(DISTINCT ?altLabel; separator = ", ") AS ?altLabels) 
        (SAMPLE(?description) AS ?description) WHERE {{
        {selection[select]}
        OPTIONAL {{ ?item skos:altLabel ?altLabel FILTER(LANG(?altLabel) = "en") }}
        OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        GROUP BY ?item ?itemLabel
        LIMIT {limit}
        """

        headers = {
            "User-Agent": "WDQS-example Python/%s.%s"
            % (requests.__version__, "MyScript"),
            "Accept": "application/json",
        }
        try:
            response = requests.get(
                endpoint_url, headers=headers, params={"query": query, "format": "json"}
            )
            response.raise_for_status()  # Raises stored HTTPError, if one occurred

            data = response.json()
            results = data["results"]["bindings"]
            results = transform_results(results)
            if select == "label":
                if len(results) < limit:
                    results_altLabel = self.query_wikidata(
                        config,
                        label,
                        select="altLabel",
                        limit=limit - len(results),
                        nested=True,
                    )
                    results.update(results_altLabel)
                if not nested:
                    if len(results) < limit and label.lower() != label:
                        results_lower = self.query_wikidata(
                            config,
                            label.lower(),
                            select=select,
                            limit=limit - len(results),
                            nested=True,
                        )
                        results.update(results_lower)
                    if len(results) < limit and label.capitalize() != label:
                        results_capitalize = self.query_wikidata(
                            config,
                            label.capitalize(),
                            select=select,
                            limit=limit - len(results),
                            nested=True,
                        )
                        results.update(results_capitalize)
                    if len(results) < limit and label.upper() != label:
                        results_upper = self.query_wikidata(
                            config,
                            label.upper(),
                            select=select,
                            limit=limit - len(results),
                            nested=True,
                        )
                        results.update(results_upper)

                    wikidata.label_entry_map[label] = list(results.keys())
                    WikiData.new_labels += 1
                    for key, value in results.items():
                        if key not in wikidata.entries:
                            wikidata.entries[key] = value
                            WikiData.new_entries += 1
            if results:
                return results
            else:
                # print("No matching Wikidata entry found.")
                return []

        except requests.exceptions.RequestException as e:
            print(f"Query failed: {e}")

    def get_uri(self, config: Config, label: str, allow_query=True):
        if label in self.label_entry_map:
            return self.label_entry_map[label]
        elif allow_query:
            res = self.query_wikidata(config, label)
            if res == False:
                print("Could not get URI. Query limit reached.")
                return False
            if res:
                self.save(config)
            return self.label_entry_map[label]


wikidata = WikiData(config)


@time_function
def query_wikidata_for_instances(
    config: Config, ontology: Ontology, wikidata: WikiData, stop_at=None
):
    for instance in ontology.instances.values():
        if instance.wikidata_uri:
            continue
        elif instance.wikidata_candidates:
            continue

        temp_res = []
        check = [instance.label] + getattr(instance, "also_known_as", [])
        i = 0
        while i < len(check):
            label = check[i]
            res = wikidata.get_uri(config, label)
            if res == False:
                print("Could not query properly. Not saving this instance.")
                ontology.save(config)
                return
            else:
                temp_res += res
            i += 1
        if temp_res:
            # We found some results
            instance.uri = temp_res
        else:
            instance.uri = -1
    ontology.save(config)
    WikiData.print_updates()


# TODO: Rework wikidata querrying
# query_wikidata_for_instances(config, ontology, wikidata)

# Obsidian


def fill_digits(var_s, cap=2):
    """Add digits until cap is reached"""
    var_s = str(var_s)
    while len(var_s) < cap:
        var_s = "0" + var_s
    return var_s


def get_clean_title(title, eID=None, obsidian=False):
    """
    Cleans a given title to make it suitable for filenames.

    Parameters:
    title (string): The title. "episode1"
    eID (int): The position of that episode in the playlist.

    Returns:
    string: cleaned title for use as filename
    """
    noFileChars = r'":\<>*?/'

    replace_dict = {
        "–": "-",
        "’": "´",
        " ": " ",
    }
    clean_title = title
    for each in noFileChars:
        clean_title = clean_title.replace(each, "")
    for key, value in replace_dict.items():
        clean_title = clean_title.replace(key, value)
    if obsidian:
        clean_title = clean_title.replace("#", "")
    if eID:
        clean_title = fill_digits(eID, 3) + "_" + clean_title
    return clean_title.strip()


def clear_name(name, can_be_folder=True):
    if can_be_folder:
        clean_title = name.replace("/", "[SLASH]")
    else:
        clean_title = name.replace("/", " or ")
    clean_title = get_clean_title(clean_title, obsidian=True)
    if can_be_folder:
        clean_title = clean_title.replace("[SLASH]", "/")
    if clean_title.startswith("https"):
        clean_title = clean_title[5:]
    while clean_title.startswith("/"):
        clean_title = clean_title[1:]
    if clean_title.startswith("www."):
        clean_title = clean_title[4:]
    while clean_title.endswith("/"):
        clean_title = clean_title[:-1]
    return clean_title


def parse_link(text):
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2]
    return text


class Node:
    def __init__(
        self,
        instance: KnowledgeGraphEntry = None,
        path: str = None,
        content: str = None,
    ):
        self.instance: KnowledgeGraphEntry = instance
        self.path = (
            path if path else self.instance.get("path", None) if self.instance else None
        )
        self.content = (
            content
            if content
            else self.instance.get("content", None) if self.instance else None
        )

        if path and not instance:
            self.load()

    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        elif hasattr(self.instance, key):
            return self.instance.get(key)
        elif key == "properties":
            return self.instance.__dict__
        else:
            return default

    def load(self, path=None):
        if not path:
            path = self.path
        with open(self.path, "r", encoding="utf8") as f:
            content = f.read()
            # read properties from yaml frontmatter
            yaml_find = 0
            lines = content.splitlines()
            properties = {}
            key = None
            value = None
            while lines:
                line = lines.pop(0)
                if line.startswith("---"):
                    # yaml frontmatter either begins or ends
                    yaml_find += 1

                elif yaml_find == 1:
                    # inside yaml frontmatter
                    # if ":" in line:
                    if not line.strip().startswith("-") and ":" in line:
                        if key:
                            properties[key] = value
                        pieces = line.split(":")
                        key = pieces[0].strip()
                        value = ":".join(pieces[1:]).strip()
                        value = parse_link(value)
                    else:
                        # multiline value
                        if not isinstance(value, list):
                            if value:
                                value = [value]
                            else:
                                value = []

                        prefix = " - "
                        line = line.replace(
                            prefix, ""
                        ).strip()  # TODO: remove [[ ]] from links
                        line = parse_link(line)
                        if not line:
                            continue
                        else:
                            value.append(line)

                elif yaml_find == 2:
                    # end of yaml frontmatter
                    if key:
                        properties[key] = value
                    self.content = "\n".join(lines)
                    break
            if properties:
                self.instance = KnowledgeGraphEntryFactory.create(properties=properties)

    def prep_for_yaml(self, text):
        # this needs to be improved
        mapping = {
            # "\&": "&",
            "\\&": "&",
            '"': "'quotationmark'",
            "\n": " 'newline' ",
        }
        if "\\" in text and "/" in text:
            text = path_cleaning(text)
        for key, value in mapping.items():
            text = text.replace(key, value)

        if not text.startswith('"') and not text.endswith('"'):
            text = '"{}"'.format(text)

        return text

    def save(self, path=None):
        # lists = [
        #     "layman term",
        #     "subclass of",
        #     "instance of",
        #     "aliases",
        #     "tags",
        #     "wikidata candidates",
        #     "orkg candidates",
        # ]
        # data = self.convert_python_to_obsidian()
        # if data:
        if not path:
            path = self.path
        data = {}
        for key, value in self.instance.__dict__.items():
            # if key in ["path", "content"]:
            #     continue
            if value == None:
                value = ""
            # if key == "wikidata ID" and isinstance(value, list):
            #     data["wikidata candidates"] = value
            #     value = ""
            # elif key in lists:
            #     if not isinstance(value, list):
            #         value = [value]
            # if key == "instance of":
            if isinstance(value, str):
                # if "{" in value or "}" in value:
                value = self.prep_for_yaml(value)

            if isinstance(value, list):
                # TODO: improve this lookup
                if key in ["instance_of", "subclass_of"]:
                    value = ['"[[{}]]"'.format(val) for val in value]
                value = "\n - " + "\n - ".join(value)
            elif isinstance(value, dict):
                # value = "\n".join([f" - {k}: {v}" for k, v in value.items()])
                value = json.dumps(value)
            data[key] = value

        with open(path, "w", encoding="utf8") as f:
            f.write("---\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
            f.write("---\n")
            f.write("\n")

            if self.content:
                self.content.strip()
                while self.content.startswith("\n"):
                    self.content = self.content[1:]
                while self.content.endswith("\n"):
                    self.content = self.content[:-1]
                f.write(self.content)
                f.write("\n")
        return True


class ObsidianFolderBuilder(Builder):
    """
    Represents the Obsidian readable representation of our ontology.
    Structure:
    /templates # contains templates for the different node types
        - Instance.md
        - Class.md
    And then the actual nodes, each accoring to their type specified in templates
    """

    def __init__(self, director: Director, classes={}, instances={}):
        super().__init__(director)

        self.path = (
            self.config.obsidian_path
            if self.config and hasattr(self.config, "obsidian_path")
            else None
        )
        self.templates: dict[str, Node] = {}
        self.nodes: dict[str, Node] = {}

        self.classes: dict[str, Instance] = {}
        self.instances: dict[str, Instance] = {}
        self.papers: dict[str, Instance] = {}
        # self.other_nodes: dict[str, Node] = {}

        if self.path:
            self.load(self.path)

    def build(self):
        self.populate(force=True)
        self.save()

    def load(self, path):
        self.path = path
        templates_path = os.path.join(path, "templates")
        for file in os.listdir(templates_path):
            if file.endswith(".md"):
                filepath = os.path.join(templates_path, file)
                self.templates[file[:-3]] = Node(path=filepath)

        for file in os.listdir(path):
            if file.endswith(".md"):
                filepath = os.path.join(path, file)
                node = Node(path=filepath)
                try:
                    if "class" in node.instance.tags or hasattr(
                        node.instance, "subclass of"
                    ):
                        self.classes[node.instance.label] = node.instance
                    elif "instance" in node.instance.tags or hasattr(
                        node.instance, "instance of"
                    ):
                        if "paper" in node.instance.instance_of:
                            self.papers[node.instance.label] = node.instance
                        else:
                            self.instances[node.instance.label] = node.instance
                    else:
                        self.other_nodes[node.instance.label] = node.instance
                except:
                    # self.other_nodes[node.name] = node
                    print(f"Error: Could not determine type of node {filepath}")

        print("Loaded Obsidian folder:")
        print(
            "number of tempaltes: "
            + str(len(self.templates))
            + " ("
            + ", ".join(self.templates.keys())
            + ")"
        )
        print("number of classes: " + str(len(self.classes)))
        print("number of instances: " + str(len(self.instances)))
        # print("number of other nodes: " + str(len(self.other_nodes)))

    def save(self, path=None, overwrite_templates=False):
        if not path:
            path = self.path
        templates_path = os.path.join(path, "templates")
        if not os.path.exists(templates_path):
            os.makedirs(templates_path)

        paths = []

        if overwrite_templates:
            for template in self.templates.values():
                template.save()

        for node in self.nodes.values():
            node.save()
            print(node.instance.label + ": " + node.path)
            if node.path not in paths:
                paths.append(node.path)
            else:
                Warning(f"Error: Duplicate path {node.path}")

    # def obsidify_property(self, text:str):
    #     mapping = {
    #         "_": " ",
    #     }
    #     for key, value in mapping.items():
    #         text = text.replace(key, value)
    #     return text

    def properties_from_template(self, template_name, node: Node):
        # print(node)
        template = self.templates.get(template_name, {})
        if not template:
            return

        for key, value in template.__dict__.items():
            # node properties
            if not hasattr(node, key) or not getattr(node, key):
                setattr(node, key, value)

        # properties.update(template.instance.get("properties", {}))

        properties = {}
        properties.update(template.instance.__dict__)
        for key, value in node.instance.__dict__.items():
            # key = self.obsidify_property(key)
            if key not in properties or not properties[key]:
                properties[key] = value
            elif not value:
                continue
            else:
                # both exist, try to merge
                # print(f"Merging {key} ({value}, {properties[key]}) for {name}")
                if isinstance(value, list):
                    for entry in value:
                        entry = entry.strip()
                        if entry not in properties[key]:
                            properties[key].append(entry)

                    if key == "tags":
                        added = []
                        to_delete = []
                        for listID, entry in enumerate(properties[key]):
                            entry = entry.strip()
                            if entry.startswith("#"):
                                entry = entry[1:]
                            if entry in added:
                                to_delete.append(listID)
                            properties[key][listID] = entry
                            added.append(entry)
                        for listID in to_delete:
                            properties[key].pop(listID)

                elif isinstance(value, dict):
                    properties[key].update(value)
                else:
                    name = getattr(node, "name", getattr(node, "label", "unknown name"))
                    Warning(
                        f"Error: Could not merge properties {key} ({value}, {properties[key]}) for {name}"
                    )
        node.instance.set_properties(properties)

    def add_nodes(
        self, instances: dict[str, Instance], template_name="Instance", force=False
    ):
        for name, instance in instances.items():
            if name not in self.nodes or force:
                filepath = os.path.join(
                    self.path, f"{clear_name(name, can_be_folder = False)}.md"
                )
                node = Node(instance, filepath)
                self.properties_from_template(template_name, node)
                self.nodes[name] = node

    def populate(self, instances={}, classes={}, force=False):
        self.instances.update(instances)
        self.classes.update(classes)

        print("Populating Obsidian folder")
        self.add_nodes(self.instances, template_name="Instance", force=force)
        self.add_nodes(self.papers, template_name="Instance", force=force)
        self.add_nodes(self.classes, template_name="Class", force=force)

        # if force:
        #     print("Forcing overwrite of all nodes")
        #     self.classes = {}
        #     self.instances = {}
        #     self.other_nodes = {}
        # for name, instance in instances.items():
        #     if name not in self.instances:
        #         filepath = os.path.join(
        #             self.path, f"{clear_name(name, can_be_folder = False)}.md"
        #         )
        #         node = Node(instance, filepath)
        #         self.properties_from_template("Instance", node)
        #         self.instances[name] = instance
        #         self.nodes[name] = node
        # for name, instance_type in classes.items():
        #     if name not in self.classes:
        #         filepath = os.path.join(
        #             self.path, f"{clear_name(name, can_be_folder = False)}.md"
        #         )
        #         properties = self.properties_from_template("Class", instance_type)
        #         self.classes[name] = Node(filepath, properties)
        print(
            "Added "
            + str(len(self.instances))
            + " instances and "
            + str(len(self.classes))
            + " classes to Obsidian folder"
        )

        # def __init__(self, path, properties={}):

    #     self.path = path
    #     self.content = properties.get("content", "")
    #     self.set_properties(properties)

    # def get(self, label="", default={}):
    #     if not label:
    #         return self.__dict__
    #     if label == "properties":
    #         return {
    #             key: value
    #             for key, value in self.__dict__.items()
    #             if key not in ["path"]
    #         }
    #     elif label in self.__dict__:
    #         return self.__dict__[label]
    #     else:
    #         return default

    # def set_properties(self, properties={}, force=False):
    #     if properties:
    #         # properties = self.convert_python_to_obsidian(properties)
    #         for key, value in properties.items():
    #             if hasattr(self, key):
    #                 existing = getattr(self, key)
    #                 if existing != value:
    #                     if not force:
    #                         print(f"Preserving existing value for {key}: {existing}")
    #                         continue
    #                     else:
    #                         print(f"Overwriting existing value for {key}: {existing}")
    #             setattr(self, key, value)
    #     else:
    #         try:
    #             self.load()
    #         except:
    #             pass

    # def convert_python_to_obsidian(self, input={}, back_to_python=False):
    #     if not input:
    #         input = self.__dict__

    #     forbidden = ["path", "content"]
    #     data = {k: v for k, v in input.items() if k not in forbidden}

    # data = {}
    # for key, value in input.items():
    #     if key == "path" or key == "content":
    #         continue

    # for key, value in Node.obsidian_python_property_map.items():
    #     if key == "path" or key == "content" or hasattr(Node, key):
    #         continue

    #     # pos_key = key if not back_to_python else value
    #     # if isinstance(value, dict):
    #     #     if "instance of" in input and input["instance of"] == key:
    #     #         for subkey, subvalue in value.items():
    #     #             pos_key = subkey if not back_to_python else subvalue
    #     #             if subvalue in input:
    #     #                 data[pos_key] = input[subvalue]
    #     #             elif subkey in input:
    #     #                 data[pos_key] = input[subkey]
    #     #             else:
    #     #                 data[pos_key] = None
    #     # elif value in input:
    #     #     data[pos_key] = input[value]
    #     # elif key in input:
    #     #     data[pos_key] = input[key]
    #     # else:
    #     #     data[pos_key] = None
    # if data["instance of"]:
    #     # is an instance, delete subclass attribute
    #     del data["subclass of"]
    # else:
    #     # is a class, delete instance attribute
    #     del data["instance of"]

    # return data


director.build_obsidian_folder()


# get all text files
def get_paper_full_text(directory):
    paper_full_text = {}
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".txt"):
                    file_path = os.path.join(folder_path, file)
                    paper_full_text[file[:-4]] = file_path
                    break

    return paper_full_text


paper_full_text = get_paper_full_text(
    "G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR/00_PDFs"
)


# Step 2: find occurrences of instances in full text of papers
import sys
from bisect import bisect_left
import numpy as np
import json


class PosInPaper:
    def __init__(self):
        # List of paper identifiers
        self.papers = []
        # List of literals
        self.literals = []
        # Dict of unique words across all literals
        self.words = {}
        self.word_len = []
        # List of unique combinations of words across all literals
        self.word_combinations = {}
        self.word_combination_lists = []
        self.word_combination_index_literal = {}
        # 2D list mapping pairs of literals to their word combination index
        self.word_combination_index_literal_literal = []
        # 2D list of SortedSets, each containing the positions of a word in a paper
        self.word_occurrences_in_papers = []
        # 3D list containing the minimum distances between word combinations in each paper
        self.min_distances = []

    @time_function
    def populate(
        self,
        config: Config,
        papers: list,
        literals: list[str],
        paper_full_text,
        optimize=True,
    ):
        """
        Populates the internal data structures with occurrences and distances of literals in papers.

        Parameters:
        - config (Config): Configuration object containing settings.
        - papers (list): List of paper identifiers.
        - literals (list[str]): List of literals to process.
        - paper_full_text (dict): Mapping from paper identifiers to their full text file paths.
        - optimize (bool): Flag to optimize data structures after population.
        """
        self.initialize_variables(papers, literals)
        self.process_literals()
        self.process_literal_combinations()
        self.setup_data_structures()
        self.find_occurrences_in_texts(paper_full_text)
        if optimize:
            self.optimize_data()

    def update_list_attribute(self, list, name):
        existing = getattr(self, name)
        if not existing:
            setattr(self, name, list)
        else:
            if existing != list:
                print(f"Warning: {name} has changed.")
                for item in list:
                    if item not in existing:
                        print(f"Item {item} is new.")
                        existing.append(item)
                # update
                raise NotImplementedError(
                    "create a function to update other relying attributes"
                )

    @time_function
    def initialize_variables(self, papers, literals):
        """
        Initializes basic variables for the class instance.

        Parameters:
        - papers (list): List of paper identifiers.
        - literals (list): List of literals to process.
        """
        if not self.papers:
            self.papers = papers
        else:
            if self.papers != papers:
                print("Warning: Papers have changed.")
                for paper in papers:
                    if paper not in self.papers:
                        print(f"Paper {paper} is new.")
                        self.papers.append(paper)
        # self.papers = papers

        if not self.literals:
            self.literals = literals
        else:
            if self.literals != literals:
                print("Warning: Literals have changed.")
                for literal in literals:
                    if literal not in self.literals:
                        print(f"Literal {literal} is new.")
                        self.literals.append(literal)
                        self.word_combination_index_literal[literal] = None

        if len(self.literals) != len(self.word_combination_index_literal):
            for literal in self.literals:
                if literal not in self.word_combination_index_literal:
                    self.word_combination_index_literal[literal] = None
            # sort self.word_combination_index_literal by self.literals
            self.word_combination_index_literal = {
                k: self.word_combination_index_literal[k] for k in self.literals
            }
        if (
            isinstance(self.word_combination_index_literal_literal, np.ndarray)
            and self.word_combination_index_literal_literal.size == 0
        ):
            self.word_combination_index_literal_literal = np.full(
                (len(self.literals), len(self.literals)), None, dtype=object
            )
        elif (
            isinstance(self.word_combination_index_literal_literal, list)
            and self.word_combination_index_literal_literal == []
        ):
            self.word_combination_index_literal_literal = [
                [None] * len(self.literals) for _ in range(len(self.literals))
            ]
        elif len(self.literals) != len(self.word_combination_index_literal_literal):
            # pad self.word_combination_index_literal_literal
            len_dif = len(self.literals) - len(
                self.word_combination_index_literal_literal
            )
            self.word_combination_index_literal_literal = np.pad(
                self.word_combination_index_literal_literal,
                ((0, len_dif), (0, len_dif)),
                "constant",
                constant_values=None,
            )
            # self.word_combination_index_literal_literal = [[None] * len(self.literals) for _ in range(len(self.literals))]

        # self.literals = literals

    @time_function
    def process_literals(self):
        """
        Processes each literal to extract and store unique words and word combinations.

        Parameters:
        - literals (list): List of literals to process.
        """
        for lit in self.literals:
            word_list = split_string(lit)
            self.add_words(word_list)
            self.add_if_word_combination(word_list, lit)

    def add_words(self, word_list):
        """
        Adds unique words from a list to the internal list of words.

        Parameters:
        - word_list (list): List of words to add.
        """
        for word in word_list:
            if word not in self.words:
                self.words[word] = len(self.words)
                self.word_len.append(len(word))

    def add_if_word_combination(self, word_list, lit):
        """
        Adds a unique combination of words from a list to the internal list of word combinations.

        Parameters:
        - word_list (list): List of words forming a combination.
        - lit (str): The literal corresponding to the word combination.
        """
        if len(word_list) > 1:
            pos = self.word_combination_index_literal.get(lit, -1)
            if pos == -1 or pos == None:
                froz = frozenset(word_list)
                pos = len(self.word_combinations)
                self.add_word_combination(froz, pos)
                self.word_combination_index_literal[lit] = pos

    def add_word_combination(self, froz, pos):
        self.word_combinations[froz] = pos
        self.word_combination_lists.append(
            [self.words[word] for word in sorted(froz, key=len, reverse=True)]
        )

    @time_function
    def process_literal_combinations(self):
        """
        Processes combinations of literals to store their indices in the internal data structure.

        Parameters:
        - literals (list): List of literals to process.
        """
        # Use a dictionary for quick lookup and storage
        combination_index = len(self.word_combinations)

        for id1, literal1 in enumerate(self.literals):
            for id2 in range(id1 + 1, len(self.literals)):
                if self.word_combination_index_literal_literal[id1][id2] is not None:
                    continue
                literal2 = self.literals[id2]
                # Use a sorted tuple for consistent ordering
                froz = frozenset(split_string(literal1) + split_string(literal2))
                # Check if the combination is already in the dictionary
                pos = self.word_combinations.get(froz, -1)
                if pos == -1:
                    pos = combination_index
                    combination_index += 1

                    self.add_word_combination(froz, pos)

                # Update the matrix with the index of the combination
                self.word_combination_index_literal_literal[id1][id2] = pos
                self.word_combination_index_literal_literal[id2][id1] = pos

    @time_function
    def setup_data_structures(self):
        """
        Initializes the data structures for storing word occurrences and minimum distances.

        Parameters:
        - papers (list): List of paper identifiers.
        """
        if self.word_occurrences_in_papers == []:
            self.word_occurrences_in_papers = [
                [[] for _ in self.words] for _ in self.papers
            ]
        new_papers = len(self.papers) - len(self.word_occurrences_in_papers)
        new_words = len(self.words) - len(self.word_occurrences_in_papers[0])
        if new_words > 0:
            for paper in self.word_occurrences_in_papers:
                paper += [[] for _ in range(new_words)]
        if new_papers > 0:
            self.word_occurrences_in_papers += [
                [[] for _ in self.words] for _ in range(new_papers)
            ]

        if (
            isinstance(self.min_distances, list)
            and self.min_distances == []
            or self.min_distances is None
        ):
            self.min_distances = np.full(
                (len(self.papers), len(self.word_combinations)), -2, dtype=int
            )
        # If new papers or words have been added, update the data structures
        if len(self.papers) > len(self.min_distances):
            self.min_distances = np.pad(
                self.min_distances,
                ((0, len(self.papers) - len(self.min_distances)), (0, 0)),
                "constant",
                constant_values=-2,
            )
        if len(self.word_combinations) > len(self.min_distances[0]):
            len_dif = len(self.word_combinations) - len(self.min_distances[0])
            self.min_distances = np.pad(
                self.min_distances,
                ((0, 0), (0, len_dif)),
                "constant",
                constant_values=-2,
            )

    @time_function
    def find_occurrences_in_texts(self, paper_full_text):
        """
        Finds and stores the occurrences of each word in the full text of each paper.

        Parameters:
        - papers (list): List of paper identifiers.
        - paper_full_text (dict): Mapping from paper identifiers to their full text file paths.
        """
        for paperID, paper in enumerate(self.papers):
            if paper in paper_full_text:
                with open(paper_full_text[paper], "r", encoding="utf8") as f:
                    text = f.read().lower()
                    for word, wordID in self.words.items():
                        if not self.word_occurrences_in_papers[paperID][wordID]:
                            self.find_and_add_word_occurrences(
                                paperID, wordID, word, text
                            )
            else:
                print(f"Paper {paper} has no full text available.")

    def find_and_add_word_occurrences(self, paperID, wordID, word, text):
        """
        Finds and adds the occurrences of a word in a paper's text to the internal data structure.

        Parameters:
        - paperID (int): The index of the paper in the internal list.
        - wordID (int): The index of the word in the internal list.
        - word (str): The word to find occurrences of.
        - text (str): The full text of the paper.
        """
        pos = text.find(word)
        while pos != -1:
            # self.word_occurrences_in_papers[paperID][wordID].add(pos)
            self.word_occurrences_in_papers[paperID][wordID].append([pos, wordID])
            pos = text.find(word, pos + 1)

    @time_function
    def optimize_data(self):
        """
        Optimizes the internal data structures for faster access and smaller memory footprint.
        """
        # self.word_combination_index_literal_literal = np.array(self.word_combination_index_literal_literal, dtype=int)
        for paperID in range(len(self.papers)):
            for wordID in range(len(self.words)):
                # self.word_occurrences_in_papers[paperID][wordID] = SortedSet(self.word_occurrences_in_papers[paperID][wordID])
                if not self.word_occurrences_in_papers[paperID][wordID]:
                    continue
                if isinstance(self.word_occurrences_in_papers[paperID][wordID][0], int):
                    self.word_occurrences_in_papers[paperID][wordID] = [
                        (x, wordID)
                        for x in self.word_occurrences_in_papers[paperID][wordID]
                    ]
                    print(
                        f"Optimizing {list(self.words.keys())[wordID]} in paper {paperID}"
                    )
                for occurrence in self.word_occurrences_in_papers[paperID][wordID]:
                    if isinstance(occurrence, int):
                        self.word_occurrences_in_papers[paperID][wordID] = [
                            (occurrence, wordID)
                        ]
                        # break
                        raise Exception("This should not happen")

    def save_to_csv(self, config: Config = None, path=None, name="pos_in_paper"):
        if path is None:
            path = config.get_output_path()

        # save min_distances to csv
        # dump self.min_distances to csv, with self.papers as row headers and self.word_combinations as column headers
        filepath = os.path.join(path, name + "_min_distances.csv")
        with open(filepath, "w", encoding="utf-8") as f:
            word_combinations = [
                "_".join(sorted(froz, key=len, reverse=True))
                for froz in self.word_combinations.keys()
            ]
            f.write(
                "papers"
                + config.csv_separator
                + config.csv_separator.join(word_combinations)
                + "\n"
            )
            for i, paper in enumerate(self.papers):
                f.write(
                    paper
                    + config.csv_separator
                    + config.csv_separator.join(map(str, self.min_distances[i]))
                    + "\n"
                )

    @time_function
    def save_to_file(
        self,
        config,
        path=None,
        name="pos_in_paper",
        check_size=False,
        min_distance_to_csv=False,
        backup=True,
    ):
        """
        Saves the internal data structures to files for persistence.

        Parameters:
        - path (str, optional): The base path for the output files. Defaults to "pos_in_paper".
        """
        if path is None:
            path = config.get_output_path()
        filepath = os.path.join(path, name + ".json")

        data = {}

        for key, value in self.__dict__.items():
            # if key == "min_distances" or key == "word_combination_index_literal_literal":
            if (
                value.__class__.__name__ == "ndarray"
            ):  # min_distances, word_combination_index_literal_literal
                data[key] = value.tolist()
            # if key == "min_distances":
            #     data[key] = value.tolist()
            elif key == "word_combinations":
                data[key] = {
                    "_".join(key): value
                    for key, value in self.word_combinations.items()
                }
            else:
                data[key] = value
            if check_size:
                # Construct the file name for each sub-dictionary
                filepath = os.path.join(path, f"{name}_{key}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data[key], f, ensure_ascii=False)
            pass

        if min_distance_to_csv:
            self.save_to_csv(config, path, name)

        if backup:
            backup_path = os.path.join(path, name + "_backup" + ".json")
            if os.path.exists(filepath):
                existing_is_healthy = True
                try:
                    self.load_from_file(config, path, name)
                except Exception as e:
                    print(f"Overwriting existing save")
                    existing_is_healthy = False
                if existing_is_healthy:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(filepath, backup_path)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    @time_function
    def load_from_file(self, config, path=None, name="pos_in_paper", backup=True):
        """
        Loads the internal data structures from files.

        Parameters:
        - path (str, optional): The base path for the input files. Defaults to "pos_in_paper".
        """
        if path is None:
            path = config.get_output_path()
        filepath = os.path.join(path, name + ".json")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading file {filepath}: {e}")
            if backup:
                backup_path = os.path.join(path, name + "_backup" + ".json")
                if os.path.exists(backup_path):
                    print(f"Trying to load backup file {backup_path}")
                    with open(backup_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    raise Exception(f"No backup file found at {backup_path}")
            else:
                raise e

        for key, value in data.items():
            if key == "word_combinations":
                setattr(
                    self,
                    key,
                    {
                        frozenset(split_string(sub_key)): i
                        for i, sub_key in enumerate(value)
                    },
                )
            elif (
                key == "min_distances"
                or key == "word_combination_index_literal_literal"
            ):
                setattr(self, key, np.array(value))
            else:
                try:
                    setattr(self, key, value)
                except Exception as e:
                    raise Exception(f"Error loading pos_in_paper attribute {key}: {e}")

        self.setup_data_structures()

    @time_function
    def calculate_all_possible(self):
        """
        Calculates the minimum distances between all possible combinations of literals in all papers.
        """
        save_every = None
        if len(self.papers) > 300:
            print(
                "Warning: This operation is computationally expensive and may take a long time."
            )
            save_every = 300
        for p in range(len(self.papers)):
            if save_every and p % save_every == 0:
                print(f"Processing paper {p} of {len(self.papers)}")
                self.save_to_file(config)
            for w in range(len(self.word_combinations)):
                self.find_min_distance_by_id(p, w)
            # for i in range(len(self.literals)):
            #     for j in range(i + 1, len(self.literals)):
            #         # get word_combination_index_literal_literal
            # self.find_min_distance_by_id(p, self.word_combination_index_literal_literal[i][j])

    def find_min_distance_by_id(self, paperID, wcID):
        """
        Finds the minimum distance between occurrences of literals in a paper.

        Parameters:
        - paper (str): The identifier for the paper.
        - literals (list): A list of literals for which the distance is to be found.
        - allow_call (bool): Flag to allow recursive call to get_min_distance.

        Returns:
        - int: The minimum distance between occurrences of the literals.
        """
        distance = self.min_distances[paperID][wcID]

        if distance == -1:
            # word combination not found in paper
            return -1
        if distance == -2:
            # calculate distance
            pass
        else:
            return distance

        list_ids = self.word_combination_lists[wcID]
        # since we have attached global Word IDs to the occurrences, we need to map to their local position
        list_ids_map = {list_ids[i]: i for i in range(len(list_ids))}
        # literals = [list(self.words)[i] for i in list_ids]

        # TODO: It should be possible to remove smaller words from the list,
        # if a larger word contains it:
        # e.g. remove "engine" if "engineer" is in the list
        ## The following implementation works, but is not used for now. Reasons:
        ## 1. It could be slower than the current implementation
        ## 2. It might be beneficial to future use-cases to not remove smaller words
        # literals = [list(self.words)[key] for key in list_ids_map]
        # # check if any literal is a substring of another
        # for i, lit1 in enumerate(literals):
        #     for j, lit2 in enumerate(literals):
        #         if i != j and lit1 in lit2:
        #             # if lit1 is a substring of lit2, remove it from the list
        #             list_ids_map.pop(list_ids[i])
        #             break

        lit_len = [self.word_len[i] for i in list_ids]

        for i in list_ids:
            if not self.word_occurrences_in_papers[paperID][i]:
                self.min_distances[paperID][wcID] = -1
                return -1
        # Outsourced to optimize
        # inputs = [[(x, i) for x in self.word_occurrences_in_papers[paperID][wordID]] for i, wordID in enumerate(list_ids)]
        inputs = [
            self.word_occurrences_in_papers[paperID][wordID] for wordID in list_ids
        ]

        indices = [lst[0][0] for lst in inputs]
        best = float("inf")

        for item in sorted(sum(inputs, [])):
            if item[0] not in indices:
                continue
            indices[list_ids_map[item[1]]] = item[0]
            arr_min = min(indices)
            best = min(max(indices) - arr_min - lit_len[indices.index(arr_min)], best)
            if best <= 0:
                best = 0
                break
        self.min_distances[paperID][wcID] = best

        return best

    pos_in_paper = PosInPaper()


# config.recalculate_pos_in_paper = True # May be used for debug purposes

if not config.recalculate_pos_in_paper:
    try:
        pos_in_paper.load_from_file(config)
    # print exception
    except Exception as e:
        # if config.debug:
        #     raise e
        print(e)
        print("Starting from scratch.")

        config.recalculate_pos_in_paper = True

# TODO:
# raise NotImplementedError("Implement a check that compares the loaded instances and papers with the current ones")

# if config.recalculate_pos_in_paper:
pos_in_paper.populate(
    config,
    list(director.papers.keys()),
    list(director.instances.keys()),
    paper_full_text,
)
# pos_in_paper.save_to_file(config)


class ErrorMatrixBuilder(MatrixBuilder):
    def __init__(self, director: Director, pos_in_paper: PosInPaper):
        super().__init__(director)

        self.papers = list(director.papers.keys())
        self.literals = list(director.instances.keys())
        self.pos_in_paper = pos_in_paper
        self.paper_full_text = director.paper_full_text
        self.paper_instance_occurrence_matrix = director.builder[
            "occurrence_matrix"
        ].matrix

    @time_function
    def build_matrix(self):
        # self.matrix = find_instance_piece_gap(
        # self.config,
        # self.papers,
        # self.paper_full_text,
        # self.literals,
        # self.paper_instance_occurrence_matrix,
        # self.pos_in_paper,
        # )
        # def find_instance_piece_gap(
        #     config: Config,
        #     papers,
        #     paper_full_text,
        #     instances,
        #     paper_instance_occurrence_matrix,
        #     pos_in_paper: PosInPaper,
        # ):
        self.matrix = np.zeros(self.paper_instance_occurrence_matrix.shape, dtype=float)
        for paperID, paper in enumerate(self.papers):
            if paperID % 100 == 0:
                # print(f"Processing paper {paperID} of {len(papers)}")
                pass
            if paper in paper_full_text:
                for i, instance in enumerate(self.literals):
                    if self.paper_instance_occurrence_matrix[paperID][i] == 0:
                        continue
                    wcID = pos_in_paper.word_combination_index_literal[instance]
                    # TODO: handle if that instance has no word combination index entry
                    if wcID is None:
                        # word has no distance
                        continue
                    min_distance = pos_in_paper.find_min_distance_by_id(paperID, wcID)
                    if min_distance is None:
                        pass
                    if min_distance > config.gap_too_large_threshold:
                        # print(f"Gap for {instance} in {paper} ({min_distance} > {GAP_TOO_LARGE_THRESHOLD})")
                        self.paper_instance_occurrence_matrix[paperID][i] = 0
                        # get log base 10 of min distance
                        self.matrix[paperID][i] = round(np.log10(min_distance), 1)

                    # Some pieces may not be found in the full text
                    if min_distance == -1:
                        # print(f"{instance} not found in {paper} at all")
                        self.paper_instance_occurrence_matrix[paperID][i] = 0
                        self.matrix[paperID][i] = min_distance
                        # for these, we do not store the gap
                        continue

        # return error_matrix

    def build(self):
        self.build_matrix()

        self.remove_zeros()
        # error_matrix, has_error = remove_zeros(error_matrix)

        self.papers = self.handle_deletions(self.papers)
        self.literals = self.handle_deletions(self.literals, rows=False)

        # process_matrix(
        #     self.config,
        #     self.matrix,
        #     self.papers,
        #     self.literals,
        #     "error_matrix",
        # )
        # paper_instance_occurrence_matrix, instances, deletions = update_instances(
        #     paper_instance_occurrence_matrix, literals, instance_types_dicts
        # )

        # papers = handle_deletions(papers, deletions)

        # free unneeded memory
        # del deletions, has_error


# instance_instance_co_occurrence_matrix = np.dot(
#     paper_instance_occurrence_matrix.T, paper_instance_occurrence_matrix
# )

# error_matrix = find_instance_piece_gap(
#     config,
#     papers,
#     paper_full_text,
#     literals,
#     paper_instance_occurrence_matrix,
#     pos_in_paper,
# )

director.paper_full_text = paper_full_text

director.builder["error_matrix_builder"] = ErrorMatrixBuilder(director, pos_in_paper)
director.builder["error_matrix_builder"].build()
director.builder["error_matrix_builder"].save()
director.sort_instances()


# visualize timeline
import numpy as np
import matplotlib.pyplot as plt
import math


def visualize_timeline(
    config: Config,
    year_instance_occurrence_matrix,
    year_papers,
    instances,
    instance_types_dicts,
    name="some_timeline",
    path=None,
    recursion_depth=0,
    start_index=0,
    error_matrix=None,
    error_instances=None,
):
    if not path:
        path = config.get_output_path(path, visualization=True)
    years = list(year_papers.keys())
    max_papers = max([len(year_papers[year]) for year in years])
    yearly_papers = [len(year_papers[year]) for year in years]

    ALPHA_ERROR_LINE = 0.3
    ALPHA_ERROR_ZONE = 0.2
    ALPHA_PAPER_BAR = 0.3

    for type in instance_types_dicts:
        use = [instance in instance_types_dicts[type] for instance in instances]
        type_instances = [
            instance for instance, use_flag in zip(instances, use) if use_flag
        ]
        total_occurrences = [
            np.sum(year_instance_occurrence_matrix[:, instances.index(instance)])
            for instance in type_instances
        ]
        type_instances_sorted = [
            x
            for _, x in sorted(
                zip(total_occurrences, type_instances),
                key=lambda pair: pair[0],
                reverse=True,
            )
        ]

        PARTITION_SIZE = 10
        # if error_instances is not None:
        #     PARTITION_SIZE = int(0.5 * PARTITION_SIZE)

        type_matrix = year_instance_occurrence_matrix[
            :, [instances.index(instance) for instance in type_instances_sorted]
        ]
        factor = 1
        size_x = (2 + len(years) / 6) * factor
        size_y = (2 + max_papers / 15) * factor
        size_y_2 = (2 + PARTITION_SIZE / 2) * factor
        size_y = max(size_y, size_y_2)
        fig, ax = plt.subplots(figsize=(size_x, size_y), dpi=300)

        ax.set_xticks(range(len(years)))
        years_labels = [year if len(year_papers[year]) > 0 else "" for year in years]
        ax.set_xticklabels(years_labels, fontsize=10, rotation=90)

        step_size = max(1, math.ceil(max_papers / 10))
        ax.set_yticks(np.arange(0, max_papers + 1, step=step_size))
        ax.set_yticklabels(
            [str(int(x)) for x in np.arange(0, max_papers + 1, step=step_size)],
            fontsize=10,
        )

        # set y axis label
        ax.set_ylabel("absolute", fontsize=10)

        plt.bar(
            range(len(years)),
            yearly_papers,
            color="black",
            alpha=ALPHA_PAPER_BAR,
            label=f"Total papers ({sum(yearly_papers)})",
            zorder=0,
        )

        line_count = 0
        i = start_index
        while line_count < PARTITION_SIZE and i < len(type_instances_sorted):
            instance = type_instances_sorted[i]
            yearly_occurrences = type_matrix[:, i]
            i_total_occurrences = yearly_occurrences.sum()
            label = f"{instance} ({i_total_occurrences})"
            values = yearly_occurrences
            line = plt.plot(range(len(years)), values, label=label, zorder=3)[0]
            line_count += 1
            if error_matrix is not None and instance in error_instances:
                color = line.get_color()
                errors = error_matrix[:, error_instances.index(instance)]
                errors_plus = yearly_occurrences + errors
                line.set_label(f"{instance} ({i_total_occurrences}-{sum(errors_plus)})")
                # Plot the error as a half transparent line on top of the normal line
                plt.plot(
                    range(len(years)),
                    errors_plus,
                    color=color,
                    alpha=ALPHA_ERROR_LINE,
                    label=f"{instance} (w/o proximity)",
                    zorder=2,
                )
                line_count += 1
                # color in the area between the normal line and the error line
                plt.fill_between(
                    range(len(years)),
                    yearly_occurrences,
                    errors_plus,
                    color=color,
                    alpha=ALPHA_ERROR_ZONE,
                    zorder=1,
                )
            i += 1

            # plt.scatter(range(len(years)), errors, color='red', label=f"{instance} (error)", zorder=1)
        stop_index = i

        plt.legend()

        plt.title(
            f"Number of papers covering {type} instances (#{start_index+1} to #{stop_index} of {len(type_instances_sorted)})"
        )

        # Inset for relative values
        fig.canvas.draw()
        x_lim = ax.get_xlim()  # Get the current x-axis limits from the main plot

        bbox = ax.get_position()
        bb_left, bb_bottom = bbox.x0, bbox.y0
        bb_width, bb_height = bbox.width, bbox.height

        ax_inset = plt.axes(
            [bb_left, 0.05, bb_width, 0.15],
            alpha=ALPHA_PAPER_BAR,
            facecolor="lightgrey",
        )
        for i, instance in enumerate(
            type_instances_sorted[start_index:stop_index], start=start_index
        ):
            yearly_occurrences = type_matrix[:, i]
            values_relative = [
                occurrences / papers if papers > 0 else 0
                for occurrences, papers in zip(yearly_occurrences, yearly_papers)
            ]
            line_relative = ax_inset.plot(
                range(len(years)),
                values_relative,
                label=f"{instance} (relative)",
                zorder=3,
            )[0]

            # add the error part
            if error_matrix is not None and instance in error_instances:
                color = line_relative.get_color()
                errors = error_matrix[:, error_instances.index(instance)]
                errors_plus = yearly_occurrences + errors
                errors_relative = [
                    error / papers if papers > 0 else 0
                    for error, papers in zip(errors_plus, yearly_papers)
                ]
                if max(errors_relative) > 1:
                    print(f"Error: {instance} has a relative error > 1")
                    # throw an exception because this should never be the case:
                    # raise Exception(f"Error: relative {instance} occurrence + error > 1")

                ax_inset.plot(
                    range(len(years)),
                    errors_relative,
                    alpha=ALPHA_ERROR_LINE,
                    color=color,
                    label=f"{instance} (error, relative)",
                    zorder=2,
                )
                # color in the area between the normal line and the error line
                ax_inset.fill_between(
                    range(len(years)),
                    values_relative,
                    errors_relative,
                    alpha=ALPHA_ERROR_ZONE,
                    color=color,
                    zorder=1,
                )

        ax_inset.set_xlim(x_lim)

        ax_inset.set_xticks([])
        ax_inset.set_yticks(np.arange(0, 1.1, step=0.5))
        ax_inset.set_yticklabels(
            [f"{int(x*100)}%" for x in np.arange(0, 1.1, step=0.5)], fontsize=8
        )

        # set y axis label
        ax_inset.set_ylabel("relative", fontsize=10)

        plt.subplots_adjust(bottom=0.3)

        start_string = f"{start_index+1}"
        stop_string = f"{stop_index}"

        # fill up with 0 to have a constant length
        start_string = "0" * (3 - len(start_string)) + start_string
        stop_string = "0" * (3 - len(stop_string)) + stop_string

        part_appendix = f"{start_string}_to_{stop_string}"
        filepath = os.path.join(path, name)
        plt.savefig(f"{filepath}_{type.replace(' ', '_')}_{part_appendix}.png")
        plt.close()

        start_index = stop_index
        if start_index < len(type_instances_sorted):
            # if recursion_depth > 0:
            #     break
            visualize_timeline(
                config,
                year_instance_occurrence_matrix,
                year_papers,
                instances,
                {type: instance_types_dicts[type]},
                name,
                path=path,
                recursion_depth=recursion_depth + 1,
                start_index=start_index,
                error_matrix=error_matrix,
                error_instances=error_instances,
            )
        start_index = 0


# if config.visualize:
#     yearly_error_matrix, year_error_papers = create_year_paper_occurrence_matrix(
#         papers_metadata, error_matrix, error_papers, is_error_matrix=True
#     )
#     visualize_timeline(
#         config,
#         year_instance_occurrence_matrix,
#         year_papers,
#         instances,
#         instance_types_dicts,
#         name="year_instance_occurrence_matrix",
#         error_matrix=yearly_error_matrix,
#         error_instances=error_instances,
#     )


# Create year_paper_occurrence_matrix
class YearPaperOccurrenceMatrixBuilder(MatrixBuilder):
    def __init__(
        self,
        director,
        papers=None,
        paper_instance_occurrence_matrix=None,
        is_error_matrix=False,
    ):
        super().__init__(director)

        # self.papers_metadata = papers_metadata
        self.papers: dict[str, Instance] = papers or director.papers
        self.paper_instance_occurrence_matrix = (
            paper_instance_occurrence_matrix
            or director.builder["occurrence_matrix"].matrix
        )
        self.is_error_matrix = is_error_matrix
        self.year_papers: dict[int, dict[str, Instance]] = {}

    def build_matrix(
        self, paper_instance_occurrence_matrix=None, papers=None, is_error_matrix=False
    ):
        paper_instance_occurrence_matrix = (
            paper_instance_occurrence_matrix or self.paper_instance_occurrence_matrix
        )
        papers = papers or self.papers
        # self.matrix, self.year_papers = create_year_paper_occurrence_matrix(
        #     papers_metadata, paper_instance_occurrence_matrix, papers, is_error_matrix
        # )

        # def create_year_paper_occurrence_matrix(
        #     papers_metadata, paper_instance_occurrence_matrix, papers, is_error_matrix=False
        # ):
        indexed_papers = {paper: i for i, paper in enumerate(papers)}
        for paper, instance in self.papers.items():
            if hasattr(instance, "year"):
                year = int(getattr(instance, "year"))
                if year not in self.year_papers:
                    self.year_papers[year] = {}
                self.year_papers[year][paper] = instance

        earliest = min(self.year_papers)
        latest = max(self.year_papers)
        span = latest - earliest + 1

        for year in range(earliest, latest):
            if year not in self.year_papers:
                self.year_papers[year] = []

        self.year_papers = {
            k: v for k, v in sorted(self.year_papers.items(), key=lambda item: item[0])
        }

        if is_error_matrix:
            # convert any value != 0 to 1
            paper_instance_occurrence_matrix = np.where(
                paper_instance_occurrence_matrix != 0, 1, 0
            )

        # create a year_instance_occurrence matrix from the paper_instance_occurrence_matrix
        year_instance_occurrence_matrix = np.zeros(
            (span, paper_instance_occurrence_matrix.shape[1]), dtype=int
        )
        for yearID, year in enumerate(self.year_papers):
            for paper in self.year_papers[year]:
                if paper in papers:
                    paperID = indexed_papers[paper]
                    year_instance_occurrence_matrix[
                        yearID
                    ] += paper_instance_occurrence_matrix[paperID]

    def build(self):
        self.build_matrix()


director.builder["year_instance_occurrence_matrix"] = YearPaperOccurrenceMatrixBuilder(
    director
)
director.builder["year_instance_occurrence_matrix"].build()

# year_instance_occurrence_matrix, year_papers = create_year_paper_occurrence_matrix(
#     papers_metadata, paper_instance_occurrence_matrix, papers
# )


# ~3 min | {( len(papers) * len(instances) ) / (3 * 1000) }seconds  compare proximity of all instances with one antoher
# ~8 min right now.
# 3 min 30 sec with 164 papers and 339 instances
class ProximityMatrixBuilder(MatrixBuilder):
    def __init__(
        self,
        director: Director,
        instances=None,
        papers=None,
        pos_in_paper=None,
        mode="sqrt",
    ):
        super().__init__(director)

        self.instances: dict[str, Instance] = instances or director.instances
        self.papers: dict[str, Instance] = papers or director.papers
        self.pos_in_paper: PosInPaper = pos_in_paper or director.pos_in_paper

        self.mode = mode

    def build_matrix(self, instances=None, papers=None, pos_in_paper=None):
        instances = instances or self.instances
        papers = papers or self.papers
        pos_in_paper = pos_in_paper or self.pos_in_paper

        # self.matrix, self.proximity_instances = calculate_proximity_matrix(
        #     self.config, pos_in_paper, instances, mode="sqrt"
        # )

    def build(self):
        self.build_matrix()
        self.remove_zeros()
        self.instances = self.handle_deletions(self.instances)

    @time_function
    def build_matrix(
        self,
        # config: Config,
        # pos_in_paper: PosInPaper,
        # instances,
        # mode="sqrt",
        try_to_save_time=False,
    ):
        # TODO: Optimize this function.
        # each instance needs to have it's occurrences as pieces clustered together, so that only those below max distance are considered

        # create a np zeros matrix of size instances x instances
        indexed_instances = {instance: i for i, instance in enumerate(self.instances)}

        self.matrix = np.zeros((len(self.instances), len(self.instances)), dtype=float)

        # alternatives are:
        # "sqrt" - 1 / (square root of the distance)
        # "linear" - 1 / distance
        # "binary" - 1 if distance < MAX_GAP_THRESHOLD, 0 otherwise
        # "log" - 1 / log(distance)

        # There is a chance that pos_in_paper papers and instances are out of sync with the current papers and instances
        paperIDs = [
            paperID
            for paperID, name in enumerate(pos_in_paper.papers)
            if name in self.papers
        ]
        lID_map = {
            indexed_instances[name]: instanceID
            for instanceID, name in enumerate(pos_in_paper.literals)
            if name in self.instances
        }

        for id1 in range(len(self.instances)):
            # print (f"Processing {id1} of {len(instances)}: {instance1}")
            for id2 in range(id1 + 1, len(self.instances)):
                # FIXME: this resulted in a matrix which was not symmetric.
                # That hints at a problem with the calclulation, [id1][id2] and [id2][id1] should be the same
                wcID = pos_in_paper.word_combination_index_literal_literal[
                    lID_map[id1]
                ][lID_map[id2]]
                for paperID in paperIDs:
                    distance = pos_in_paper.find_min_distance_by_id(paperID, wcID)

                    if distance < 0:
                        # print(f"Error: {instance1} and {instance2} not found in {paper}")
                        continue
                    result = 0.0
                    if distance == 0:
                        result = 1
                    elif distance == 1:
                        result = 1
                    elif self.mode == "sqrt":
                        result = 1 / np.sqrt(distance)
                    elif self.mode == "linear":
                        result = 1 / distance
                    elif self.mode == "binary":
                        result = 1 if distance < config.gap_too_large_threshold else 0
                    elif self.mode == "log":
                        result = 1 / np.log(distance)
                    else:
                        print("Error: unknown mode")
                        break
                    if result > 0.0:
                        self.matrix[id1][id2] += result
                        self.matrix[id2][id1] += result

        # TODO rest doesnt seem to work, short fix implemented:
        # create a copy of labels that only contains instances that are in the proximity matrix

        # instance_instance_proximity_matrix, deletions = remove_zeros(
        #     instance_instance_proximity_matrix
        # )
        # proximity_instances = handle_deletions(instances, deletions, rows=False)


director.pos_in_paper = pos_in_paper
director.builder["proximity_matrix"] = ProximityMatrixBuilder(director)
director.builder["proximity_matrix"].build()
# instance_instance_proximity_matrix, proximity_instances = calculate_proximity_matrix(
#     config, pos_in_paper, instances
# )


from mlxtend.frequent_patterns import association_rules
from mlxtend.frequent_patterns import apriori


def get_rules(matrix, columns):
    # AttributeError: 'numpy.ndarray' object has no attribute 'dtypes'
    dataframe = pd.DataFrame(matrix, columns=columns).astype(bool)

    # for each process:
    # create one res

    res = apriori(dataframe, min_support=0.4, use_colnames=True, max_len=2)

    # visualize res
    res = res.sort_values(by="support", ascending=False)
    res = res.reset_index(drop=True)
    # res

    rules = association_rules(res)
    # sort rules by confidence
    # rules = rules.sort_values(by='confidence', ascending=False)
    rules = rules.sort_values(by="lift", ascending=False)  # (propably most important)
    # rules = rules.sort_values(by='leverage', ascending=False)
    # export rules to csv
    return rules


rules = get_rules(
    director.builder["occurrence_matrix"].matrix, list(director.instances.keys())
)


# rules
process_dataframe(config, rules, "rules")


def identify_cross_type_rules(rules, director: Director):
    cross_type = [False] * len(rules)

    for i, antecentent in enumerate(rules.antecedents):
        if not isinstance(antecentent, str):
            (antecentent,) = antecentent
        consequent = rules.iloc[i].consequents
        if not isinstance(consequent, str):
            (consequent,) = consequent
        type1, type2 = None, None
        type1 = director.instances.get(antecentent, {}).get("instance_of", [None])[0]
        type2 = director.instances.get(consequent, {}).get("instance_of", [None])[0]
        # for type in director.classes:
        #     if antecentent in instance_types_dicts[type]:
        #         type1 = type
        #     if consequent in instance_types_dicts[type]:
        #         type2 = type
        #     if type1 and type2:
        #         break
        if type1 and type2 and type1 != type2:
            cross_type[i] = True
            # print(rules.iloc[i])

    # create a copy for all rules that are cross type
    rules_cross_type = rules[cross_type].copy()
    return rules_cross_type


rules_cross_type = identify_cross_type_rules(rules, director)

# def process_dataframe(config:Config, input_df, name = "some_df", path=None):
#     if path is None:
#         path = config.get_output_path()
#     filepath = os.path.join(path, name)

#     # convert all froensets to strings
#     for col in input_df.columns:
#         if isinstance(col[0], frozenset):
#             # input_df[col] = input_df[col].apply(lambda x: "_".join(x))
#             # input_df[col] = input_df[col].apply(lambda x: "_".join(x))
#             input_df[col] = input_df[col].apply(lambda x: x + "_HI!")
#             pass

#     input_df.to_csv(filepath + '.csv', sep=config.csv_separator, decimal=config.csv_decimal)
#     show(input_df)

# rules_cross_type = identify_cross_type_rules(rules)

process_dataframe(config, rules_cross_type, "rules_cross_type")
# cross_type_rules

kg_done = False


def print_kg_dict(config: Config, kg_dict, header):
    filepath = os.path.join(config.get_output_path(), "instance_relations.csv")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        total_comma = len(kg_dict) - 1
        for pos1, type1 in enumerate(kg_dict):
            preamble = "," * pos1
            for pos2, type2 in enumerate(kg_dict[type1]):
                intermediate = "," * (pos2 + 1)
                rest_comma = "," * (total_comma - pos1 - pos2)
                for i1, i2 in kg_dict[type1][type2]:
                    f.write(preamble + i1 + intermediate + i2 + rest_comma + "\n")


def knowledge_graph_population_cross_type_rules(
    config: Config, rules: association_rules, instance_types_dicts
):
    header = config.csv_separator.join(instance_types_dicts.keys())
    # Triangular dict
    dummy_dict = {}
    for instance_type in instance_types_dicts:
        dummy_dict[instance_type] = {}
        for type in instance_types_dicts:
            if type not in dummy_dict:
                dummy_dict[instance_type][type] = []
    for i, antecentent in enumerate(rules.antecedents):
        (antecentent,) = antecentent
        (consequent,) = rules.iloc[i].consequents
        first_type = None
        second_type = None
        for type in instance_types_dicts:
            if antecentent in instance_types_dicts[type]:
                # type1 = type
                if not first_type:
                    first_type = type
                    first_instance = antecentent
                else:
                    second_type = type
                    second_instance = antecentent
            if consequent in instance_types_dicts[type]:
                if not first_type:
                    first_type = type
                    first_instance = consequent
                else:
                    second_type = type
                    second_instance = consequent
            if first_type and second_type:
                break
        if first_type != second_type:
            dummy_dict[first_type][second_type].append(
                (first_instance, second_instance)
            )

    print_kg_dict(config, dummy_dict, header)

    return True


## Disabled. likely not needed anymore
# try:
#     kg_done = knowledge_graph_population_cross_type_rules(
#         config, rules_cross_type, director
#     )
# except Exception as e:
#     if config.debug:
#         raise e
#     else:
#         print(e)

# prepare csv file again
# process,software,data item,data model,data format specification,interchange format,data visualization,data validation,inference,source


@time_function
def knowledge_graph_population(
    config: Config,
    instance_types_dicts,
    property_types_dicts,
    instance_instance_proximity_matrix,
    proximity_instances,
):
    columns = list(instance_types_dicts.keys())
    # columns += list(property_types_dicts.keys())
    # columns = ['process', 'software', 'data item', 'data model', 'data format specification', 'data visualization', 'data validation', 'inference']

    rows = []
    for c_ID, column in enumerate(columns):
        for instance in instance_types_dicts[column]:
            # add the instance to the csv with each of their relations
            if instance not in proximity_instances:
                continue
            instance_index = proximity_instances.index(instance)
            for oc_ID, other_column in enumerate(columns):
                if other_column not in instance_types_dicts:
                    if other_column in property_types_dicts:
                        # TODO: handle properties specially
                        continue
                    continue
                if other_column != column:
                    other_column_instances = instance_types_dicts[other_column]
                    for other_instance in other_column_instances:
                        if other_instance not in proximity_instances:
                            continue
                        other_instance_index = proximity_instances.index(other_instance)
                        if (
                            instance_instance_proximity_matrix[instance_index][
                                other_instance_index
                            ]
                            > config.proximity_min_value
                        ):
                            # build row column by column
                            row = [""] * len(columns)
                            row[c_ID] = instance
                            row[oc_ID] = other_instance
                            rows.append(row)

    # write to csv
    filepath = os.path.join(config.get_output_path(), "instance_relations.csv")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(config.csv_separator.join(columns) + "\n")
        for row in rows:
            f.write(config.csv_separator.join(row) + "\n")
    return True


## Disabled. likely not needed anymore
# if not kg_done:
#     kg_done = knowledge_graph_population(
#         config,
#         instance_types_dicts,
#         property_types_dicts,
#         instance_instance_proximity_matrix,
#         proximity_instances,
#     )


from owlready2 import *
import pandas as pd
import types


# process,software,data item,data model,data format specification,interchange format,data visualization,data validation,inference,source
# process,software,data item,data model,data format specification


def save_as_owl(config: Config, path=None):
    onto_path = config.ontology_path
    df_cl = pd.read_csv(os.path.join(onto_path, "classes.csv"))
    df_re = pd.read_csv(os.path.join(onto_path, "relations.csv"))
    df_re = df_re.set_index("Domain\Range")
    if path is None:
        path = config.get_output_path()
    data_path = os.path.join(path, "instance_relations.csv")
    df = pd.read_csv(data_path)
    # df = pd.read_csv('data.csv')

    onto = get_ontology("http://tib.eu/slr")

    df_contributions = pd.read_csv(
        os.path.join(path, "paper_instance_occurrence_matrix.csv")
    )
    df_rules = pd.read_csv(os.path.join(path, "rules_cross_type.csv"))

    with open(os.path.join(path, "instance_types_dicts.json")) as file:
        inst_data = json.load(file)

    onto = get_ontology("http://tib.eu/slr")

    with onto:

        # Classes
        for ind, row in df_cl.iterrows():
            cl = types.new_class(row["URI"], (Thing,))
            cl.label = row["Label"]
            re = types.new_class(
                f'has{row["Label"].title().replace(" ", "")}', (ObjectProperty,)
            )
            re.label = f'has {row["Label"]}'

        # Instances
        for key, value in inst_data.items():
            cl = onto.search_one(label=key)
            if cl:
                for item in value:
                    inst = cl()
                    inst.label = item

        # Statements
        Contribution = types.new_class("Contribution", (Thing,))
        mentions = types.new_class("mentions", (ObjectProperty,))
        mentions.label = "mentions"
        for ind, row in df_contributions.iterrows():
            contrib_inst = Contribution()
            contrib_inst.label = row[0]
            for col in df_contributions.columns:
                if row[col]:
                    inst = onto.search_one(label=col)
                    if inst:
                        contrib_inst.mentions.append(inst)

        # Rules
        for ind, row in df_rules.iterrows():
            subj_inst = onto.search_one(label=row["antecedents"])
            obj_inst = onto.search_one(label=row["consequents"])
            if subj_inst and obj_inst:
                obj_cl = obj_inst.is_a[0]
                rel_label = f"has {str(obj_cl.label[0])}"
                rel = onto.search_one(label=rel_label)
                if rel:
                    rel[subj_inst].append(obj_inst)

    output_path = os.path.join(onto_path, "onto.owl")
    # onto.save('onto.owl')
    onto.save(output_path)
    onto.destroy()


# save_as_owl(config)


# prepare for ORKG
# header:
# paper:title,paper:authors,paper:publication_month,paper:publication_year,paper:published_in,paper:research_field,paper:doi,paper:url,contribution:research_problem,contribution:extraction_method,Property 1,Property 2


def flatten_nested_properties(data, pefix=""):
    res = {}
    for key, value in data.items():
        if isinstance(value, dict):
            res.update(flatten_nested_properties(value, f"{pefix}{key}:"))
        else:
            res[f"{pefix}{key}"] = value
    return res


class Paper:
    order = [
        "title",
        "authors",
        "publication_month",
        "publication_year",
        "published_in",
        "research_field",
        "doi",
        "url",
    ]

    def __init__(self, paperID, data={}):
        self.paperID: str = paperID
        self.title: str = data.get("title", "")
        ## now handled later
        # if self.title:
        #     self.title = '"' + self.title + '"'
        if self.title and "{" in self.title or "}" in self.title:
            self.title = self.title.replace("{", "").replace("}", "")
        self.authors: list[str] = data.get("author", "")
        if isinstance(self.authors, str):
            authors = self.authors.split("and ")
            if authors:
                for i, author in enumerate(authors):
                    name = author.split(",")
                    if len(name) > 1:
                        name = f"{name[1].strip()} {name[0].strip()}"
                    else:
                        name = name[0].strip()
                    authors[i] = name
            self.authors = "; ".join(authors)
        self.publication_month: int = data.get("publication_month", "")
        self.publication_year: int = data.get("year", "")
        self.published_in = ""
        for key in ["journal", "conference", "journal"]:
            if key in data:
                self.published_in = data[key]
                break
        self.research_field: str = data.get("research_field", "")
        if not self.research_field:
            # TODO: find a way to get the research field
            self.research_field = "R195"
        self.doi: str = data.get("doi", "")
        self.url: str = data.get("url", "")


class Contribution:
    def __init__(self, paperID, properties={}):
        self.paperID: str = paperID
        self.properties: dict = flatten_nested_properties(properties)


class ORKGComparison:
    def __init__(self):
        self.papers = {}  # paperID:paper data
        self.contibutions: dict[str:Contribution] = {}  # paperID:contribution data
        self.properties = {}

    def populate(
        self,
        config: Config,
        papers,
        instances,
        instance_types_dicts,
        paper_instance_occurrence_matrix,
        papers_metadata,
    ):
        # Create a dictionary to hold the count of existing values for each property
        property_ranges = {
            property: sum(
                value in instances for value in values
            )  # Count how many values exist in 'instances'
            for property, values in instance_types_dicts.items()  # Iterate over each property and its values
        }
        # floor = 0
        # for prop, value in property_ranges.items():
        #     property_ranges[prop] += floor
        #     floor += value

        for paperID, paper in enumerate(papers):
            paper_data = papers_metadata.get(paper, {})
            self.papers[paperID] = Paper(paper, paper_data)
            properties = {prop: [] for prop in property_ranges}
            floor = 0
            for prop, prop_range in property_ranges.items():
                for i in range(floor, floor + prop_range):
                    if paper_instance_occurrence_matrix[paperID][i] == 1:
                        properties[prop].append(instances[i])
                floor += prop_range
            self.contibutions[paperID] = Contribution(paper, properties)
        return self

    def populate_properties(self):
        for contribution in self.contibutions.values():
            for prop, value in contribution.properties.items():
                len_values = len(value) if isinstance(value, list) else 1
                if prop not in self.properties or self.properties[prop] < len_values:
                    self.properties[prop] = len_values
        return self.properties

    def get(self, key):
        if key == "properties" and not self.properties:
            self.populate_properties()
        return getattr(self, key)

    def save(self, config: Config, path=None, name="orkg_comparison"):
        if path is None:
            path = config.orkg_path
        filepath = os.path.join(path, name)
        if not filepath.endswith(".csv"):
            filepath += ".csv"

        rows = []
        row = ["paper:" + prop for prop in Paper.order]
        for prop, count in self.get("properties").items():
            # row += [f"contribution:{prop}"] * count
            row += [prop] * count
        rows.append(row)

        for paperID, contribution in self.contibutions.items():
            paper = self.papers[paperID]
            row = [getattr(paper, key, "") for key in Paper.order]
            for prop, count in self.properties.items():
                value = contribution.properties.get(prop, "")
                if not isinstance(value, list):
                    value = [value]
                len_taken = len(value)
                if len_taken < count:
                    value += [""] * (count - len_taken)
                row += value
            rows.append(row)

        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows:
                for id, item in enumerate(row):
                    if config.csv_separator in item:
                        if item.startswith('"') and item.endswith('"'):
                            continue
                        row[id] = '"' + item + '"'
                f.write(config.csv_separator.join(row) + "\n")


# orkg_comparison = ORKGComparison()
# orkg_comparison.populate(
#     config,
#     papers,
#     instances,
#     instance_types_dicts,
#     paper_instance_occurrence_matrix,
#     papers_metadata,
# )
# orkg_comparison.save(config)

for name, builder in director.builder.items():
    if not hasattr(builder, "matrix"):
        continue
    if name in ["year_instance_occurrence_matrix"]:
        continue
    rows = []
    candidates = ["papers", "instances"]
    for candidate in candidates:
        if hasattr(builder, candidate):
            rows = getattr(builder, candidate)
            break
    if not rows:
        raise Exception(f"Could not find rows for {name}")
    if isinstance(rows, dict):
        rows = list(rows.keys())

    cols = []
    candidates = ["instances", "literals"]
    for candidate in candidates:
        if hasattr(builder, candidate):
            cols = getattr(builder, candidate)
            break
    if not cols:
        raise Exception(f"Could not find cols for {name}")
    if isinstance(cols, dict):
        cols = list(cols.keys())

    process_matrix(director.config, builder.matrix, rows, cols, name)

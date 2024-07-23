from __future__ import annotations
from code_config import Config
from code_ontology import *
from code_helper import *
import os

# Step 1: find occurrences of instances in bag of words of papers
import pandas as pd
import json
import numpy as np

# visualize co-occurrences
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import pandas as pd


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


class Builder:
    def __init__(self, director: Director = None, config: Config = None):
        self.director: Director = director
        self.config = config if config else director.config if config else Config()

    def build(self):
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
        self.ontology.get_metadata("paper", self.config.folder_path)

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


class InstanceBuilder(Builder):
    def __init__(self, director: Director):
        super().__init__(director)

    def build(self):
        instance_types_dicts = {}

        # paper_instance_occurrence_matrix = np.zeros((), dtype=int)

        # TODO: Delete first 2 lines and see why this throws error then
        instance_types_dicts = self.csv_to_dict_of_sets(self.config.csv_file, self.config)

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

        self.instances = None

        self.size_x = None
        self.size_y = None
        self.dpi = None

    def save(self):
        self.build()

    def build(self):
        self.to_csv()
        if config.visualize:
            self.visualize_matrix(
                self.config,
                self.matrix,
                self.rows,
                self.columns,
                self.name,
                path=self.visualization_path,
            )
            # if instance_types_dicts:
            if self.instances:
                self.sankey(
                    self.config,
                    self.matrix,
                    self.rows,
                    self.name + "_sankey",
                    path=self.visualization_path,
                )
                if self.mode:
                    self.visualize_matrix_graph(
                        self.config,
                        self.matrix,
                        self.rows,
                        # instance_types_dicts,
                        self.name + "_graph",
                        path=self.visualization_path,
                        node_size_mode=self.config.proximity_mode,
                    )
                else:
                    self.visualize_matrix_graph(
                        self.config,
                        self.matrix,
                        self.rows,
                        # instance_types_dicts,
                        self.name + "_graph",
                        path=self.visualization_path,
                    )

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

    def visualize_matrix(
        self,
        config: Config,
        matrix: np.ndarray,
        rows: list[str],
        columns: list[str] = None,
        name: str = "some_matrix",
        format=".png",
        path=None,
    ) -> None:
        """
        Visualizes a matrix as a heatmap.
        matrix: The matrix to visualize
        rows: The labels for the rows
        columns: The labels for the columns
        name: The name of the file to save
        format: The format of the file to save (default: '.png', also accepts '.svg' and '.pdf', also accepts a list of formats)
        """

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

    def visualize_matrix_graph(
        self,
        config: Config,
        matrix,
        instances,
        # instance_types_dicts,
        name="some_matrix_graph",
        path=None,
        node_size_mode="sqrt",
        raise_mode="prune",
    ):
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

    def sankey(
        self,
        config: Config,
        matrix,
        instances,
        instance_types_dicts,
        name="some_sankey",
        path=None,
    ):
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


class MatrixBuilder(Builder):
    def __init__(self, director: Director):
        super().__init__(director)

        self.matrix: np.ndarray = None
        self.row_labels = []  # papers
        self.col_labels = []  # instances

        self.deletions = [np.array([]), np.array([])]
        # TODO: Likely add more proerties to map from full corpus to reduced corpus

    def save(self, name="some_matrix"):
        self.exporter: MatrixExporter = MatrixExporter(
            self.director, self.matrix, self.row_labels, self.col_labels, name
        )
        self.exporter.save()

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

        self.row_labels = self.get_labels(rows=True)
        self.col_labels = self.get_labels(rows=False)

    def get_labels(self, rows=True):
        if rows:
            return list(self.papers.keys())
        return list(self.instances.keys())

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


class ErrorMatrixBuilder(MatrixBuilder):
    def __init__(self, director: Director, pos_in_paper: PosInPaper):
        super().__init__(director)

        self.row_labels = list(director.papers.keys())
        self.col_labels = list(director.instances.keys())
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
        for paperID, paper in enumerate(self.row_labels):
            if paperID % 100 == 0:
                # print(f"Processing paper {paperID} of {len(papers)}")
                pass
            if paper in self.paper_full_text:
                for i, instance in enumerate(self.col_labels):
                    if self.paper_instance_occurrence_matrix[paperID][i] == 0:
                        continue
                    wcID = self.pos_in_paper.word_combination_index_literal[instance]
                    # TODO: handle if that instance has no word combination index entry
                    if wcID is None:
                        # word has no distance
                        continue
                    min_distance = self.pos_in_paper.find_min_distance_by_id(
                        paperID, wcID
                    )
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

        self.row_labels = self.handle_deletions(self.row_labels)
        self.col_labels = self.handle_deletions(self.col_labels, rows=False)

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

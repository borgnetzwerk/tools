from code_config import Config
from code_ontology import *
from code_helper import *
import os

class Director:
    def __init__(self, config: Config):
        self.config = config
        # self.ontology = Ontology()
        # self.ontology.load(config)

        self.builder:dict[str, Builder] = {}
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
                    "nlp_path": path_cleaning(os.path.join(self.config.papers_path, file))
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
                    if paper_name in self.included_papers or paper_name in self.excluded_papers:
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
            self.papers = {k:v for k, v in self.included_papers.items()}
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
        papers = {x: papers[x] for x in sorted(
            papers,
            key=lambda x: (
                getattr(papers[x], "year", "9999")
                if hasattr(papers[x], "year") else "9999"
            )
        )}
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
        self.builder['ObsidianFolder'] = ObsidianFolderBuilder(self)
        self.sync(self.builder['ObsidianFolder'])
        self.builder['ObsidianFolder'].build()
        
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


# Setup
from __future__ import annotations
import os


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

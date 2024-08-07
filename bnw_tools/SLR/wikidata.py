from .config import Config
from .helper import *
from .ontology import Ontology
import os
import requests
import json


class Wikidata:
    queries_done = 0
    query_limit = 100
    new_labels = 0
    new_entries = 0

    def __init__(self, config: Config = None):
        self.path = None
        self.entries = {}
        self.label_entry_map = {}
        if config:
            self.load(config)

    def print_updates():
        print(f"Queries done: {Wikidata.queries_done}")
        print(f"New labels: {Wikidata.new_labels}")
        print(f"New entries: {Wikidata.new_entries}")

    def save(self, config=None, path=None, name="wikidata.json"):
        if not path:
            if config:
                path = config.ontology_path
            elif self.path:
                path = self.path
            else:
                raise ValueError("No path given")
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(path, name)
        with open(filepath, "w", encoding="utf8") as f:
            data = {
                k: v
                for k, v in self.__dict__.items()
                if k not in ["queries_done", "new_labels", "new_entries"]
            }
            json.dump(data, f)

    def load(self, config, path=None, name="wikidata.json"):
        if not path:
            path = config.ontology_path
        self.path = path
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(path, name)
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf8") as f:
            data = json.load(f)
            data = {
                k: v
                for k, v in data.items()
                if k not in ["queries_done", "new_labels", "new_entries"]
            }
            for key, value in data.items():
                setattr(self, key, value)

    def get_by_list(self, label_list, expand=False):
        result = {}
        for label in label_list:
            res = self.get(label, expand=expand, raise_error=False)
            if res == None:
                continue
            else:
                result[label] = res
        return result
    
    def update_queryies_done(self, raise_error=True):
        if self.queries_done >= self.query_limit:
            self.save()
            if raise_error:
                raise ValueError(f"Query limit reached")
            else:
                print("Query limit reached")
            return True
        else:
            self.queries_done += 1
            return False


    def get(self, label, expand=False, raise_error=True):
        was_queried = False
        if label not in self.label_entry_map:
            was_queried = self.query(label)
        elif expand:
            current = len(self.label_entry_map[label])
            was_queried = self.query(label, offset=current)
        return self.label_entry_map.get(label, [])

    def update(self, ID, data, overwrite=True):
        changed = False
        if ID not in self.entries:
            self.entries[ID] = data
        else:
            # Chance to clean up data
            for key in ["labels", "descriptions", "aliases"]:
                if not data.get(key, {}):
                    continue
                if "en" in data[key]:
                    data[key] = data[key]["en"]
                    if isinstance(data[key], dict):
                        data[key] = value.get("value", None)
                    elif isinstance(data[key], list):
                        data[key] = [v.get("value", None) for v in data[key]]
                else:
                    data.pop(key)
            for key, value in data.items():
                if key in ['type', 'id']:
                    continue
                if key not in self.entries[ID]:
                    self.entries[ID][key] = value
                    changed = True
                elif self.entries[ID][key] != value and overwrite:
                    if isinstance(value, list):
                        self.entries[ID][key].extend(value)
                    elif isinstance(value, dict):
                        self.entries[ID][key].update(value)
                    else:
                        self.entries[ID][key] = value
                    changed = True
            # self.entries[ID].update(data)
        return changed

    def query_by_id(self, ID, save = True, props=["claims"]):
        if self.update_queryies_done(False):
            return None
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities",
            "format": "json",
            # "languages": "en",
            "ids": ID,
            # "props": "claims|descriptions|labels|sitelinks"
            "props": "|".join(props),
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False) == 1:
                result = result.get("entities", {}).get(ID, {})
                changed = self.update(ID, result)
                if changed and save:
                    self.save()
            return result
        else:
            response.raise_for_status()
        return None


    def get_by_id(self, ID, query=True, save=True, props=None):
        entry = self.entries.get(ID, None)
        if entry:
            if all(prop in entry for prop in props):
                if "aliases" in entry and len(entry["aliases"]) > 1:
                    # Currently, a single entry in "aliases" can also be gained from label lookup
                    # This checks if aliases already have been queried and extended 
                    return entry
        if props:
            res = self.query_by_id(ID, save, props)
        else:
            res = self.query_by_id(ID, save)
        if res:
            return res
        else:
            return None

    def query(self, label, limit=7, offset=0, raise_error=False):
        if self.update_queryies_done(raise_error):
            return False
        url = "https://www.wikidata.org/w/api.php"
        limit = min(limit, 50)
        params = {
            "action": "wbsearchentities",
            "search": label,
            "language": "en",
            "format": "json",
            "props": "concepturi",
            "limit": limit,
            "continue": offset,
        }

        #   {'id': 'Q107380696',
        #    'title': 'Q107380696',
        #    'pageid': 102658834,
        #    'concepturi': 'http://www.wikidata.org/entity/Q107380696',
        #    'repository': 'wikidata',
        #    'url': '//www.wikidata.org/wiki/Q107380696',
        #    'display': {'label': {'value': 'jupyter-client', 'language': 'en'},
        #     'description': {'value': 'Python library', 'language': 'en'}},
        #    'label': 'jupyter-client',
        #    'description': 'Python library',
        #    'match': {'type': 'label', 'language': 'en', 'text': 'jupyter-client'}}],

        response = requests.get(url, params=params)

        if response.status_code == 200:
            result = response.json()
            if label not in self.label_entry_map:
                self.label_entry_map[label] = []
                self.new_labels += 1           
            for entry in result["search"]:
                ID = entry.get("id", None)
                if not ID:
                    print(f"Error: No ID found for {label}: {entry}")
                    continue
                if ID not in self.entries:
                    self.entries[ID] = entry
                    self.new_entries += 1
                if ID not in self.label_entry_map[label]:
                    self.label_entry_map[label].append(ID)
            if not self.label_entry_map[label]:
                print(f"No entries found for {label}")
        else:
            response.raise_for_status()
        return True

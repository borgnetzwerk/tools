from __future__ import annotations
import os
import json
from bnw_tools.extract import util_zotero
from .config import Config
from .helper import *


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
            if isinstance(value, str):
                if value == "{}":
                    value = {}
                elif value == "[]":
                    value = []
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
            if not hasattr(self, prop):
                setattr(self, prop, value)
                was_updated = True
                continue
            current = getattr(self, prop)
            if current == value:
                continue
            elif force:
                print(f"Updating {self.label}: {prop} from {current} to {value}")
                setattr(self, prop, value)
                was_updated = True
                continue
        return was_updated


# Class,URI,Label,Laymans Term,Status
## e.g. process,software,data item,data model,data format specification,
class InstanceType(KnowledgeGraphEntry):  # Class
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
            instance_type = InstanceType(
                label, properties=properties, instance_properties=instance_properties
            )

        elif isinstance(instance_type, dict):
            # instance is still a dict
            properties = instance_type
            label = properties.get("label", label)
            instance_type = InstanceType(
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
        if isinstance(instance_type, str):
            instance_type = [instance_type]
        properties = {}
        for i_t in instance_type:
            if i_t in self.classes:
                instance_properties = self.classes[i_t].instance_properties
                if instance_properties:
                    properties.update(instance_properties)
        return {}

    def get(self, label):
        if label == "instances_by_class":
            self.update_instance_by_class()

        if hasattr(self, label):
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

    def sort(self):
        # FIXME: This is not working
        Warning("This function is not working")
        pass

    def save(self, config: Config = None, path=None, name="ontology.json", sort=True, indent=4):
        # FIXME: Needs to be completely reworked
        # Warning("This function is not working")
        # pass

        if path is None and config and hasattr(config, "ontology_path"):
            path = config.ontology_path
        else:
            path = ""

        filepath = os.path.join(path, name)

        data = json_proof(self.__dict__)

        with open(filepath, "w", encoding="utf8") as f:
            json.dump(data, f, indent=indent)

    def load(self, config, path=None, name="ontology.json", try_backup=True):
        if not path:
            path = config.ontology_path
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(path, name)

        try:
            data = {}
            try:
                with open(filepath, "r", encoding="utf8") as f:
                    data = json.load(f)
            except Exception as e:
                pass
            if not data:
                filepath = filepath.replace(".json", "_backup.json")
                with open(filepath, "r", encoding="utf8") as f:
                    data = json.load(f)
            # self.add_instances(data)
            for key, value in data.items():
                if key == "classes":
                    for label, instance_type in value.items():
                        self.add_class(instance_type, label)
                elif key == "instances":
                    for label, instance in value.items():
                        self.add_instance(instance, label)
                elif key == "relations":
                    for relation in value.items():
                        self.add_relation(relation)

        except Exception as e:
            self.load_csv(config, path, try_backup=try_backup)
            # TODO: handle if not loaded correctly
            # raise e

        self.update_instance_by_class()

    def load_csv(self, config, path=None, name="instances.csv", try_backup=True):
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

    def confirm(self, config:Config):
        a = input("Do you want to save the ontology? (y/n)")
        print(a)
        if a == "y":
            self.save(config, name="ontology_backup.json", indent=None)
        else:
            print("Ontology not saved.")

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

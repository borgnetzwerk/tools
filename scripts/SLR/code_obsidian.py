import os
import json
from code_ontology import *
from code_builder import *
from code_helper import *

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

    def __init__(
        self, director: Director = None, config=None, classes={}, instances={}
    ):
        super().__init__(director, config)

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
            # print(node.instance.label + ": " + node.path)
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

        print(
            "Added "
            + str(len(self.instances))
            + " instances and "
            + str(len(self.classes))
            + " classes to Obsidian folder"
        )

        # def __init__(self, path, properties={}):

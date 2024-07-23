from __future__ import annotations
import os
import json
from .ontology import *
from .builder import *
from .helper import *


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


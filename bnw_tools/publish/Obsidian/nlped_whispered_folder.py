# controllers.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...extract.nlp.util_nlp import Folder
from ...core import helper

from .. import util_wordcloud
from .. import util_pyplot

import urllib.parse
import os
import json
import re
from importlib.resources import as_file, files

LIMIT_BAG_OF_WORDS = 10
LIMIT_NAMED_ENTITIES = 5
SIM_THRESHOLD = 0.05


class ObsidianNote:
    def __init__(self, path=None, name=None, text=None, simVec=None):
        self.path = path
        self.name = name
        self.text = text or None
        self.related_note_ids = None
        if path and text is None:
            self.from_file(path)
        # if not self.iscomplete() and text:
        #     self.complete(text)
        if simVec:
            # TODO: Establish this function
            self.get_related_note_ids(simVec)

    def from_file(self, path):
        """
        Load transcript from the given path.

        Args:
            path (str): Path to the transcript file.
        """
        self.path = path
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf8") as f:
                    self.text = f.read()
        except Exception as e:
            print(e)

    def iscomplete(self):
        if self.text and self.path:
            return True
        return False

    def save(self, path=None):
        if path is None:
            path = self.path

        with open(path, "w", encoding="utf8") as f:
            f.write(self.text)

    def get_name(self, filename=None, fallback=None):
        if self.name and not filename:
            return self.name
        if self.path or filename:
            name = filename or os.path.basename(self.path)
        elif fallback:
            name = fallback
        else:
            raise Exception("This Obsidian note cannot find a name")

        if os.path.splitext(name) != ".md":
            name += ".md"
        self.name = helper.get_clean_title(name, obsidian=True)
        return self.name

    def get_path(self, parent_path=None):
        if parent_path:
            self.path = os.path.join(parent_path, self.get_name())
        return self.path

    def build_note(
        self,
        text,
        highlights=None,
        links=None,
        name=None,
        related_notes=None,
        files=None,
        additional_meta_data=None,
        rq_scores=None,
        folder_path=None,
        keyword_scores=None,
        visualizations=None,
    ):
        def dict_to_dataview(
            input_dict: dict[str, any],
            title="",
            join_char=", ",
            fromat_group="",
            open=True,
            end=True,
        ):
            res = ""
            is_empty = True
            if input_dict:
                if open:
                    res += f"%%{title}\n"
                elif title:
                    res += f"{title}\n"
                entry_counter = 0
                entry_sum = 0
                for key, value in input_dict.items():
                    if value == "" or value is None:
                        continue
                    if isinstance(value, str):
                        value = value.replace("\\", "/")
                    if fromat_group:
                        value = ", ".join(fromat_group.format(w) for w in value)
                    # TODO: turn this from a quick fix into a proper solution
                    entry_counter += 1
                    line = f"{key}:: {value}\n"
                    if title == "RQ Scores":
                        if key != f"RQ{entry_counter}":
                            line = f"RQ{entry_counter}:: {value}\n"
                        entry_sum += float(value)
                    res += line
                    is_empty = False
                # TODO: turn this from a quick fix into a proper solution
                if title == "RQ Scores":
                    res += f"RQsum:: {round(entry_sum,3)}\n"
                    res += f"RQave:: {round(entry_sum/entry_counter,3)}\n"
                if is_empty:
                    res = ""
                elif end:
                    res += f"%%\n\n"
            return res

        title = name or self.get_name()
        # if links:
        #     for link_name, words in links.items():
        #         metadata += f"{link_name}:: {', '.join('[[{}]]'.format(w) for w in words)}\n"
        # if highlights:
        #     for highlight_name, words in highlights.items():
        #         metadata += f"{highlight_name}:: {', '.join('**{}**'.format(w) for w in words)}\n"

        # if related_notes:
        #     metadata += f"Related Notes:: {', '.join('[[{}]]'.format(n) for n in related_notes)}\n"

        # todo: append more info here
        # if additional_meta:
        # metadata += f""

        corpus = ""
        for type, path in files.items():
            path = path.replace("\\", "/")

            corpus += f"\n\n## {type}"
            if type == "PDF":
                pdf_absolute_path = (
                    os.path.join(folder_path, path)
                    .replace(" ", "%20")
                    .replace("\\", "/")
                )
                corpus += f"\n* [Open PDF in default app]({pdf_absolute_path})"
            corpus += f"\n![[{path}]]"

        # Replace first occurrence of each word in text with a link if it's in links or highlights
        transcript = ""
        if text:
            for word in text.split():
                if word in links:
                    text = text.replace(word, f"[[{word}]]", 1)
                elif word in highlights:
                    text = text.replace(word, f"**{word}**", 1)
            transcript += f"\n\n## Transcript\n{text}"

        metadata = ""
        metadata += dict_to_dataview(
            links, fromat_group="[[{}]]", open=False, end=False
        )
        metadata += dict_to_dataview(
            highlights, fromat_group="**{}**", open=False, end=False
        )
        metadata += dict_to_dataview(
            related_notes, fromat_group="[[{}]]", open=False, end=False
        )
        if metadata:
            metadata = "\n\n%%\n" + metadata + "%%"

        fin_meta = ""
        if additional_meta_data:
            fin_meta += f"\n\n%%\n"
            for key, value in additional_meta_data.items():
                if value == "" or value is None:
                    continue
                if isinstance(value, str):
                    value = value.replace("\\", "/")
                fin_meta += f"{key}:: {value}\n"
            if fin_meta != f"%%\n":
                fin_meta += f"%%\n"
            else:
                fin_meta = ""

        fin_meta += "\n"
        fin_meta += dict_to_dataview(rq_scores, title="RQ Scores")
        rq_colon = ""
        for i in range(len(rq_scores)):
            rq_colon += f"\nRQ{i+1}_notes:: "

        related_cols = ""
        related_sort = ""
        if rq_scores:
            pieces = []
            for i, key in enumerate(rq_scores.keys()):
                if key == f"RQ{i+1}":
                    pieces.append(key)
                else:
                    pieces.append(f"{key} as RQ{i+1}")
            rq_sum = " + ".join(rq_scores.keys())
            pieces.append(f'round({rq_sum},3) as "Sum"')
            related_cols = "\n" + ", ".join(pieces)
            related_sort = f"\nSORT {rq_sum} desc"

        # ORKG block:
        ORKG_data = {}
        if additional_meta_data:
            url_suffix = None
            look_at = ["doi", "title"]
            while look_at and not url_suffix:
                check = look_at.pop(0)
                if check in additional_meta_data and additional_meta_data[check]:
                    url_suffix = additional_meta_data[check].replace("/", "%2F")
            if url_suffix:
                ORKG_data["ORKG_search"] = (
                    f"https://orkg.org/search/{urllib.parse.quote(url_suffix)}"
                )
        fin_meta += dict_to_dataview(ORKG_data, title="ORKG")

        if keyword_scores:
            fin_meta += dict_to_dataview(keyword_scores, title="Keyword Scores")

        ORKG_Document_Properties = ""
        if ORKG_data:
            for key in ORKG_data.keys():
                ORKG_Document_Properties += f"\n| {key} | `=this.{key}` |"

        # Rank according to age of paper

        property_block = ""
        property_view = f"""

## Document Properties
| Property | Value |
| --- | --- |
| Date | `=this.date` |
| Authors | `=this.author` |
| DOI | `=this.doi` |
| Published in | `=this.published_in` |
| Paper URL | `=this.url` |{ORKG_Document_Properties}
	(You can update this in edit mode at the end of the document)"""

        if visualizations:
            for vis in visualizations:
                property_view += f"\n![[{vis}]]"

        # Preserve existing content
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf8") as f:
                text = f.read()
                pieces = text.split("\n## Contributions\n")

                # try to make the cut outside of the content first (external)
                append = ""
                external_splitter = ["## PDF"]
                splitter = external_splitter + ["Contribution completed"]
                if len(pieces) > 1:
                    while not append and len(splitter):
                        test = splitter.pop(0)
                        if test in pieces[1]:
                            pieces = pieces[1].split(test)
                            append = test
                    if not append:
                        error = "Could not find the end of the contributions section."
                        print("Error on build_note for ", self.path)
                        print(error)
                        return error
                    # If we were able to make the cut outside of the content, we don't need to append anything
                    if append in external_splitter:
                        append = ""

                if len(pieces) > 1:
                    edited_indicators = [
                        # Has a tasked checked
                        "- [x]",
                        # Has a second contribution added
                        "### Contribution 2",
                    ]
                    edited_indicators_re = [
                        # r"review_score:: *[^\n]",
                        # r"review_comment:: *[^\n]",
                        # Has a property filled in
                        r":: +[^\n\\]+",
                    ]

                    edited = False
                    for indicator in edited_indicators:
                        if indicator in pieces[0]:
                            edited = True
                            break
                    if not edited:
                        for indicator in edited_indicators_re:
                            if re.search(indicator, pieces[0]):
                                edited = True
                                break

                    if edited:
                        property_block = "\n\n## Contributions\n" + pieces[0] + append

                        # TODO: better dynamic solution
                        legacy_updates = {
                            "notes_for_RQ1": "RQ1_notes",
                            "notes_for_RQ2": "RQ2_notes",
                            "notes_for_RQ3": "RQ3_notes",
                            "notes_for_RQ4": "RQ4_notes",
                        }
                        for legacy, new in legacy_updates.items():
                            property_block = property_block.replace(legacy, new)

        # todo see if i can compare these property_blocks better
        if not property_block:
            property_block = f"""

## Contributions
review_score:: 
review_comment:: 

### Contribution 1
research_problem:: 
result:: 
method:: 
material:: {rq_colon}
- [ ] Paper read
- [ ] Contribution completed"""
            
        # remove trailing \n from property_block
        # TODO: Improve the above construction of edited property_blocks, so that this is not necessary
        while property_block[-1] == "\n":
            property_block = property_block[:-1]

        self.text = f"""# {title}{property_view}{property_block}{corpus}

### Related Documents:
```dataview
TABLE{related_cols}
WHERE contains(file.inlinks, this.file.link){related_sort}
```{transcript}{metadata}{fin_meta}
"""


# Directly from dictionary
# TODO: Make this package-worthy

# with open(os.path.join("bnw_tools","ORKG", "ResearchFields.json")) as json_file:

# a = files('bnw_tools.ORKG')
# b = a.joinpath('ResearchFields.json')
# c = as_file(b)

# with open(as_file((files('bnw_tools.ORKG').joinpath('ResearchFields.json')))) as json_file:

with open(files("bnw_tools.ORKG").joinpath("ResearchFields.json")) as json_file:
    meta = json.load(json_file)

RF_map = {}
for rf in list(meta.values())[0]:
    RF_map.update({rf["id"]: rf["label"]})
RF_map = {k: v for k, v in sorted(RF_map.items(), key=lambda item: int(item[0][1:]))}

# with open(os.path.join(root_stepup, "bnw_tools","ORKG", "RF_Map.json"), 'w') as outfile:
with open((files("bnw_tools.ORKG").joinpath("RF_Map.json")), "w") as outfile:
    json.dump(RF_map, outfile, indent=4)

RF_patterns = {}
for raw_field in RF_map.values():
    pot_fields = raw_field
    if " " not in raw_field:
        continue
    fields = []
    master = ""
    patterns = []
    if " of " in raw_field:
        master = raw_field.split(" of ", 1)[0]
        pot_fields.replace(f"{master} of ", "")
        master = re.escape(master) + r"*"
    elif " and " in raw_field:
        temp = raw_field.split(" and ", 1)[1]
        if " " in temp:
            temp = " ".join(temp.split(" ", 1)[1:])
            master = re.escape(temp) + r"*"
    fields = re.split(",|/| and ", raw_field)
    fields = [field.strip(" ") for field in fields]
    if "" in fields:
        fields.remove("")
    if len(fields) > 1:
        for field in fields:
            pat = r"\b" + re.escape(field) + r"\b"
            patterns.append(pat + r".*" + master)
            patterns.append(master + r".*" + pat)
    if patterns:
        RF_patterns[raw_field] = patterns


def identify_field_weight(field, content):
    if field in content:
        return 1
    elif field in RF_patterns:
        # Is: "Electrical Engineering"
        # Field: "Electrical and Computer Engineering"
        for pattern in RF_patterns[field]:
            if re.search(pattern, content):
                return 1  # maybe weigh this less?


def update_RF(meta):
    # TODO
    # Attempt to get RF:
    weights = {
        "booktitle": 10,
        "journaltitle": 10,
        "title": 4,
        # "abstract": 1,
    }
    assume = {}
    for search_key, weight in weights.items():
        if search_key in meta:
            for RF_id, field in RF_map.items():
                # TODO:
                value = identify_field_weight(field, meta[search_key])
                if value:
                    if RF_id not in assume:
                        assume[RF_id] = 0
                    assume[RF_id] = value * weight
    assume = {
        k: v for k, v in sorted(assume.items(), key=lambda item: item[1], reverse=True)
    }
    highest = 0
    results = []
    for RF_id, value in assume.items():
        # TODO multiple matches?

        for result in results:
            # check if "Engineering" could be made "Computer Engineering"
            comp = identify_field_weight(RF_map[result], RF_map[RF_id])
            if comp:
                # "Engineering" is in "Computer Engineering"
                results.remove(result)
                results.append(RF_id)
                highest = value
                continue

        if value >= highest:
            if RF_id not in results:
                results.append(RF_id)
            highest = value

            # 'R137': 10,     "R137": "Numerical Analysis/Scientific Computing",
            # 'R194': 10,     "R194": "Engineering",
            # 'R237': 10,     "R237": "Electrical and Computer Engineering",
            # 'R241': 10,     "R241": "Electrical and Electronics",
            # 'R254': 10,     "R254": "Materials Science and Engineering",
            # 'R201': 4     "R201": "Structures and Materials",
    # If you want to be able to read the results
    # results = [RF_map[x] for x in results]
    if results:
        # data.update({f"paper:{key}": "orkg:" + "; orkg:".join(results)})
        # data.update({f"paper:{key}": "; ".join(results)})
        # data.update({f"paper:{key}" : f"orkg:{results[-1]}"})
        meta.update({f"research_field": f"{results[-1]}"})
        meta.update({f"research_field_label": f"{RF_map[results[-1]]}"})
    return meta


def folder(
    folder: Folder,
    limit_ns=LIMIT_BAG_OF_WORDS,
    limit_ne=LIMIT_NAMED_ENTITIES,
    force=False,
):
    # loop over each file in the directory
    # build Entry Node
    # Sort all files into subfolders

    for idr, mr in enumerate(folder.media_resources):
        if not mr.obsidian_note:
            mr.add_obsidian_note()
        mr.obsidian_note.get_name(mr.original_name, fallback=mr.basename)
        mr.obsidian_note.get_path(folder.notes.path)

        # Create the Obsidian directory if it does not exist,

        bag_of_words = list(mr.nlp_analysis.bag_of_words.tf_idf.keys())[
            : LIMIT_BAG_OF_WORDS + LIMIT_NAMED_ENTITIES
        ]
        named_entities = list(mr.nlp_analysis.named_entities.get().keys())[
            :LIMIT_NAMED_ENTITIES
        ]

        for name in named_entities:
            lookfor = set([name.lower()]).union(name.lower().split())
            for word in lookfor:
                if word in bag_of_words:
                    bag_of_words.remove(word)
        bag_of_words = bag_of_words[:LIMIT_BAG_OF_WORDS]

        links = {}
        highlights = {}

        if named_entities:
            links["named_entities"] = named_entities

        if bag_of_words:
            highlights["bag_of_words"] = bag_of_words

        files = {}
        if mr.audio_file:
            files["Audio"] = os.path.basename(mr.audio_file.path)
        if mr.pdf:
            files["PDF"] = os.path.relpath(mr.pdf.path, folder.path)

        simVec = folder.sim_matrix[idr]
        top_indices = simVec.argsort()[-6:-1]
        related_notes = []
        for i in top_indices:
            # check if similarity is high enough
            if simVec[i] < SIM_THRESHOLD:
                break
            cr = folder.media_resources[i]
            related_notes.append(cr.obsidian_note.get_name(cr.original_name))
        related_notes = {"Related Notes": related_notes}
        text = None
        if mr.transcript:
            text = mr.transcript.text

        meta = {}
        if mr.pdf and mr.pdf.metadata:
            meta.update(mr.pdf.metadata)
        if mr.info:
            block = mr.info.__dict__
            del block["thumbnail_urls"]
            del block["cap_codes"]
            meta.update(block)

        if meta:
            # research field:
            # update_RF(meta)

            # date
            if "date" in meta:
                values = meta["date"].split("-")
                meta.update({"publication_year": values[0]})
                if len(values) > 1:
                    meta.update({"publication_month": values[1]})

            # date
            for key in ["booktitle", "journaltitle"]:
                if key in meta:
                    meta.update({"published_in": meta[key]})
                    break
        rq_scores = {}
        try:
            if folder.rq and folder.rq.research_questions:
                for id_rq, rq in enumerate(folder.rq.research_questions):
                    rq_scores.update({rq.tag: round(folder.rq_sim_mat[idr][id_rq], 3)})
        except Exception as e:
            print(e)

        name = mr.original_name

        if mr.pdf and mr.pdf.metadata:
            if "title" in mr.pdf.metadata:
                name = mr.pdf.metadata["title"]
        elif mr.info:
            if hasattr(mr.info, "title"):
                name = mr.info.title

        keyword_scores = None
        if mr.keyword_scores:
            keyword_scores = {}
            for key, value in mr.keyword_scores.items():
                keyword_scores["keys_" + key.replace(" ", "_")] = value

        # Visualizations
        # paused while not fully solved for many keywords
        visualizations = []
        hold_visualizations_for_now = False
        if sum(mr.keyword_scores.values()) and not hold_visualizations_for_now:
            keyword_bar_path = mr.obsidian_note.path.replace(
                "03_notes", "03_visualizations"
            )
            keyword_bar_path = keyword_bar_path.replace(".md", "_bar.png")
            # todo: shift this to a more general location
            # all non 0 elements in mr.keyword_scores:
            data = {k: v for k, v in mr.keyword_scores.items() if v > 0}

            ylabel = "% of max"
            title = "Relevant Keywords frequency present in this document, compared to the maximum found in any document."
            util_pyplot.dict_to_barchart(
                data,
                path=keyword_bar_path,
                sort=True,
                ylabel=ylabel,
                title=title,
                limit=0,
            )
            visualizations.append(keyword_bar_path)

            keyword_cloud_path = keyword_bar_path.replace("_bar.png", "_cloud.png")
            util_wordcloud.generate_wordcloud(
                data, keyword_cloud_path, width=1900, height=300
            )
            visualizations.append(keyword_cloud_path)

            for i in range(len(visualizations)):
                # remove folder.path from keyowrd_bar_path
                visualizations[i] = os.path.relpath(visualizations[i], folder.path)
                visualizations[i] = visualizations[i].replace("\\", "/")

        errors = mr.obsidian_note.build_note(
            text,
            links=links,
            highlights=highlights,
            name=name,
            related_notes=related_notes,
            files=files,
            additional_meta_data=meta,
            rq_scores=rq_scores,
            folder_path=folder.path,
            keyword_scores=keyword_scores,
            visualizations=visualizations,
        )

        if not errors:
            # create the markdown file
            mr.obsidian_note.save()

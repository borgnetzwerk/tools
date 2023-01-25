import csv
import json
import re
import helper
# import urllib.request
# page = urllib.request.urlopen('https://orkg.org/api/classes/ResearchField/resources/?page=0&size=999')
# print(page.read())
# a = page.read()
# RF_WEB = json.loads(page.text)

# Using a JSON string

# Directly from dictionary
with open('ORKG/ResearchFields.json') as json_file:
    data = json.load(json_file)

RF_map = {}
for rf in list(data.values())[0]:
    RF_map.update({rf['id']: rf['label']})
RF_map = {k: v for k, v in sorted(
    RF_map.items(), key=lambda item: int(item[0][1:]))}

with open('ORKG/RF_Map.json', 'w') as outfile:
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
            temp = " " .join(temp.split(" ", 1)[1:])
            master = re.escape(temp) + r"*"
    fields = re.split(',|/| and ', raw_field)
    fields = [field.strip(' ') for field in fields]
    if "" in fields:
        fields.remove("")
    if len(fields) > 1:
        for field in fields:
            pat = r"\b" + re.escape(field) + r"\b"
            patterns.append(pat + r".*" + master)
            patterns.append(master + r".*" + pat)
    if patterns:
        RF_patterns[raw_field] = patterns


def update_string(data, key, value):
    data.update({f"paper:{key}": value})
    return data


def update_list(data, key, value):
    values = value.split(", ")
    data.update({f"paper:{key}": ";".join(values)})
    return data


def update_authors(data, key, value):
    values = value.split(" and ")
    true_values = []
    for value in values:
        true_values += value.split(" and ")
    values = true_values
    true_values = []
    for value in values:
        result = value
        if "," in value:
            group = value.split(",")
            if len(group) == 2:
                result = group[1] + " " + group[0]
            else:
                print('Found an author with >2 "," : ' + value)
        true_values.append(result)
    values = true_values
    data.update({f"paper:{key}": ";".join(values)})
    return data


def update_date(data, key, value):
    values = value.split("-")
    data.update({f"paper:publication_year": values[0]})
    if len(values) > 1:
        data.update({f"paper:publication_month": values[1]})
    return data


def identify_field_weight(field, content):
    if field in content:
        return 1
    elif field in RF_patterns:
        # Is: "Electrical Engineering"
        # Field: "Electrical and Computer Engineering"
        for pattern in RF_patterns[field]:
            if re.search(pattern, content):
                return 1  # maybe weigh this less?


def update_RF(data, key, tex):
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
        if search_key in tex:
            for RF_id, field in RF_map.items():
                # TODO:
                value = identify_field_weight(field, tex[search_key])
                if value:
                    if RF_id not in assume:
                        assume[RF_id] = 0
                    assume[RF_id] = value * weight
    assume = {k: v for k, v in sorted(
        assume.items(), key=lambda item: item[1], reverse=True)}
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
        data.update({f"paper:{key}": f"{results[-1]}"})
    return data


def update_research_problem(data, key, value):
    # TODO
    # values = value.split(" and ")
    # [
    #     "This work addresses"
    # ]
    # data.update({f"paper:{key}": "; ".join(values)})
    return data


def tex_to_csv_format(tex):
    data = {}
    handlers = {
        "title": update_string,
        "authors": update_authors,
        "publication_year": update_date,
        "published_in": update_string,
        "research_field": update_RF,
        "doi": update_string,
        "url": update_string,
        "research_problem": update_research_problem,

        # End of fixed:
        "keywords": update_list,
        # "location": update_string,
        # "abstract": update_string,
        # "publication_month": update_string,
    }
    tex_map = {
        "authors": ["author"],
        "publication_year": ["date"],
        "published_in": ["booktitle", "journaltitle"],
    }
    tex_advanced = [
        "research_field",
        "research_problem",
    ]
    for key in handlers:
        searchfor = [key]
        if key in tex_map:
            searchfor += tex_map[key]
        for search_key in searchfor:
            if search_key in tex:
                data = handlers[key](data, key, tex[search_key])
            elif search_key in tex_advanced:
                data = handlers[key](data, key, tex)
    return data


def write_to_csv(data, path):
    header_names = set()
    for entry in data:
        header_names.update(entry.keys())
    helper.write_to_csv(header_names, data, path)
        


def main(tex, path=None):
    data = tex_to_csv_format(tex)
    if path:
        write_to_csv([data], path)
    else:
        return data
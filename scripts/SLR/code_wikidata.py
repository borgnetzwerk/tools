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

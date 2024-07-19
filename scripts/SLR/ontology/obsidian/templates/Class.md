---
label: 
source: 
subclass_of: 
  - 
aliases: 
tags:
  - class
wikidata_uri: 
orkg_uri: 
wikidata_candidates: 
  - 
orkg_candidates:
  - 
---

## Instances
```dataview
TABLE WITHOUT ID 
file.link AS "Instance", wikidata_uri AS "Wikidata URI", orkg_uri AS "ORKG URI"
WHERE contains(instance_of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata_uri DESC, orkg_uri DESC, file.name ASC
```

## Subclasses
```dataview
TABLE WITHOUT ID 
file.link AS "Subclasses", wikidata_uri AS "Wikidata URI", orkg_uri AS "ORKG URI"
WHERE contains(subclass_of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata_uri DESC, orkg_uri DESC, file.name ASC
```

## Other Mentions
```dataview
TABLE WITHOUT ID 
file.link AS "Node", wikidata_uri AS "Wikidata URI", orkg_uri AS "ORKG URI"
WHERE contains(file.outlinks, this.file.link) and !contains(instance_of, this.file.link) and !contains(subclass_of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata_uri DESC, orkg_uri DESC, file.name ASC
```

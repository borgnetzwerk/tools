---
label: 
layman term: 
  - 
source: 
subclass of: 
  - 
aliases: 
tags:
  - class
wikidata ID: 
orkg ID: 
wikidata candidates: 
  - 
orkg candidates:
  - 
---

## Instances
```dataview
TABLE WITHOUT ID 
file.link AS "Instance", wikidata-id AS "wikidata ID", orkg-id AS "orkg ID"
WHERE contains(instance-of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata-id DESC, orkg-id DESC, file.name ASC
```

## Subclasses
```dataview
TABLE WITHOUT ID 
file.link AS "Subclasses", wikidata-id AS "wikidata ID", orkg-id AS "orkg ID"
WHERE contains(subclass-of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata-id DESC, orkg-id DESC, file.name ASC
```

## Other Mentions
```dataview
TABLE WITHOUT ID 
file.link AS "Node", wikidata-id AS "wikidata ID", orkg-id AS "orkg ID"
WHERE contains(file.outlinks, this.file.link) and !contains(instance-of, this.file.link) and !contains(subclass-of, this.file.link) AND !contains(file.path, "templates")
SORT wikidata-id DESC, orkg-id DESC, file.name ASC
```

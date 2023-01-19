import re

text = """
'---\nyear: 2019\ntitle: Systematic evaluation of the interface description for fluid–structure interaction simulations using the isogeometric mortar-based mapping\nauthors: Andreas Apostolatos, Guillaume De Nayer, Kai-Uwe Bletzinger, Michael Breuer, Roland Wüchner\nin: Journal of Fluids and Structures\npage: 368–399\nciteTitle: [[@apostolatos_systematic_2019|Systematic evaluation of the interface description for fluid–structure interaction simulations using the isogeometric mortar-based mapping]]\nciteID: \\[[[@apostolatos_systematic_2019|00]]\\]\n---\nurl: https://www.sciencedirect.com/science/article/pii/S0889974618307308\nzotero: [zotero://select/items/@apostolatos_systematic_2019](zotero://select/items/@apostolatos_systematic_2019)\n\n---\n\ntags:: #science #literature\nread?:: #read/false\ncomment::  \n\n---\n\n# Learning\n\n## Key notes\n\n\n## Quotes\n\n\n# Abstract\nWithin this study the influence of the interface description for partitioned Fluid–Structure Interaction (FSI) simulations is systematically evaluated. In particular, a Non-Uniform Rational B-Spline (NURBS)-based isogeometric mortar method is elaborated which enables the transfer of fields defined on low-order and isogeometric representations of the interface along which the FSI constraints are defined. Moreover, the concept of the Exact Coupling Layer (ECL) using the proposed isogeometric mortar-based mapping method is presented. It allows for smoothing fields that are transferred between two standard low-order surface discretizations applying the exact interface description in terms of NURBS. This is especially important for highly turbulent flows, where the artificial roughness of the low-order faceted FSI interfaces results in spurious flow fields leading to inaccurate FSI solutions. The approach proposed is subsequently compared to the standard mortar-based mapping method for transferring fields between two low-order surface representations (finite volume method for the fluid and finite element method for the structure) and validated on a simple lid-driven cavity FSI benchmark. Then, the physically motivated 3D example of the turbulent flow around a membranous hemisphere (Wood et al., 2016) is considered. Its behavior is predicted by combining the large-eddy simulation technique with the isogeometric analysis to demonstrate the usefulness of the isogeometric mortar-based mapping method for real-world FSI applications. Additionally, the test case of a bluff body significantly deformed in an eigenmode shape of the aforementioned hemisphere is used. For this purpose, both “standard” low-order finite element discretizations and a smooth IGA-based description of the structural surface are considered. This deformation is transferred to the fluid FSI interface and the influence of the interface description on the fluid flow is analyzed. Finally, the computational costs related to the presented methodology are evaluated. The results suggest that the proposed methodology can effectively improve the overall FSI behavior with minimal effort by considering the exact geometry description based on the Computer-Aided Design (CAD) model of the FSI interface.\n\n# Full Text\n![[Apostolatos et al. - 2019 - Systematic evaluation of the interface description.pdf]]\n'
"""

to = """
---
year: 2007
title: "DBpedia: A nucleus for a web of open data"
authors: "Sören Auer, Christian Bizer, Georgi Kobilarov, Jens Lehmann, Richard Cyganiak, Zachary Ives"
in: "The semantic web"
page: 722–735
---
```citeTitle:
[[@hutchison_dbpedia_2007|DBpedia: A nucleus for a web of open data]]
```
```citeID: 
\[[[@hutchison_dbpedia_2007|00]]\]
```
---
url: https://www.sciencedirect.com/science/article/pii/S0889974618307308
zotero: [zotero://select/items/@apostolatos_systematic_2019](zotero://select/items/@apostolatos_systematic_2019)

---
tags:: #science #literature
read?:: #read/false
comment::  

---
# Learning
"""   

def reformat(text):
    splitter = "\n# Learning\n"
    pieces = text.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]
    finddict = {
        "year" : '(?<=year: ).*?(?=\\n)',
        "title" : '(?<=title: ).*?(?=\\n)',
        "authors" : '(?<=authors: ).*?(?=\\n)',
        "var_in" : '(?<=in: ).*?(?=\\n)',
        "page" : '(?<=page: ).*?(?=\\n)',
        "citeTitle" : '(?<=citeTitle: ).*?(?=\\n)',
        "citeID" : '(?<=citeID: ).*?(?=\\n)',
        "url" : '(?<=url: ).*?(?=\\n)',
        "zotero" : '(?<=zotero: ).*?(?=\\n)',
        "tags" : '(?<=tags:: ).*?(?=\\n)',
        "read?" : '(?<=read\?:: ).*?(?=\\n)',
        "comment" : '(?<=comment:: ).*?(?=\\n)',
    }
    dic_var = {}
    for key, value in finddict.items():
        dic_var[key] = re.search(value, work).group()
    
    build = "---\n"
    build += "year: " + dic_var["year"] + "\n"
    build += "title: \"" + dic_var["title"] + "\"\n"
    build += "authors: \"" + dic_var["authors"] + "\"\n"
    build += "in: \"" + dic_var["var_in"] + "\"\n"
    build += "page: " + dic_var["page"] + "\n"
    build += "---\n"
    build += "```citeTitle:\n" + dic_var["citeTitle"] + "\n```\n"
    build += "```citeID:\n" + dic_var["citeID"] + "\n```\n"
    build += "---\n"
    build += "url: " + dic_var["url"] + "\n"
    build += "zotero: " + dic_var["zotero"] + "\n"
    build += "\n---\n"
    build += "tags:: " + dic_var["tags"] + "\n"
    build += "read?:: " + dic_var["read?"] + "\n"
    build += "comment:: " + dic_var["comment"] + "\n"
    build += "\n---"


    return build + splitter + rest

def reformat(text):
    splitter = "\n# Learning\n"
    pieces = text.split(splitter, 1)
    work = pieces[0]
    rest = pieces[1]
    
    # Extract values of fields using regular expression
    date = re.search(r'(?<=year: ).*?(?=\n)', work).group()
    title = re.search(r'(?<=title: ).*?(?=\n)', work).group()
    authors = re.search(r'(?<=authors: ).*?(?=\n)', work).group()
    in_ = re.search(r'(?<=in: ).*?(?=\n)', work).group()
    page = re.search(r'(?<=page: ).*?(?=\n)', work).group()
    cite_title = re.search(r'(?<=citeTitle:[\n ]).*?(?=\n)', work).group()
    cite_id = re.search(r'(?<=citeID:[\n ]).*?(?=\n)', work).group()
    url = re.search(r'(?<=url: ).*?(?=\n)', work).group()
    zotero = re.search(r'(?<=zotero: ).*?(?=\n)', work).group()
    tags = re.search(r'(?<=tags:: ).*?(?=\n)', work).group()
    read = re.search(r'(?<=read\?:: ).*?(?=\n)', work).group()
    comment = re.search(r'(?<=comment:: ).*?(?=\n)', work).group()
    
    # Build output string using string formatting method
    build = "---\n"
    build += f"year: {date}\n"
    build += f"title: {title}\n"
    build += f"authors: {authors}\n"
    build += f"in: {in_}\n"
    build += f"page: {page}\n"
    build += "---\n"
    build += f"```citeTitle:\n{cite_title}\n```\n"
    build += f"```citeID:\n{cite_id}\n```\n"
    build += "---\n"
    build += f"url: {url}\n"
    build += f"zotero: {zotero}\n"
    build += "\n---\n"
    build += f"tags:: {tags}\n"
    build += f"read?:: {read}\n"
    build += f"comment:: {comment}\n"
    build += "\n---\n"
    output_string = build + splitter + rest
    return output_string

text = reformat(text)
print(text)
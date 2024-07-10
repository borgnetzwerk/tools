# SLR

## Notebook
[co_occurence.ipynb](co_occurence.ipynb)
This notebook contains the entire code for creating our visualizations and knowledge graph

## Background
Essentially, this work analyzes 1000 documents to identify the answers to these questions:

- **RQ1**: By which means, such as knowledge representations and schemas, do aerospace engineers externalize, such as formalize and visualize, knowledge?
- **RQ2**: By which means, such as knowledge bases and services, do aerospace engineers utilize, such as organize and interface with, explicit knowledge?
- **RQ3**: By which means, such as tools and methods, do aerospace engineers exchange, such as transfer and distribute, explicit knowledge?

Summing these up, we're basically looking for the answer:

- Which Aerospace Engineering **Task** is completed by which **Tool** using which **Data** in which **Format** and **Schema**?

As a result, we have identified over 300 Tasks, Tools, Data Items, Data Formats and Data Schemas and measure their (co-)occurrence in 1000 papers.

By manually checking a subset of these Papers, we can validate our data analysis.

We also extend our findings with a survey you can contribute to right now:

- https://survey.uni-hannover.de/index.php/589597

### Results
Paper instance occurence matrix, showing if an instance (column) occurs in a given paper (row). 
![paper_instance_occurrence_matrix](<images\paper_instance_occurrence_matrix.png>)

Instance - Instance - co-occurence, showing how many times instances co-occured in the same document.
![instance_instance_co_occurrence_matrix](<images\instance_instance_co_occurrence_matrix.png>)

Instance - Instance - proximity, showing how close instances co-occured in the same document. Scores are sum(1/sqrt(distance)), so 100 characters distance award .1 points, while neighbors get full points 
![instance_instance_proximity_matrix](<images\instance_instance_proximity_matrix.png>)
![instance_instance_proximity_matrix_graph](<images\instance_instance_proximity_matrix_graph.png>)
![instance_instance_proximity_matrix_sankey](<images\instance_instance_proximity_matrix_sankey.png>)

We can also plot the absolute & relative occurence of any process, software etc. in any given year:
![year_instance_occurrence_matrix_process_008_to_014](<images\year_instance_occurrence_matrix_process_008_to_014.png>)
![year_instance_occurrence_matrix_software_013_to_020](<images\year_instance_occurrence_matrix_software_013_to_020.png>)
![year_instance_occurrence_matrix_data_model_001_to_008](<images\year_instance_occurrence_matrix_data_model_001_to_008.png>)
![year_instance_occurrence_matrix_data_item_008_to_015](<images\year_instance_occurrence_matrix_data_item_008_to_015.png>)
![year_instance_occurrence_matrix_data_format_specification_010_to_017](<images\year_instance_occurrence_matrix_data_format_specification_010_to_017.png>)

### Additional Data
The error_matrix holds all evidence of instance occurences did not pass the different metrics to count as "true" occurence: e.g. a "system administrator" only counts as such if both words occur close enough to eachother. An "administrator of the system" counts, while "system [...] administrator" with [...] being > 1000 characters does not count. The matrix shows the logarithmic distance (4 = 10.000 characters distance), or a -1 if earlier metrics suggested an occurence, but no single match could be found in the fulltext. 
![Caption](<images\error_matrix.png)
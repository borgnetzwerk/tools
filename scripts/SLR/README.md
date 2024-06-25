# SLR

## Notebook
[co_occurence.ipynb](co_occurence.ipynb)
This notebook contains the entire code for creating our visualizations and knowledge graph

## Background
Paper instance occurence matrix, showing if an instance (column) occurs in a given paper (row). 
![Caption](<data\visualization\paper_instance_occurrence_matrix.png)

The error_matrix holds all evidence of instance occurences did not pass the different metrics to count as "true" occurence: e.g. a "system administrator" only counts as such if both words occur close enough to eachother. An "administrator of the system" counts, while "system [...] administrator" with [...] being > 1000 characters does not count. The matrix shows the logarithmic distance (4 = 10.000 characters distance), or a -1 if earlier metrics suggested an occurence, but no single match could be found in the fulltext. 
![Caption](<data\visualization\error_matrix.png)

Instance - Instance - co-occurence, showing how many times instances co-occured in the same document.
![Caption](<data\visualization\instance_instance_co_occurrence_matrix.png)

Instance - Instance - proximity, showing how close instances co-occured in the same document. Scores are sum(1/sqrt(distance)), so 100 characters distance award .1 points, while neighbors get full points 
![Caption](<data\visualization\instance_instance_proximity_matrix.png)

![Caption](<data\visualization\instance_instance_proximity_matrix_graph.png)

![Caption](<data\visualization\instance_instance_proximity_matrix_sankey.png)


![Caption](<data\visualization\year_instance_occurrence_matrix_data_format_specification_001_to_009.png)

![Caption](<data\visualization\year_instance_occurrence_matrix_data_item_001_to_007.png)

![Caption](<data\visualization\year_instance_occurrence_matrix_data_model_001_to_008.png)

![Caption](<data\visualization\year_instance_occurrence_matrix_process_001_to_008.png)

![Caption](<data\visualization\year_instance_occurrence_matrix_software_001_to_007.png)


´´´









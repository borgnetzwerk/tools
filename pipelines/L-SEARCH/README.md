# L-SEARCH - Literature Survey and Extraction using AI and Research Tools

L-SEARCH is a tool that combines AI and research tools to simplify the process of conducting literature surveys and extracting relevant information from academic papers. This README file will guide you through the setup process.

## Phase 0: Setup

### Zotero

Zotero is a free and open-source reference management software that helps you organize your research sources. To use L-SEARCH, you'll need to create a Zotero account and install the software. 

1. Create a Zotero account at https://www.zotero.org/user/register/.
2. Download and install Zotero for your operating system from https://www.zotero.org/download/.
3. Install the Zotero Connector for your web browser. You can find the connectors for Chrome, Firefox, and Safari at https://www.zotero.org/download/.

### Python

L-SEARCH is written in Python, so you'll need to have Python installed on your computer to use it. We recommend using Python 3.7 or higher.

1. Download and install Python for your operating system from https://www.python.org/downloads/.
2. Verify that Python is installed correctly by opening a terminal or command prompt and running the following command: 

´´´
python --version
´´´

This should print the version number of Python installed on your system.

## Phase 1: Preparation Run
The preparation run involves several tasks to prepare for the literature search. These tasks are:

### 1.1 Search query
The search query task involves identifying relevant keywords and phrases related to the topic of interest. These can be identified through previous and related work, base material such as a project proposal or a call for contribution. These initial keywords can be extended by utilizing AI tools, as well as by using overview projects such as Open Knowledge Maps. The goal is to generate a weighted list of search terms.

#### 1.1.1 Search term extraction
This task involves identifying relevant keywords and phrases related to the topic of interest. These can be identified through previous and related work, base material such as a project proposal or a call for contribution. These initial keywords can be extended by utilizing of AI tools, as well as by usage of overview projects such as Open Knowledge Maps. The goal is to generate a weighted list of search terms.

#### 1.1.2 Search Query execution
Once the search terms are identified, they can be used to run a search query in a search engine or database. The goal is to primarely focus on Google Scholar, and enhance the results by running additional queries on other tools such as Open Knowledge Maps and Connected Papers. The goal is to retrieve an extensive set of relevant documents.

### 1.2 Zotero
Zotero is a tool used to manage the retrieved documents and extract relevant information from them. The tasks involved in this step are:

#### 1.2.1 PDF search
This task involves searching for PDF versions of the retrieved documents using tools such as Zotero. This step can save time and make it easier to extract relevant information from the documents. You may need to add PDFs manually if they are not picked up, always add them to the respective entry in Zotero to avoid creating duplicate entries. Additionally, if you have to add an entire entry manually because a PDF you deemed important wasn't picked up, that might mean your search query wasn't extensive enough yet. Double-check if your search query is correct, refine it if necessary and run it again if that is the case.

#### 1.2.2 Information extraction
Once the PDFs are retrieved, this task involves extracting relevant information from them. This can include metadata like author names, publication date, abstracts and keywords, but also further details like research questions, methodology, citations and other Information like the frequency of important keywords accessible via Natural Language Processing (NLP). The goal is to create a representation of the resource with relevant information.

#### 1.2.3 Ranking
After the information is extracted, this task involves ranking the documents based on their relevance to the topic. This is done automatically via the weighted keywords from 1.1.1 and their respective frequency in the resources representations from 1.2.2. 

#### 1.2.4 Illustration
This task involves creating visual representations of the information retrieved in previous steps. This can include exporting the ranked representations to Excel or Obsidian, form clusters, graphs or other visualizations to help understand the relationships between the resources.

### 1.3 ORKG
This task involves using the Open Research Knowledge Graph (ORKG) to make the discovered work accessible to the scientific community. The findings are linked semantically and enhanced with the aid of a variety of different tools.

#### 1.3.1 Paper
First the papers need to be added, starting from the highest ranked paper. In the process of adding a paper previously extracted information can be added to the ORKG Contribution and will subsequently aid the linking process of this particualarly Survey, as well as any other subsequently conducted Reviews.

#### 1.3.2 List
The ranked list of resources available since 1.2.3 can now be represented in the ORKG as well. Each Paper added in 1.3.1 can be assigned to this List. The Researcher can decide to add them all together once he fully completed step 1.3.1 for all papers, or add each imediatly after it has passed 1.3.1. The result of 1.3.2 is an accessible ranked list to be used for this survey and any subsequently interested Researcher in this particular field. 

#### 1.3.3 Comparison
Creating comparisons from the List components is highly advised. In order of significance we propose 
1. VIP: Very Important Papers:
   A Comparison of the most important Papers, regardless of their rank, identified after 1.3.2 was fully completed. It represents the results of the survey and can be considered "The final representation of the survey's result". It is the gateway to all the knowledge relevant to the initial search query.
2. TRIP: Top Ranked Important Papers:
   A Comparison of the top 10 / Top 50 / Top 100 Papers by rank. This can be insightful to already gain an overview before creating the final VIP
3. Interesting findings:
   A Comparison of interesting Methodologies, a comparison over similar approaches with different resoults, similar research questions, usage of similar Tools - any given Comparison that comes to mind while investigating the literature at hand.
Comparisons are the most accessible artifacts of the literature review. While the List and Paper Contributions are important Artifacts to both eventually achieve the final result while building a traceble and lasting foundation for your results, they are not the most accessible representation of the knowledge the L-SEARCH reveals. With the Comparisons and respective Vizualization You enhance this knowledge to be quickly comprehended and spring new scholarly discourse and discovery.

## Phase 2: Focus Run
After the initial run, increased familiarity with the system and the topic at hand, a more focussed second run can be held.
It followes 3 goals:
1. Specify the desired resources and ranking more than the previous iteration
2. Fill gaps that previously surfaced
3. Verify Literature gaps

That's it! Happy researching!
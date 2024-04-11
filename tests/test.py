# Setup
from bnw_tools.extract.nlp import util_nlp

folder_path = "G:/Meine Ablage/SE2A-B42-Aerospace-knowledge-SWARM-SLR"
language = "en"

nlptools = util_nlp.NLPTools()


# Jump to the function definition
from bnw_tools.review.similarity import normalize

config = {
    # Used for normalize (see above)
    "log_level": False,
    # "sqrt_level": 2, # default, reduces keyword stuffing, but rewards long documents
    "sqrt_level": False,
    # Consider all entries in a research question group as one
    "merge_RQ_group_entries": True,
}

# NLP (Flair and SpaCy)
folder = util_nlp.Folder(
    folder_path, nlptools=nlptools, language=language, publish=True, config=config
)

import bibtexparser
import re


def clean(bib_path):
    with open(bib_path, encoding='UTF8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    """
    Errors:
    Entry type report not standard. Not considered.
    Entry type online not standard. Not considered.
    Entry type thesis not standard. Not considered.
    """

    def handle_int(key, value):
        try:
            value = int(value)
        except:
            pass
        return {key: value}

    def handle_str(key, value):
        return {key: value}

    def handle_file(key, value):
        result = {}
        'Full Text PDF:files/4/Sicklinger et al. - 2014 - Interface Jacobian-based Co-Simulation.pdf:application/pdf;Snapshot:files/5/nme.html:text/html'
        files = re.split(r'(?<!\\);', value)
        for file in files:
            pieces = file.split(":")
            # deciced not to include the path in YAML
            # k = "path_" + pieces[0].replace(" ", "_")
            k = pieces[0]
            v = pieces[1]
            result[k] = v
        return {key: result}

    def handle_langid(key, value):
        # might unify landid later
        'english'
        return {key: value}

    def handle_editor(key, value):
        'van Beurden, Martijn and Budko, Neil and Schilders, Wil'
        return {key: value}

    def handle_author(key, value):
        'Georg, Niklas and Lehmann, Christian and Römer, Ulrich and Schuhmann, Rolf'
        return {key: value}

    def handle_publisher(key, value):
        'Springer International Publishing'
        return {key: value}

    def handle_booktitle(key, value):
        'Scientific Computing in Electrical Engineering'
        return {key: value}

    def handle_pages(key, value):
        '127--135'
        return {key: value}

    def handle_abstract(key, value):
        'This work addresses uncertainty quantification for optical structures. We decouple the propagation of uncertainties by combining local surrogate models with a scattering matrix approach, which is then embedded into a multifidelity Monte Carlo framework. The so obtained multifidelity method provides highly efficient estimators of statistical quantities jointly using different models of different fidelity and can handle many uncertain input parameters as well as large uncertainties. We address quasi-periodic optical structures and propose the efficient construction of low-fidelity models by polynomial surrogate modeling applied to unit cells. We recall the main notions of the multifidelity algorithm and illustrate it with a split ring resonator array simulation, serving as a benchmark for the study of optical structures. The numerical tests show speedups by orders of magnitude with respect to the standard Monte Carlo method.'
        return {key: value}

    def handle_series(key, value):
        'Mathematics in Industry'
        return {key: value}

    def handle_doi(key, value):
        '10.1007/978-3-030-84238-3_13'
        return {key: value}

    def handle_isbn(key, value):
        '978-3-030-84238-3'
        return {key: value}

    def handle_title(key, value):
        'Multifidelity Uncertainty Quantification for Optical Structures'
        return {key: value}

    def handle_location(key, value):
        'Cham'
        return {key: value}

    def handle_ENTRYTYPE(key, value):
        'inproceedings'
        return {key: value}

    def handle_ID(key, value):
        'georg_multifidelity_2021'
        return {key: value}

    def default_handler(key, value):
        print(f"No handler found for key '{key}' with value '{value}'")
        return {key: value}

    handlers = {
        'file': handle_file,
        'langid': handle_langid,
        'date': handle_int,
        'editor': handle_editor,
        'author': handle_author,
        'publisher': handle_publisher,
        'booktitle': handle_booktitle,
        'pages': handle_pages,
        'abstract': handle_abstract,
        'series': handle_series,
        'doi': handle_doi,
        'isbn': handle_isbn,
        'title': handle_title,
        'location': handle_location,
        'ENTRYTYPE': handle_ENTRYTYPE,
        'ID': handle_ID,
        'url': handle_str,
        'journaltitle': handle_str,
        'volume': handle_str,
        'issn': handle_int,
        'number': handle_int,
        'rights': handle_str,
        'keywords': handle_str,
        'urldate': handle_int,
        'shorttitle': handle_int,
        'pmid': handle_int,
        'note': handle_str,
        'eprint': handle_str,
        'eprinttype': handle_str,
        'shortjournal': handle_str,
        'issue': handle_int,
        'editorbtype': handle_str,
        'editorb': handle_str,
        'eventtitle': handle_str,
        'pagetotal': handle_int,
        'pmcid': handle_int,
    }
    bib_db_clean = {}
    for entry in bib_database.entries:
        entry_dict = {}
        for key, value in entry.items():
            handler = handlers.get(key, default_handler)
            result = handler(key, value)
            for k, v in result.items():
                entry_dict[k] = v
        bib_db_clean[entry['ID']] = entry_dict
    return bib_db_clean


def get_title(record):
    try:
        return record['titles']['title']['style']['#text']
    except KeyError:
        return None

def get_abstract(record):
    try:
        return record['abstract']['style']['#text']
    except KeyError:
        return None

def get_accession_num(record):
    try:
        return record['accession-num']['style']['#text']
    except KeyError:
        return None
    
def get_journal(record):
    try:
        return record['periodical']['full-title']['style']['#text']
    except KeyError:
        return None

def get_edition(record):
    try:
        return record['edition']['style']['#text']
    except KeyError:
        return None
    
def get_year(record):
    try:
        return record['dates']['year']['style']['#text']
    except KeyError:
        return None

def get_date(record):
    try:
        return record['dates']['pub-dates']['date']['style']['#text']
    except KeyError:
        return None
    
def get_internal_pdf(record):
    try:
        tokens = record['urls']['pdf-urls']['url'].split("/")
        return tokens[len(tokens) - 1]
    except KeyError:
        return None
    except AttributeError:
        return None
    except TypeError:
        return None

def get_remote_database(record):
    try:
        return record['remote-database-name']['style']['#text']
    except KeyError:
        return None

def parse_record(record):
    """
    Parse an article record and get a dict of the article metadata
    
    Args:
        record: The record
        
    Returns:
        Dictionary of metadata
    """
    return {'abstract': get_abstract(record),
            'accession_num': get_accession_num(record),
            'date': get_date(record),
            'edition': get_edition(record),
            'internal_pdf': get_internal_pdf(record),
            'journal': get_journal(record),
            'database': get_remote_database(record),
            'title': get_title(record),
            'year': get_year(record)}





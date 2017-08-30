import xmltodict

metadata_dir = "/Users/prussell/Dropbox/github_mining/articles/article_metadata/"
pdf_dir = "/Users/prussell/Dropbox/github_mining/articles/pdfs/"

metadata_xml = ["%s/Ben_Harnke_%s_Russell.xml" % (metadata_dir, range) 
                for range in ["1-5000", "5001-10000", "10001-15000", "15001-20000", "20001-25000", "25001-28326"]]


def get_title(record):
    return record['titles']['title']['style']['#text']

def get_abstract(record):
    return record['abstract']['style']['#text']

def get_accession_num(record):
    try:
        return record['accession-num']['style']['#text']
    except KeyError:
        return None
    
def get_journal(record):
    return record['periodical']['full-title']['style']['#text']

def get_edition(record):
    try:
        return record['edition']['style']['#text']
    except KeyError:
        return None
    
def get_year(record):
    return record['dates']['year']['style']['#text']

def get_date(record):
    try:
        return record['dates']['pub-dates']['date']['style']['#text']
    except KeyError:
        return None
    
def get_internal_pdf(record):
    tokens = record['urls']['pdf-urls']['url'].split("/")
    return tokens[len(tokens) - 1]

def get_remote_database(record):
    return record['remote-database-name']['style']['#text']

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
            'remote_db': get_remote_database(record),
            'title': get_title(record),
            'year': get_year(record)}



with open(metadata_xml[0], encoding = "utf8") as reader:
    records = xmltodict.parse(reader.read())['xml']['records']['record']

for record in records[0:10]:
    print(parse_record(record))







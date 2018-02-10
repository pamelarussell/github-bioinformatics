import argparse
import os.path

from bigquery import get_client
import xmltodict

from lit_search import parse_record, gh_repo_from_text, gh_repo_from_pdf
from util import delete_bq_table, create_bq_table, push_bq_records


parser = argparse.ArgumentParser()
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
parser.add_argument('--metadata-dir', action = 'store', dest = 'metadata_dir', required = True, 
                    help = 'Directory containing article metadata XML files')
parser.add_argument('--pdf-dir', action = 'store', dest = 'pdf_dir', required = True, 
                    help = 'Directory containing article PDF files')
parser.add_argument('--bq-ds', action = 'store', dest = 'bq_ds', required = True,
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--bq-tb', action = 'store', dest = 'bq_tb', required = True,
                    help = 'BigQuery table to write to')
args = parser.parse_args()

# Article metadata and PDFs
metadata_dir = args.metadata_dir
pdf_dir = args.pdf_dir
metadata_xml = ["%s/Ben_Harnke_%s_Russell.xml" % (metadata_dir, label) 
                for label in ["1-5000", "5001-10000", "10001-15000", "15001-20000", "20001-25000", "25001-28326"]]

# Read metadata from each XML file
records = []
for metadata_group in metadata_xml:
    with open(metadata_group, encoding = "utf8") as reader:
        print("\nParsing group %s" % metadata_group)
        records += xmltodict.parse(reader.read())['xml']['records']['record']
        print("Imported %s records so far." % len(records))


# Get a GitHub repo name from a metadata dict
# Returns a dict with repos = the set of repo names and source = abstract or pdf, or None if couldn't get repo name
def gh_repos_from_metadata(metadata):
    abstract = metadata['abstract']
    gh_from_abstract = gh_repo_from_text(abstract)
    # If the abstract contains a GitHub repo, return that
    if gh_from_abstract is not None:
        return {'repos': gh_from_abstract, 'source': 'abstract'}
    else:
        # Look for a pdf
        pdf = "%s/%s" % (pdf_dir, metadata['internal_pdf'])
        if os.path.isfile(pdf):
            # Try to get GitHub repo from pdf; will be None if not applicable
            gh_from_pdf = gh_repo_from_pdf(pdf)
            if gh_from_pdf is not None:
                return {'repos': gh_from_pdf, 'source': 'pdf'}
            else:
                return None
        else:
            # Return None if there is no pdf
            return None

# Write the results to BigQuery table
# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
json_key = args.json_key
bq_ds = args.bq_ds
bq_tb = args.bq_tb
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the output table if it exists
delete_bq_table(client, bq_ds, bq_tb)

# Create the table
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'repo_source', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'title', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'journal', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'database', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'accession_num', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'year', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'date', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'edition', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'internal_pdf', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'abstract', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, bq_ds, bq_tb, schema)

# Iterate through the records and write to BQ table
print('\nExtracting GitHub repo names from articles...')
num_done = 0
num_found = 0
recs_to_push = []
for record in records:
    metadata = parse_record(record)
    repos = gh_repos_from_metadata(metadata)
    if repos is not None:
        num_found += len(repos['repos'])
        for repo in repos['repos']:
            metadata_this_repo = metadata.copy()
            metadata_this_repo['repo_name'] = repo
            metadata_this_repo['repo_source'] = repos['source']
            recs_to_push.append(metadata_this_repo)
    num_done += 1
    if num_done % 100 == 0:
        print("Analyzed %s papers. Found %s valid repo names." % (num_done, num_found))
        if recs_to_push:
            push_bq_records(client, bq_ds, bq_tb, recs_to_push)
        recs_to_push.clear()
    
# Push final batch of records
if recs_to_push:
    push_bq_records(client, bq_ds, bq_tb, recs_to_push)


print("\n\nAll done.")




import argparse
from collections import Counter
import csv
import os
import re
import subprocess
import sys

from bigquery import get_client

from google.cloud import bigquery, storage
from google.cloud.bigquery import SchemaField
from util import parse_cloc_response, delete_bq_table, create_bq_table, push_bq_records, write_file, run_query_and_save_results
from util import rec_contents_comments_stripped
from util import unique_vals


# Count lines of code in source files and store this information in a new table in BigQuery
# Use the program CLOC to count lines of code
# Also strip comments and push the stripped file contents to a new BigQuery table
# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--bucket', action = 'store', dest = 'bucket', required = True,
                    help = 'Google Cloud Storage bucket containing file contents CSV files')
parser.add_argument('--regex_csv', action = 'store', dest = 'regex_csv', required = True,
                    help = 'Regex uniquely identifying contents CSV file names in the Google Cloud Storage bucket')
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery GitHub bioinformatics project')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
parser.add_argument('--out_ds', action = 'store', dest = 'out_ds', required = True, 
                    help = 'BigQuery dataset to write to')
parser.add_argument('--tb_loc', action = 'store', dest = 'tb_loc', required = True, 
                    help = 'BigQuery table to write language and LOC results to')
parser.add_argument('--tb_sc', action = 'store', dest = 'tb_sc', required = True, 
                    help = 'BigQuery table to write comment-stripped versions of source file contents to')
parser.add_argument('--tb_skip', action = 'store', dest = 'tb_skip', required = True,
                    help = 'BigQuery table to write skipped file SHAs to')
parser.add_argument('--cloc', action = 'store', dest = 'cloc', required = True, 
                    help = 'Full path to CLOC executable')
parser.add_argument('--outfile', action = 'store', dest = 'out', required = True, 
                    help = 'Output log file')
args = parser.parse_args()

# Log file
outfile = args.out
os.makedirs(os.path.split(outfile)[0], exist_ok = True)
w = open(outfile, mode = 'x', buffering = 1)

# Temp directory to save source files in
outdir = os.path.dirname(outfile)

# Google Cloud Storage parameters
bucket_name = args.bucket
regex_csv = re.compile(args.regex_csv)

# BigQuery parameters
proj = args.proj
json_key = args.json_key
out_ds = args.out_ds
table_loc_ungrouped = "tmp_loc_ungrouped"
table_sc_ungrouped = "tmp_sc_ungrouped"
table_loc = args.tb_loc
table_sc = args.tb_sc
table_skip = args.tb_skip

# CLOC executable
cloc_exec = args.cloc

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
bq_client = get_client(json_key_file=json_key, readonly=False)

# Delete the final output tables if they exist
delete_bq_table(bq_client, out_ds, table_loc)
delete_bq_table(bq_client, out_ds, table_sc)

# Get SHAs already in ungrouped tables or skipped
existing_sha_loc = unique_vals(bq_client, proj, out_ds, table_loc_ungrouped, "sha")
existing_sha_sc = unique_vals(bq_client, proj, out_ds, table_sc_ungrouped, "sha")
if not Counter(existing_sha_loc) == Counter(existing_sha_sc):
    print("Deleting tables %s and %s because they do not contain the same SHAs. Starting over." %(table_loc_ungrouped, table_sc_ungrouped))
    delete_bq_table(bq_client, out_ds, table_loc_ungrouped)
    delete_bq_table(bq_client, out_ds, table_sc_ungrouped)
if len(existing_sha_loc) > 0:
    print("Only running CLOC for SHAs not in set of %s already analyzed" %(len(existing_sha_loc)))
existing_sha_skip = unique_vals(bq_client, proj, out_ds, table_skip, "sha")
if len(existing_sha_skip) > 0:
    print("Skipping %s files already skipped" %(len(existing_sha_skip)))

# Create the lines of code tables with schema corresponding to CLOC output
schema_loc = [
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(bq_client, out_ds, table_loc, schema_loc)
if not bq_client.check_table(out_ds, table_loc_ungrouped):
    create_bq_table(bq_client, out_ds, table_loc_ungrouped, schema_loc)

# Create the comment-stripped contents tables
schema_sc = [
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents_comments_stripped', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(bq_client, out_ds, table_sc, schema_sc)
if not bq_client.check_table(out_ds, table_sc_ungrouped):
    create_bq_table(bq_client, out_ds, table_sc_ungrouped, schema_sc)
    
# Table to keep track of skipped files
schema_skip = [{'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'}]
if not bq_client.check_table(out_ds, table_skip):
    create_bq_table(bq_client, out_ds, table_skip, schema_skip)

# File extensions that can be skipped
skip_re = re.compile(
                     '\.jpg$|\.pdf$|\.eps$|\.fa$|\.fq$|\.ps$|\.sam$' + \
                     '|\.fasta$|\.gff3$|\.vcf$|\.dat$|\.png$|\.gz$' + \
                     '|\.gitignore$|\.fai$|\.bed$' + \
                     '|\.mat$|\.zip$|\.gif$|\.svg$|\.fastq$|\.jar$|\.mp3$' + \
                     '|\.mp4$|\.class$|\.bwt$|\.bz2$|\.cram$|\.crai$|\.ppt$' + \
                     '|\.pptx$|\.RData$|\.Rhistory$|\.tgz$|\.gtf$', 
                     re.IGNORECASE)

# Identify contents file names in GCS bucket
print("\nIdentifying contents CSV files on Google Cloud Storage")
gcs_client = storage.Client.from_service_account_json(json_key)
bucket = gcs_client.get_bucket(bucket_name)
blobs = bucket.list_blobs()
contents_blobs = [blob for blob in blobs if regex_csv.match(blob.name)]
print("Found %s blobs matching regex: %s" %(len(contents_blobs), regex_csv.pattern))
# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

num_done = 0
num_skipped_already_done = 0
num_skipped_no_result = 0
num_skipped_empty_content = 0
num_skipped_file_extension = 0
num_skipped_skipped = 0
num_success = 0

# Run CLOC on each file and add results to database tables
for contents_blob in contents_blobs:
    
    contents_csv = "/%s/%s" % (outdir, contents_blob.name)
    print("\nDownloading GCS blob %s to local file %s due to record size issues" % (contents_blob.name, contents_csv))
    contents_blob.download_to_filename(contents_csv)
    
    print("Reading file contents and running CLOC on each file...")
    
    with open(contents_csv) as csvfile:
        
        reader = csv.DictReader(x.replace('\0', '') for x in csvfile)
        recs_to_add_loc = []
        recs_to_add_sc = []
        skipped_sha = []
          
        for rec in reader:
              
            if num_done % 1000 == 0:
                print('Finished %s files. Got results for %s. Skipped %s already done, %s previously skipped, %s with empty content, %s with invalid file extension, and %s with no CLOC result.' 
                      % (num_done, num_success, num_skipped_already_done, num_skipped_skipped, 
                         num_skipped_empty_content, num_skipped_file_extension, num_skipped_no_result))
              
            # Push batch of records
            if num_done % 10 == 0:
                if len(recs_to_add_loc) > 0:
                    push_bq_records(bq_client, out_ds, table_loc_ungrouped, recs_to_add_loc)
                    push_bq_records(bq_client, out_ds, table_sc_ungrouped, recs_to_add_sc)
                if len(skipped_sha) > 0:
                    push_bq_records(bq_client, out_ds, table_skip, [{'sha': sha} for sha in skipped_sha])
                recs_to_add_loc.clear()
                recs_to_add_sc.clear()
                skipped_sha.clear()
          
            num_done = num_done + 1
          
            repo = rec["repo_name"]
            filename = rec["file_name"]
            path = rec["path"]
            sha = rec["sha"]
            content_str = rec["contents"]
          
            # Process the record
            if sha in existing_sha_skip:
                num_skipped_skipped = num_skipped_skipped + 1
                w.write('%s. %s/%s - skipping - previously skipped\n' % (num_done, repo, path))
                continue
            if sha in existing_sha_loc:
                num_skipped_already_done = num_skipped_already_done + 1
                w.write('%s. %s/%s - skipping - already done\n' % (num_done, repo, path))
                continue
            if content_str is None:
                num_skipped_empty_content = num_skipped_empty_content + 1
                skipped_sha.append(sha)
                w.write('%s. %s/%s - skipping - content is empty\n' % (num_done, repo, path))
                continue
            if skip_re.search(filename):
                num_skipped_file_extension = num_skipped_file_extension + 1
                skipped_sha.append(sha)
                w.write('%s. %s/%s - skipping - file extension\n' % (num_done, repo, path))
                continue
            # Write the file contents to disk
            destfile_content = '/%s/%s' % (outdir, re.sub(r'[\^\-\]\\`~!@#$%&*()=+[{}|;:,<>/?]', '_', path))
            ext_sc = 'comments_stripped'
            destfile_sc = '%s.%s' % (destfile_content, ext_sc)
            content = write_file(content_str, destfile_content)
            # Run CLOC
            cloc_result = subprocess.check_output([cloc_exec, '--strip-comments=%s' % ext_sc, '--original-dir', content]).decode('utf-8')
            os.remove(content)
            cloc_data = parse_cloc_response(cloc_result)
            if cloc_data is not None:
                num_success = num_success + 1
                cloc_data['sha'] = sha
                recs_to_add_loc.append(cloc_data)
                recs_to_add_sc.append(rec_contents_comments_stripped(sha, destfile_sc))
                os.remove(destfile_sc)
                w.write('%s. %s/%s - success\n' % (num_done, repo, path))
            else:
                num_skipped_no_result = num_skipped_no_result + 1
                skipped_sha.append(sha)
                w.write('%s. %s/%s - no CLOC result\n' % (num_done, repo, path))

        # Push final batch of records
        if len(recs_to_add_loc) > 0:
            push_bq_records(bq_client, out_ds, table_loc_ungrouped, recs_to_add_loc)
            push_bq_records(bq_client, out_ds, table_sc_ungrouped, recs_to_add_sc)
        if len(skipped_sha) > 0:
            push_bq_records(bq_client, out_ds, table_skip, [{'sha': sha for sha in skipped_sha}])

        # Delete the temporary CSV file
        print("Deleting temporary file %s" % contents_csv)
        os.remove(contents_csv)

# Group the tables to dedup records and write to final tables
query_group_loc = """
SELECT
  *
FROM (
  SELECT
    *
  FROM
    [%s:%s.%s]
  GROUP BY
    sha,
    language,
    blank,
    comment,
    code)
WHERE
  sha IN (
  SELECT
    sha
  FROM (
    SELECT
      *
    FROM
      [%s:%s.%s]
    GROUP BY
      sha,
      language,
      blank,
      comment,
      code)
  GROUP BY
    sha
  HAVING
    COUNT(sha) = 1)
""" % (proj, out_ds, table_loc_ungrouped, proj, out_ds, table_loc_ungrouped)
  
    
query_group_sc = """
SELECT
  *
FROM (
  SELECT
    *
  FROM
    [%s:%s.%s]
  GROUP BY
    sha,
    contents_comments_stripped)
WHERE
  sha IN (
  SELECT
    sha
  FROM (
    SELECT
      *
    FROM
      [%s:%s.%s]
    GROUP BY
      sha,
      contents_comments_stripped)
  GROUP BY
    sha
  HAVING
    COUNT(sha) = 1)
""" % (proj, out_ds, table_sc_ungrouped, proj, out_ds, table_sc_ungrouped)
  
run_query_and_save_results(bq_client, query_group_loc, out_ds, table_loc, 300)
run_query_and_save_results(bq_client, query_group_sc, out_ds, table_sc, 300)
      
# Delete the temporary tables
#delete_bq_table(bq_client, out_ds, table_loc_ungrouped)
#delete_bq_table(bq_client, out_ds, table_sc_ungrouped)

print('\nAll done: %s.\n\n' % os.path.basename(__file__))
w.close()





#!/usr/bin/perl

use strict;
use warnings;
use File::Slurp;
use JSON;


# -----------------------------------------------------------------
#                    Pipeline configuration
# -----------------------------------------------------------------

# Key names for config file
my $key_gh_user = "gh_username";
my $key_gh_oauth_key = "gh_oauth_key";
my $key_json_key_google = "json_key";
my $key_bq_proj = "bq_proj";
my $key_gsheet_repos = "gsheet_repos";
my $key_gcs_bucket = "gcs_bucket";
my $key_python3 = "python3";
my $key_cloc_exec = "cloc";
my $key_src_dir = "src_dir";
my $key_out_results_dir = "out_results_dir";
my $key_lit_search_metadata_dir = "lit_search_metadata_dir";
my $key_lit_search_pdf_dir = "lit_search_pdf_dir";
my $key_genderize_key_file = "genderize_key_file";
my $key_extract_repos_from_lit_search = "extract_repos_from_lit_search";
my $key_check_repo_existence = "check_repo_existence";
my $key_query_eutils_article_metadata = "query_eutils_article_metadata";
my $key_generate_language_bytes = "generate_language_bytes";
my $key_generate_licenses = "generate_licenses";
my $key_generate_commits = "generate_commits";
my $key_generate_file_info = "generate_file_info";
my $key_generate_file_contents = "generate_file_contents";
my $key_generate_file_init_commits = "generate_file_init_commits";
my $key_generate_repo_metrics = "generate_repo_metrics";
my $key_generate_pr_data = "generate_pr_data";
my $key_run_cloc = "run_cloc";
my $key_run_bq_analysis_queries = "run_bq_analysis_queries";
my $key_run_extract_comments = "run_extract_comments";
my $key_run_code_chunk_frequency = "run_code_chunk_frequency";
my $key_infer_gender = "infer_gender";


# Help message
my $help_str = 	"\n--------------------------------------------------------\n\n" .
				"Usage: github_bioinformatics_pipeline.pl <config.json>\n" .
				"\n" .
				"Config file is JSON with top-level keys:\n" .
				"\n" .
				"* GitHub API configuration *\n" .
				"\n" .
				"'$key_gh_user': GitHub username\n" .
				"'$key_gh_oauth_key': GitHub Oauth key\n" .
				"\n" .
				"* Google configuration *\n" .
				"\n" .
				"'$key_json_key_google': File with JSON key for Google credentials\n" .
				"'$key_bq_proj': Name of BigQuery project\n" .
				"'$key_gsheet_repos': Name of Google Sheet with curated article and repo info\n" .
				"'$key_gcs_bucket': Name of Google Cloud Storage bucket for project data\n" .
				"\n" .
				"* Local structure *\n" .
				"\n" .
				"'$key_src_dir': Source code directory\n" .
				"'$key_out_results_dir': Directory to save some results in\n" .
				"'$key_lit_search_metadata_dir': Directory with XML metadata from lit search\n" .
				"'$key_lit_search_pdf_dir': Directory containing PDF articles from lit search\n" .
				"'$key_genderize_key_file': File containing single line with genderize.io API key\n" .
				"\n" .
				"* Executables *\n" .
				"\n" .
				"'$key_python3': Python 3 executable\n" .
				"'$key_cloc_exec': CLOC executable\n" .
				"\n" .
				"* Workflow steps *\n" .
				"\n" .
				"'$key_extract_repos_from_lit_search': (true/false) Extract GitHub repo names from literature search\n" .
				"'$key_check_repo_existence': (true/false) Check for issues with repository names that have been manually curated\n" .
				"'$key_query_eutils_article_metadata: (true/false) Query Eutils for article metadata'\n" .
				"'$key_generate_language_bytes: (true/false) Get amount of code per language from GitHub API'\n" .
				"'$key_generate_licenses': (true/false) Get licenses from GitHub API\n" .
				"'$key_generate_commits': (true/false) Get commit records from GitHub API\n" .
				"'$key_generate_file_info': (true/false) Get file metadata from GitHub API\n" .
				"'$key_generate_file_contents': (true/false) Get file contents from GitHub API\n" .
				"'$key_generate_file_init_commits': (true/false) Get file initial commit times from GitHub API\n" .
				"'$key_generate_repo_metrics': (true/false) Get repo-level metrics from GitHub API\n" .
				"'$key_generate_pr_data': (true/false) Get pull request records from GitHub API\n" .
				"'$key_run_cloc': (true/false) Count lines of code, identify language, and strip comments for each source file\n" .
				"'$key_run_bq_analysis_queries': (true/false) Run analysis queries and save results to tables\n" .
				"'$key_run_extract_comments': (true/false) Extract comments from source files and push to table\n" .
				"'$key_run_code_chunk_frequency': (true/false) Analyze frequency of code chunks\n" .
				"'$key_infer_gender': (true/false) Infer gender for project contributors\n" .
				"\n--------------------------------------------------------\n\n";


my $json_config = $ARGV[0] or die_with_message("Missing argument: config file");

# Read the JSON config file
my $json_config_content = read_file($json_config) or die_with_message("Couldn't read config file");
my $config_scalar = decode_json($json_config_content) or die_with_message("Malformed config file");
my %config = %$config_scalar or die_with_message("Malformed config file");

# Check for required keys
my @required_keys = ($key_bq_proj, $key_gsheet_repos, $key_gcs_bucket, $key_python3, $key_cloc_exec, $key_src_dir,
	$key_out_results_dir, $key_lit_search_metadata_dir, $key_lit_search_pdf_dir, $key_genderize_key_file,
	$key_extract_repos_from_lit_search, $key_check_repo_existence, $key_query_eutils_article_metadata, $key_json_key_google,
	$key_generate_language_bytes, $key_generate_licenses, $key_generate_commits, $key_generate_file_info,
	$key_generate_file_contents, $key_generate_file_init_commits, $key_generate_repo_metrics, $key_generate_pr_data,
	$key_run_cloc, $key_run_bq_analysis_queries, $key_run_extract_comments, $key_run_code_chunk_frequency, $key_infer_gender,
	$key_gh_user, $key_gh_oauth_key);
foreach my $key (@required_keys) {if(!exists $config{$key}) {die_with_message("Missing key: $key")}}

# Get parameters from config
my $gh_user = $config{$key_gh_user};
my $gh_oauth_key = $config{$key_gh_oauth_key};
my $json_key = $config{$key_json_key_google};
my $bq_proj = $config{$key_bq_proj};
my $gsheet_repos = $config{$key_gsheet_repos};
my $gcs_bucket = $config{$key_gcs_bucket};
my $python3 = $config{$key_python3};
my $cloc_exec = $config{$key_cloc_exec};
my $src_dir = $config{$key_src_dir};
my $out_results_dir = $config{$key_out_results_dir};
my $lit_search_metadata_dir = $config{$key_lit_search_metadata_dir};
my $lit_search_pdf_dir = $config{$key_lit_search_pdf_dir};
my $genderize_key_file = $config{$key_genderize_key_file};
my $extract_repos_from_lit_search = $config{$key_extract_repos_from_lit_search};
my $check_repo_existence = $config{$key_check_repo_existence};
my $query_eutils_article_metadata = $config{$key_query_eutils_article_metadata};
my $generate_language_bytes = $config{$key_generate_language_bytes};
my $generate_licenses = $config{$key_generate_licenses};
my $generate_commits = $config{$key_generate_commits};
my $generate_file_info = $config{$key_generate_file_info};
my $generate_file_contents = $config{$key_generate_file_contents};
my $generate_file_init_commits = $config{$key_generate_file_init_commits};
my $generate_repo_metrics = $config{$key_generate_repo_metrics};
my $generate_pr_data = $config{$key_generate_pr_data};
my $run_cloc = $config{$key_run_cloc};
my $run_bq_analysis_queries = $config{$key_run_bq_analysis_queries};
my $run_extract_comments = $config{$key_run_extract_comments};
my $run_code_chunk_frequency = $config{$key_run_code_chunk_frequency};
my $infer_gender = $config{$key_infer_gender};


# -----------------------------------------------------------------
#                   BigQuery project structure
# -----------------------------------------------------------------

# Datasets
my $bq_ds_repos = "repos";
my $bq_ds_analysis_results = "analysis";
my $bq_ds_lit_search = "lit_search";
# Data tables with data pulled from GitHub API
my $bq_tb_repo_metrics = "repo_metrics";
my $bq_tb_commits = "commits";
my $bq_tb_contents = "contents";
my $bq_tb_files = "file_info";
my $bq_tb_file_init_commit = "file_init_commit";
my $bq_tb_languages_gh_api = "languages_gh_api";
my $bq_tb_licenses = "licenses";
my $bq_tb_prs = "pull_requests";
# Analysis tables
my $bq_tb_lang_bytes_by_repo = "language_bytes_by_repo"; # Total bytes of code per language per repo
my $bq_tb_bytes_by_language = "bytes_by_language"; # Total bytes of code per language across all repos
my $bq_tb_lang_list_by_repo = "language_list_by_repo"; # List of languages used by repo
my $bq_tb_num_langs_by_repo = "num_langs_by_repo"; # Number of languages used by repo
my $bq_tb_num_repos_by_lang = "num_repos_by_lang"; # Number of repos using each language
my $bq_tb_repo_article = "repo_and_article_incl_non_bioinf"; # Repo names and articles they're mentioned in, including non-bioinformatics
my $bq_tb_repo_article_curated = "repo_and_article_curated"; # Repo names and articles they're mentioned in
my $bq_tb_eutils = "article_metadata_eutils"; # Article metadata from Eutils
my $bq_tb_loc_by_file = "lines_of_code_by_file"; # Computed table with language and lines of code per source file
my $bq_tb_loc_by_file_skipped = "lines_of_code_by_file_skipped"; # Files skipped in lines of code analysis
my $bq_tb_loc_by_repo = "lines_of_code_by_repo"; # Computed table with total lines of code by repo
my $bq_tb_contents_comments_stripped = "contents_comments_stripped"; # Computed table with language and lines of code per source file
my $bq_tb_comments = "comments"; # Computed table with comments extracted from source files
my $bq_tb_code_chunk_freq = "code_chunk_freq"; # Frequency of groups of lines of code
my $bq_tb_test_cases = "test_cases"; # Test cases
my $bq_tb_test_cases_by_repo = "test_cases_by_repo"; # Test cases by repo
my $bq_tb_commit_types = "commit_types"; # Commit types
my $bq_tb_project_duration = "project_duration"; # Project duration
my $bq_tb_gender = "gender_by_name"; # Inferred gender of project contributors


# -----------------------------------------------------------------
#                    Local project structure
# -----------------------------------------------------------------

# Source directories
my $src_dir_R = "$src_dir/R/";
my $src_dir_python = "$src_dir/python/";

# Programs
my $script_check_repo_existence = "$src_dir_python/check_repo_existence.py";
my $script_article_metadata_eutils = "$src_dir_R/ncbi/paper_metadata_eutils.R";
my $script_extract_repos_from_lit_search = "$src_dir_python/extract_repos_from_articles.py";
my $script_gh_api_repo_metrics = "$src_dir_python/gh_api_repo_metrics.py";
my $script_gh_api_languages = "$src_dir_python/gh_api_languages.py";
my $script_gh_api_licenses = "$src_dir_python/gh_api_licenses.py";
my $script_gh_api_commits = "$src_dir_python/gh_api_commits.py";
my $script_gh_api_file_info = "$src_dir_python/gh_api_file_info.py";
my $script_gh_api_file_contents = "$src_dir_python/gh_api_file_contents.py";
my $script_gh_api_pr_data = "$src_dir_python/gh_api_pr_data.py";
my $script_cloc = "$src_dir_python/cloc_and_strip_comments.py";
my $script_run_bq_queries_analysis = "$src_dir_python/run_bq_queries_analysis.py";
my $script_extract_comments = "$src_dir_python/extract_comments.py";
my $script_code_chunk_frequency = "$src_dir_python/code_chunk_frequency.py";
my $script_gh_api_file_init_commit = "$src_dir_python/gh_api_file_init_commit.py";
my $script_infer_gender = "$src_dir_R/gender/infer_gender.R";

# Output directories
my $out_results_dir_cloc = "$out_results_dir/cloc/";


# -----------------------------------------------------------------
#                        Other parameters
# -----------------------------------------------------------------

my $gcs_regex_csv = "contents-[0-9]+\.csv";
my $languages_to_skip = "XML,HTML,JSON,YAML";


# -----------------------------------------------------------------
#                     Run parts of the workflow
# -----------------------------------------------------------------

# Extract GitHub repo names from literature search - includes non-bioinformatics repos
if($extract_repos_from_lit_search) {
	run_cmmd("$python3 $script_extract_repos_from_lit_search --metadata-dir $lit_search_metadata_dir ".
	"--pdf-dir $lit_search_pdf_dir --bq-ds $bq_ds_lit_search --bq-tb $bq_tb_repo_article")
} else {print("\nSkipping step: extract repo names from literature search\n")}

# Check for issues with repository names that have been manually curated
if($check_repo_existence) {
	run_cmmd("$python3 $script_check_repo_existence --sheet $gsheet_repos --json_key $json_key " .
	"--gh_user $gh_user --gh_oauth_key $gh_oauth_key");
} else {print("\nSkipping step: check for repo existence\n")}

# Get article metadata from Eutils
if($query_eutils_article_metadata) {
	run_cmmd("Rscript $script_article_metadata_eutils --project $bq_proj --dataset $bq_ds_lit_search --in_table " .
	"$bq_tb_repo_article_curated --out_table $bq_tb_eutils")
} else {print("\nSkipping step: get article metadata from Eutils\n")}

# Get repo metrics from GitHub API
if($generate_repo_metrics) {
	run_cmmd("$python3 $script_gh_api_repo_metrics --ds $bq_ds_repos --table $bq_tb_repo_metrics ".
	"--sheet $gsheet_repos --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get repo info from GitHub API\n")}

# Get language info from GitHub API
if($generate_language_bytes) {
	run_cmmd("$python3 $script_gh_api_languages --ds $bq_ds_repos --table $bq_tb_languages_gh_api ".
	"--sheet $gsheet_repos --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get language info from GitHub API\n")}

# Get licenses from GitHub API
if($generate_licenses) {
	run_cmmd("$python3 $script_gh_api_licenses --ds $bq_ds_repos --table $bq_tb_licenses ".
	"--sheet $gsheet_repos --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get licenses from GitHub API\n")}

# Get commits from GitHub API
if($generate_commits) {
	run_cmmd("$python3 $script_gh_api_commits --ds $bq_ds_repos --table $bq_tb_commits ".
	"--sheet $gsheet_repos --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get commits from GitHub API\n")}

# Get file info from GitHub API
if($generate_file_info) {
	run_cmmd("$python3 $script_gh_api_file_info --ds $bq_ds_repos --table $bq_tb_files ".
	"--sheet $gsheet_repos --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get file info from GitHub API\n")}

# Get file contents from GitHub API
if($generate_file_contents) {
	run_cmmd("$python3 $script_gh_api_file_contents --ds $bq_ds_repos --table_file_contents $bq_tb_contents ".
	"--table_file_info $bq_tb_files --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get file contents from GitHub API\n")}

# Get file initial commit times from GitHub API
if($generate_file_init_commits) {
	run_cmmd("$python3 $script_gh_api_file_init_commit --ds $bq_ds_repos --table_init_commit $bq_tb_file_init_commit ".
	"--table_file_info $bq_tb_files --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get file initial commits from GitHub API\n")}

# Get pull request info from GitHub API
if($generate_pr_data) {
	run_cmmd("$python3 $script_gh_api_pr_data --ds $bq_ds_repos --table $bq_tb_prs ".
	"--sheet $gsheet_repos --proj $bq_proj --json_key $json_key --gh_user $gh_user --gh_oauth_key $gh_oauth_key")
} else {print("\nSkipping step: get pull request info from GitHub API\n")}

# Run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables
if($run_bq_analysis_queries) {
	run_cmmd("$python3 $script_run_bq_queries_analysis " .
	"--proj $bq_proj " .
	"--github_api_ds $bq_ds_repos " .
	"--analysis_ds $bq_ds_analysis_results " .
	"--results_ds $bq_ds_analysis_results " .
	"--tb_commits $bq_tb_commits " .
	"--tb_files $bq_tb_files " .
	"--tb_languages $bq_tb_lang_bytes_by_repo " .
	"--tb_loc_file $bq_tb_loc_by_file " .
	"--tb_loc_repo $bq_tb_loc_by_repo " .
	"--tb_bytes_by_language $bq_tb_bytes_by_language " .
	"--tb_lang_list_by_repo $bq_tb_lang_list_by_repo " .
	"--tb_num_langs_by_repo $bq_tb_num_langs_by_repo " .
	"--tb_num_repos_by_lang $bq_tb_num_repos_by_lang " .
	"--tb_test_cases $bq_tb_test_cases " .
	"--tb_test_cases_by_repo $bq_tb_test_cases_by_repo " .
	"--tb_project_duration $bq_tb_project_duration " .
	"--json_key $json_key")
} else {print("\nSkipping step: run BigQuery analysis queries against GitHub bioinformatics dataset and " .
	"save results to tables\n")}

# Count lines of code and push to BigQuery table along with comment-stripped versions of source files
if($run_cloc) {
	my $out_log_cloc = "$out_results_dir_cloc/run.out";
	my $cmmd_cloc = "$python3 $script_cloc " .
	"--bucket $gcs_bucket " .
	"--regex_csv $gcs_regex_csv " .
	"--proj $bq_proj " .
	"--out_ds $bq_ds_analysis_results " .
	"--tb_loc $bq_tb_loc_by_file " .
	"--tb_sc $bq_tb_contents_comments_stripped " .
	"--tb_skip $bq_tb_loc_by_file_skipped " .
	"--outfile $out_log_cloc " .
	"--cloc $cloc_exec " .
	"--json_key $json_key";
	run_cmmd($cmmd_cloc, $out_log_cloc)
} else {print("\nSkipping step: count lines of code\n")}

# Extract comments from source files and push to BigQuery table
if($run_extract_comments) {
	my $cmmd_extract_comments = "$python3 $script_extract_comments --proj_bioinf $bq_proj --tb_contents $bq_tb_contents " .
	"--tb_loc $bq_tb_loc_by_file --ds_gh $bq_ds_repos --ds_loc " .
	"$bq_ds_analysis_results --out_ds $bq_ds_analysis_results --table $bq_tb_comments";
	run_cmmd($cmmd_extract_comments)
} else {print("\nSkipping step: extract comments\n")}

# Analyze frequency of code chunks
if($run_code_chunk_frequency) {
	my $cmmd_code_chunk_freq = "$python3 $script_code_chunk_frequency --proj_bioinf $bq_proj --ds_gh $bq_ds_repos " .
	"--ds_res $bq_ds_analysis_results --table_files $bq_tb_files --table_sc $bq_tb_contents_comments_stripped " .
	"--table_out $bq_tb_code_chunk_freq --table_loc $bq_tb_loc_by_file --langs_skip $languages_to_skip";
	run_cmmd($cmmd_code_chunk_freq);
} else {print("\nSkipping step: analyze code chunk frequency\n")}

# Analyze frequency of code chunks
if($infer_gender) {
	my $genderize_api_key = read_file($genderize_key_file);
	my $cmmd_infer_gender = "Rscript $script_infer_gender --project $bq_proj " .
	"--repo_ds $bq_ds_repos --commits $bq_tb_commits --out_ds $bq_ds_analysis_results --articles $bq_tb_eutils " .
	"--gender_table $bq_tb_gender --lit_search_ds $bq_ds_lit_search --key $genderize_api_key";
	run_cmmd($cmmd_infer_gender);
} else {print("\nSkipping step: analyze code chunk frequency\n")}


print("\n\nAll done: $0.\n\n");


# -----------------------------------------------------------------
#                          Subroutines
# -----------------------------------------------------------------

# Run a command and delete a previous version of the output if it exists
# Args:
#   1. The command
#   2. (Optional parameter) The output file to delete before running the command 
sub run_cmmd {
	my ($cmmd, $output) = @_;
	$output //= 0;
	print("\nRunning command: $cmmd\n");
	# Delete the previous version of the output file if it exists
	if($output && -e $output) {
		system("rm", $output);
		if( $? != 0 ) {die "Could not remove previous output file $output\n";}
		print("Deleted previous output file $output\n");
	}
	system($cmmd);
	if ( $? != 0 ) {die;}
}


# Die with helpful message
# Args:
#	1. Short detail message to add to larger template
sub die_with_message {
	my $mssg = shift;
	die("\n\n********** $mssg **********\n\n$help_str");
}




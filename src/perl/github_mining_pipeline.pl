use strict;
use warnings;

# AUTHENTICATION NOTE:
# For this script to work in batch mode, there must be the '.httr-oauth' file in the working directory


# ********************************************************************************************************
# ********************************************   PARAMETERS   ********************************************
# ********************************************************************************************************


# -----------------------------------------------------------------
#                    Choose steps to run 
# -----------------------------------------------------------------

# Regenerate GitHub bioinformatics dataset
# $$$ Expensive! $$$
my $generate_gh_bioinf_dataset = 0;

# Use NCBI API to generate and upload table of article data
my $generate_article_info_table = 0;

# Run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables
my $run_bq_analysis_queries = 0;

# Count lines of code and push to BigQuery table along with comment-stripped versions of source files
my $run_cloc = 0;

# Extract comments from source files and push to BigQuery table
my $run_extract_comments = 0;

# Analyze frequency of code chunks
my $run_code_chunk_frequency = 1;


# -----------------------------------------------------------------
#                   BigQuery project structure
# -----------------------------------------------------------------

# Project
my $bq_proj = "github-bioinformatics-157418";

# Datasets
my $bq_ds = "test_repos";
my $bq_ds_analysis_results = "test_repos_analysis_results";

# Tables
my $bq_tb_articles = "articles_by_repo"; # NCBI article metadata
my $bq_tb_lines_of_code_by_file = "lines_of_code_by_file"; # Computed table with language and lines of code per source file
my $bq_tb_contents_comments_stripped = "contents_comments_stripped"; # Computed table with language and lines of code per source file
my $bq_tb_comments = "source_code_comments"; # Computed table with comments extracted from source files
my $bq_tb_languages = "languages"; # Languages table extracted from similar table in public GitHub dataset
my $bq_tb_code_chunk_frequency_by_repo = "code_chunk_freq_by_repo"; # Frequency of groups of lines of code
my $bq_tb_files = "files"; # File metadata


# -----------------------------------------------------------------
#                    Local project structure
# -----------------------------------------------------------------

# Source directories
my $src_dir = "/Users/prussell/Documents/Github_mining/src/";
my $src_dir_R = "$src_dir/R/";
my $src_dir_python = "$src_dir/python/";

# Programs
my $script_generate_article_info_table = "$src_dir_R/ncbi/paper_metadata.R";
my $script_cloc = "$src_dir_python/cloc_and_strip_comments.py";
my $script_run_bq_queries_dataset_creation = "$src_dir_python/run_bq_queries_dataset_creation.py";
my $script_run_bq_queries_analysis = "$src_dir_python/run_bq_queries_analysis.py";
my $script_extract_comments = "$src_dir_python/extract_comments.py";
my $script_code_chunk_frequency = "$src_dir_python/code_chunk_frequency.py";

# Output directories
my $out_results_dir = "/Users/prussell/Documents/Github_mining/results/";
my $out_results_dir_cloc = "$out_results_dir/cloc/";

# GitHub repo names
my $repo_names_list = "/Users/prussell/Documents/Github_mining/repos/repos.txt";


# -----------------------------------------------------------------
#                        External tools
# -----------------------------------------------------------------

my $python3 = "/Library/Frameworks/Python.framework/Versions/3.6/bin/python3";
my $cloc_exec = "/Users/prussell/Software/cloc-1.72.pl";



# ********************************************************************************************************
# ***********************************   NO PARAMETERS BEYOND THIS POINT   ********************************
# ********************************************************************************************************


# -----------------------------------------------------------------
#                       Run the analyses
# -----------------------------------------------------------------

# Regenerate GitHub bioinformatics dataset
if($generate_gh_bioinf_dataset) {
	run_cmmd("$python3 $script_run_bq_queries_dataset_creation --repos $repo_names_list --results_ds $bq_ds")
} else {print("\nSkipping step: regenerate GitHub bioinformatics dataset\n")}

# Generate table of article info from NCBI
if($generate_article_info_table) {
	run_cmmd("Rscript $script_generate_article_info_table -p $bq_proj -d $bq_ds -t $bq_tb_articles ".
	"-r $repo_names_list")
} else {print("\nSkipping step: generate and upload table of article data\n")}

# Run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables
if($run_bq_analysis_queries) {
	run_cmmd("$python3 $script_run_bq_queries_analysis --github_ds $bq_ds --results_ds $bq_ds_analysis_results")
} else {print("\nSkipping step: run BigQuery analysis queries against GitHub bioinformatics dataset and " .
	"save results to tables\n")}

# Count lines of code and push to BigQuery table along with comment-stripped versions of source files
if($run_cloc) {
	my $out_log_cloc = "$out_results_dir_cloc/run.out";
	my $cmmd_cloc = "$python3 $script_cloc --in_ds $bq_ds " .
	"--out_ds $bq_ds_analysis_results --table_loc $bq_tb_lines_of_code_by_file " .
	"--table_sc $bq_tb_contents_comments_stripped " .
	"--outfile $out_log_cloc --cloc $cloc_exec";
	run_cmmd($cmmd_cloc, $out_log_cloc)
} else {print("\nSkipping step: count lines of code\n")}

# Extract comments from source files and push to BigQuery table
if($run_extract_comments) {
	my $cmmd_extract_comments = "$python3 $script_extract_comments --ds_gh $bq_ds --ds_loc " .
	"$bq_ds_analysis_results --out_ds $bq_ds_analysis_results --table $bq_tb_comments";
	run_cmmd($cmmd_extract_comments)
} else {print("\nSkipping step: extract comments\n")}

# Analyze frequency of code chunks
if($run_code_chunk_frequency) {
	my $cmmd_code_chunk_freq = "$python3 $script_code_chunk_frequency --ds_gh $bq_ds --ds_res $bq_ds_analysis_results ".
	"--table_files $bq_tb_files --table_sc $bq_tb_contents_comments_stripped --table_out $bq_tb_code_chunk_frequency_by_repo";
	run_cmmd($cmmd_code_chunk_freq);
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
















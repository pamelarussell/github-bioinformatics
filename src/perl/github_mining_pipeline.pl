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

# Run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables
my $run_bq_analysis_queries = 0;

# Plot total size of source files by language
my $run_bytes_by_lang = 0;

# Plot number of repos by language
my $run_repos_by_lang = 0;

# Plot number of repos by language pair
my $run_repos_by_lang_pair = 0;

# Plot number of forks by repo
my $run_forks_by_repo = 0;

# Plot number of occurrences of "TODO: fix" by repo
my $run_todo_fix_by_repo = 0;

# Count lines of code and push to BigQuery table
my $run_count_lines_of_code = 0;

# Extract comments from source files and push to BigQuery table
my $run_extract_comments = 1;


# -----------------------------------------------------------------
#                   BigQuery project structure
# -----------------------------------------------------------------

# Project
my $bq_proj = "github-bioinformatics-157418";

# Datasets
my $bq_ds = "test_repos";
my $bq_ds_analysis_results = "test_repos_analysis_results";

# Tables
my $bq_tb_bytes_by_lang = "bytes_by_language"; # Number of bytes of code by language
my $bq_tb_forks_by_repo = "num_forks_by_repo"; # Number of forks by repo
my $bq_tb_repos_by_lang = "num_repos_by_language"; # Number of repos by language
my $bq_tb_langs_by_repo = "language_list_by_repo"; # List of languages by repo
my $bq_tb_todo_fix_by_repo = "num_todo_fix_by_repo"; # Number of occurrences of "TODO: fix" by repo
my $bq_tb_lines_of_code = "lines_of_code"; # Computed table with language and lines of code per source file
my $bq_tb_comments = "comments"; # Computed table with comments extracted from source files


# -----------------------------------------------------------------
#                    Local project structure
# -----------------------------------------------------------------

# Source directories
my $src_dir = "/Users/prussell/Documents/Github_mining/src/";
my $src_dir_R = "$src_dir/R/";
my $src_dir_python = "$src_dir/python/";

# Programs
my $script_plot_bytes_by_lang = "$src_dir_R/bytes_by_language.R";
my $script_plot_repos_by_lang = "$src_dir_R/repos_by_language.R";
my $script_plot_repos_by_lang_pair = "$src_dir_R/repos_by_language_pair.R";
my $script_plot_forks_by_repo = "$src_dir_R/forks_by_repo.R";
my $script_plot_todo_fix_by_repo = "$src_dir_R/todo_fix_by_repo.R";
my $script_count_lines_of_code = "$src_dir_python/count_lines_of_code.py";
my $script_run_bq_queries_dataset_creation = "$src_dir_python/run_bq_queries_dataset_creation.py";
my $script_run_bq_queries_analysis = "$src_dir_python/run_bq_queries_analysis.py";
my $script_extract_comments = "$src_dir_python/extract_comments.py";

# Output directories
my $out_plots_dir = "/Users/prussell/Documents/Github_mining/plots/test_repos/";
my $out_results_dir = "/Users/prussell/Documents/Github_mining/results/";
my $out_results_dir_lines_of_code = "$out_results_dir/lines_of_code/";

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

# Run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables
if($run_bq_analysis_queries) {
	run_cmmd("$python3 $script_run_bq_queries_analysis --github_ds $bq_ds --results_ds $bq_ds_analysis_results")
} else {print("\nSkipping step: run BigQuery analysis queries against GitHub bioinformatics dataset and save results to tables\n")}

# Plot total size of source files by language
if($run_bytes_by_lang) {
	my $out_pdf_bytes_by_lang = "$out_plots_dir/bytes_by_language.pdf";
	run_cmmd("Rscript $script_plot_bytes_by_lang -p $bq_proj -d $bq_ds_analysis_results -t $bq_tb_bytes_by_lang -o $out_pdf_bytes_by_lang", $out_pdf_bytes_by_lang);
} else {print("\nSkipping step: plot number of bytes by language\n")}

# Plot number of repos by language
if($run_repos_by_lang) {
	my $out_pdf_repos_by_lang = "$out_plots_dir/repos_by_language.pdf";
	run_cmmd("Rscript $script_plot_repos_by_lang -p $bq_proj -d $bq_ds_analysis_results -c $bq_tb_repos_by_lang -l $bq_tb_langs_by_repo -o $out_pdf_repos_by_lang", $out_pdf_repos_by_lang);
} else {print("\nSkipping step: plot number of repos by language\n")}
	

# Plot number of repos by language pair
if($run_repos_by_lang_pair) {
	my $out_pdf_repos_by_lang_pair = "$out_plots_dir/repos_by_language_pair.pdf";
	run_cmmd("Rscript $script_plot_repos_by_lang_pair -p $bq_proj -d $bq_ds_analysis_results -b $bq_tb_bytes_by_lang -l $bq_tb_langs_by_repo -o $out_pdf_repos_by_lang_pair", $out_pdf_repos_by_lang_pair);
} else {print("\nSkipping step: plot number of repos by language pair\n")}

# Plot number of forks by repo
if($run_forks_by_repo) {
	my $out_pdf_forks_by_repo = "$out_plots_dir/forks_by_repo.pdf";
	run_cmmd("Rscript $script_plot_forks_by_repo -p $bq_proj -d $bq_ds_analysis_results -t $bq_tb_forks_by_repo -o $out_pdf_forks_by_repo", $out_pdf_forks_by_repo);
} else {print("\nSkipping step: plot number of forks by repo\n")}

# Plot number of occurrences of "TODO: fix" by repo
if($run_todo_fix_by_repo) {
	my $out_pdf_todo_fix_by_repo = "$out_plots_dir/todo_fix_by_repo.pdf";
	run_cmmd("Rscript $script_plot_todo_fix_by_repo -p $bq_proj -d $bq_ds_analysis_results -t $bq_tb_todo_fix_by_repo -o $out_pdf_todo_fix_by_repo", $out_pdf_todo_fix_by_repo);
} else {print("\nSkipping step: plot number of occurrences of \"TODO: fix\" by repo\n")}

# Count lines of code and push to BigQuery table
if($run_count_lines_of_code) {
	my $out_log_count_lines_of_code = "$out_results_dir_lines_of_code/run.out";
	my $cmmd_count_lines_of_code = "$python3 $script_count_lines_of_code --in_ds $bq_ds --out_ds $bq_ds_analysis_results --table $bq_tb_lines_of_code " .
	"--outfile $out_log_count_lines_of_code --cloc $cloc_exec";
	run_cmmd($cmmd_count_lines_of_code, $out_log_count_lines_of_code)
} else {print("\nSkipping step: count lines of code\n")}

# Extract comments from source files and push to BigQuery table
if($run_extract_comments) {
	my $cmmd_extract_comments = "$python3 $script_extract_comments --ds_gh $bq_ds --ds_lang $bq_ds_analysis_results ".
	"--out_ds $bq_ds_analysis_results --table $bq_tb_comments";
	run_cmmd($cmmd_extract_comments)
} else {print("\nSkipping step: extract comments\n")}


print("\n\nAll done.\n\n");


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
















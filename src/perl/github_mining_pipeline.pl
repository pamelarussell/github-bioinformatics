use strict;
use warnings;

# BigQuery project
my $bq_proj = "github-bioinformatics-157418";

# BigQuery datasets
my $bq_ds_query_results = "test_repos_query_results";

# BigQuery tables
my $bq_tb_bytes_per_lang = "language_bytes";

# Project directory structure
my $src_dir_R = "/Users/prussell/Documents/Github_mining/src/R/";
my $plots_dir = "/Users/prussell/Documents/Github_mining/plots/test_repos/";

# Programs
my $plot_bytes_per_lang = "$src_dir_R/bytes_by_language.R";

# Plot total size of source files by language
my $out_pdf_bytes_per_lang = "$plots_dir/bytes_by_language.pdf";
system("Rscript", $plot_bytes_per_lang, "-p", $bq_proj, "-d", $bq_ds_query_results, "-t", $bq_tb_bytes_per_lang, "-o", $out_pdf_bytes_per_lang);
if ( $? != 0 ) {die;}




print("\nAll done.\n\n");


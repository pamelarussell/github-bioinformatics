library(jsonlite)

json_params_main <- "/Users/Pamela/Dropbox/Documents/Github_mining/structure/config_main_proj.json"
json_params_high_profile <- "/Users/Pamela/Dropbox/Documents/Github_mining/structure/config_high_profile.json"

# Read parameters from JSON
params_main <- fromJSON(json_params_main, flatten = T)
params_high_profile <- fromJSON(json_params_high_profile, flatten = T)

# Project names
proj_main <- params_main[["bq_proj"]]
proj_high_profile <- params_high_profile[["bq_proj"]]

# Colors for plots
color_high_prof <- "#ff6666"
color_main <- "#80d4ff"

# Local structure
paper_dir <- params_main[["paper_dir"]]
paper_scripts_dir <- paste(paper_dir, "scripts", sep = "/")
saved_repo_features_main <- paste(paper_dir, "data/repo_features_main.txt", sep = "/")
saved_repo_features_high_prof <- paste(paper_dir, "data/repo_features_high_prof.txt", sep = "/")
# Function to load repo features from table
load_repo_features <- function(file) {read.table(file, header = T, sep = "\t", quote = "")}
# Load repo features for both projects
load_repo_features_all <- function() {
  repo_data_main <- load_repo_features(saved_repo_features_main)
  repo_data_high_prof <- load_repo_features(saved_repo_features_high_prof)
  rbind(repo_data_main %>% select(-contains("topic")) %>% mutate(is_high_profile = FALSE), 
                         repo_data_high_prof %>% mutate(is_high_profile = TRUE))
}

# Data from GitHub API
ds_gh <- "repos"
table_pr <- "pull_requests"
table_repo_info <- "repo_metrics"
table_init_commit <- "file_init_commit"
table_licenses <- "licenses"
table_repo_metrics <- "repo_metrics"
table_file_info <- "file_info"
table_commits <- "commits"

# Data from analysis results
ds_analysis <- "analysis"
table_repo_features <- "repo_features"
table_loc_by_repo <- "lines_of_code_by_repo"
table_code_chunk_freq_10_50 <- "code_chunk_freq_10_50"
table_code_chunk_freq_5_80 <- "code_chunk_freq_5_80"
table_loc <- "lines_of_code_by_file"
table_commit_types <- "commit_types"
table_proj_duration <- "project_duration"
table_num_langs_by_repo <- "num_langs_by_repo"
table_num_devs_by_repo <- "num_devs_by_repo"
table_lang_bytes_by_repo <- "language_bytes_by_repo"
table_test_cases <- "test_cases"
table_gender_by_name <- "gender_by_name"
table_gender_commit_authors <- "gender_commit_authors"
table_gender_commits <- "gender_commits"
table_gender_paper_authors <- "gender_paper_authors"
table_comments <- "comments"

# Language features
ds_lang <- "languages"
table_exec_method <- "execution_method"
table_paradigm <- "paradigm"
table_type_system <- "type_system"

# Top languages - included in at least 50 repos
top_langs <- c("Python",
               "Bourne Shell",
               "R",
               "C/C++ Header",
               "Perl",
               "C++",
               "JavaScript",
               "C",
               "Java",
               "Bourne Again Shell",
               "MATLAB",
               "m4",
               "SQL",
               "Ruby",
               "PHP")

# "Languages" that are actually data file types or web pages
non_lang_file_types <- c("HTML",
                         "JSON",
                         "XML",
                         "CSS",
                         "YAML",
                         "Markdown",
                         "XSD",
                         "DTD",
                         "XSLT",
                         "XMI",
                         "Haml",
                         "XHTML",
                         "XAML")

# Function to convert language name to valid column header
format_lang_as_header <- function(lang) {
  gsub("C\\+\\+", "Cpp", gsub("[ /]+", "_", lang))
}

# Lit search
ds_lit_search <- "lit_search"
table_repo_and_article <- "repo_and_article_curated"
table_article_metadata <- "article_metadata_eutils"








suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))

# Join all repo-level data
# Load all the repo-level data from BigQuery and do a full join by repo name
table_list <- c("language_list_by_repo", "num_languages_by_repo", "lines_of_code_by_repo",
                "project_duration_by_repo", "num_devs_by_repo", "commit_types_by_repo", "test_cases_by_repo")
repo_level_data <- data.frame(repo_name = character())
for(table in table_list) {
  table_data <- list_tabledata(project = proj, dataset = ds_analysis, table = table)
  repo_level_data <- full_join(repo_level_data, table_data, by = "repo_name")
}

# Add languages
lang_bytes <- list_tabledata(project = proj, dataset = ds_analysis, table = "bytes_by_language")
lang_list <- lang_bytes$language_name
lang_list_by_repo <- sapply(repo_level_data$languages, function(x) strsplit(x, ","))
for(lang in lang_list) {
  repo_level_data[[lang]] <- unlist(lapply(lang_list_by_repo, function(x) lang %in% x))
}
repo_level_data <- repo_level_data %>% rename(Cpp = `C++`)

# Repo info from gh api
repo_data_gh_api <- list_tabledata(project = proj, dataset = ds_gh, table = table_repo_info)
repo_level_data <- full_join(repo_level_data, repo_data_gh_api, by = "repo_name")

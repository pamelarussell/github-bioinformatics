
##### Setup #####

rm(list=ls())
suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(lubridate))
suppressPackageStartupMessages(library(parsedate))
setwd("/Users/Pamela/Dropbox/Documents/Github_mining/paper/")
source("../src/R/project_info.R")


##### Functions and utilities #####

# Fetch table from BigQuery
get_table <- function(proj, ds, table) {
  list_tabledata(project = proj, dataset = ds, table = table, max_pages = Inf)
}

# Get formatted table ID e.g. "[github-bioinformatics-171721:analysis.lines_of_code_by_file]"
table_str <- function(proj, dataset, table) {paste("[", proj, ":", dataset, ".", table, "]", sep = "")}

# Get formatted table ID for standard SQL e.g. `github-bioinformatics-171721.repos.file_init_commit`
table_str_std_sql <- function(proj, dataset, table) {paste("`", proj, ".", dataset, ".", table, "`", sep = "")}

# Get query result from BigQuery
fetch_query_res <- function(query, proj) {query_exec(query, project = proj, max_pages = Inf)}

# Join a table to repo_data
join_tbl <- function(repo_data, data) {
  for (colname in colnames(data)) {
    if (colname != "repo_name" && colname %in% colnames(repo_data)) {
      stop(paste("repo_data already contains column", colname))
    }
  }
  full_join(repo_data, data, by = "repo_name")
}

# Change NA to 0
na_to_zero <- function(x) {
  if (is.na(x)) 0
  else x
}

# Change NA to false
na_to_false <- function(x) {
  if (is.na(x)) FALSE
  else x
}

# Change NA to zero in repo_data for a bunch of columns
columns_na_to_zero <- function(repo_data, colnms) {
  rtrn <- repo_data
  for (col in colnms) {
    if (col != "repo_name") {
      rtrn[[col]] <- sapply(rtrn[[col]], na_to_zero)
    }
  }
  rtrn
}

# Longest contiguous subsequence of true values in a boolean vector
max_contiguous <- function(b) {
  max <- 0
  curr <- 0
  for (i in 1:length(b)) {
    if(b[i]) {curr <- curr + 1} 
    else {
      if (curr > max) {max <- curr}
      curr <- 0
    }
  }
  if (curr > max) {max <- curr}
  max
}

# Max number of consecutive months with data in a specified column
max_consecutive_months <- function(data, repo, month_col, count_true = T) {
  data_repo <- data %>% filter(repo_name == repo)
  total_months <- data_repo[1, "repo_num_months"]
  month_has_data <- rep(F, total_months)
  for (i in 1:nrow(data_repo)) {
    m <- data_repo[i, month_col] + 1
    if (m > length(month_has_data)) {
      warning(paste("Month outside span given in data:", repo, "\n"))
    } else {
      month_has_data[m] <- T
    }
  }
  if (count_true) {
    max_contiguous(month_has_data)
  } else {
    max_contiguous(!month_has_data)
  }
}

# Column names of repo_data matching pattern
cols <- function(repo_data, p) {
  names(repo_data)[grepl(p, names(repo_data))] 
}

# Add years to datetime
add_years <- function(date, years) {
  d <- as.POSIXlt(date)
  d$year <- d$year + years
  as.Date(d)
}

# Get various lines of code measurements
loc_data <- function(file_info_df, suffix, include_mean_size = TRUE) {
  data <- file_info_df %>% 
    group_by(repo_name) %>% 
    summarise(
      num_files = n(),
      mean_bytes = mean(size),
      total_lines_of_code = sum(lines_of_code), 
      total_lines_comment = sum(lines_comment), 
      total_lines_code_and_comment = sum(lines_of_code) + sum(lines_comment),
      max_lines_code = max(lines_of_code),
      max_lines_code_and_comment = max(lines_of_code + lines_comment),
      mean_lines_code = mean(lines_of_code),
      mean_lines_code_and_comment = mean(lines_of_code + lines_comment),
      mean_bytes_per_line_code_and_comment = sum(size) / (sum(lines_of_code) + sum(lines_comment))
    ) %>% mutate(pct_lines_comment = total_lines_comment / total_lines_code_and_comment)
  
  if(!include_mean_size) {
    data <- data %>% select(-mean_bytes)
  }
  
  colnames(data) <- sapply(colnames(data), function(x) {
    if (x == "repo_name") x
    else paste(x, suffix, sep = "")
  })
  
  data
}

# Count bytes and files for a boolean column in the file info
add_file_counts_bool <- function(repo_data, file_info_with_lang_no_data, col) {
  filtered <- file_info_with_lang_no_data[which(file_info_with_lang_no_data[[col]]), ]
  
  # Total file size
  bytes <- filtered %>% 
    group_by(repo_name) %>% 
    summarise(xxxxx = sum(size)) %>% 
    left_join(repo_data %>% 
                select(repo_name, total_file_size_no_data), by = "repo_name") %>% 
    mutate(yyyyy = xxxxx / total_file_size_no_data) %>% 
    mutate(zzzzz = xxxxx > 0) %>%
    select(repo_name, xxxxx, yyyyy, zzzzz)
  colname_bytes <- paste("total_bytes_no_data_", col, sep = "")
  colname_pct <- paste("pct_bytes_no_data_", col, sep = "")
  colname_bool <- paste("has_", col, sep = "")
  colnames(bytes) <- c("repo_name", colname_bytes, colname_pct, colname_bool)
  repo_data <- join_tbl(repo_data, bytes)
  repo_data[[colname_bytes]] <- sapply(repo_data[[colname_bytes]], na_to_zero)
  repo_data[[colname_pct]] <- sapply(repo_data[[colname_pct]], na_to_zero)
  repo_data[[colname_bool]] <- sapply(repo_data[[colname_bool]], na_to_false)
  
  # Total number of files
  files <- filtered %>% 
    group_by(repo_name) %>% 
    summarise(xxxxx = n()) %>%
    left_join(repo_data %>%
                select(repo_name, num_files_no_data), by = "repo_name") %>%
    mutate(yyyyy = xxxxx / num_files_no_data) %>%
    select(repo_name, xxxxx, yyyyy)
  colname_files <- paste("total_files_", col, sep = "")
  colname_pct <- paste("pct_files_no_data_", col, sep = "")
  colnames(files) <- c("repo_name", colname_files, colname_pct)
  repo_data <- join_tbl(repo_data, files)
  repo_data[[colname_files]] <- sapply(repo_data[[colname_files]], na_to_zero)
  repo_data[[colname_pct]] <- sapply(repo_data[[colname_pct]], na_to_zero)
  
  # Return repo data
  repo_data
  
}

# Count amount of code in test cases for files with a boolean property
add_test_case_code_amt_bool <- function(repo_data, test_cases_by_lang_property, colnm) {
  filtered <- test_cases_by_lang_property[which(test_cases_by_lang_property[[colnm]]),]
  summarized <- filtered %>% 
    group_by(repo_name) %>% 
    summarize(total_bytes_test_cases_category = sum(size))
  joined <- repo_data[, c("repo_name", paste("total_bytes_no_data_", colnm, sep = ""))] %>% 
    left_join(summarized, by = "repo_name")
  joined$total_bytes_test_cases_category <- sapply(joined$total_bytes_test_cases_category, na_to_zero)
  colnames(joined) <- c("repo_name", "total_bytes_no_data_category", "total_bytes_test_cases_category")
  joined <- joined %>% 
    mutate(pct_bytes_test_cases_category = total_bytes_test_cases_category / total_bytes_no_data_category) %>%
    select(repo_name, total_bytes_test_cases_category, pct_bytes_test_cases_category)
  colnames(joined) <- sapply(colnames(joined), function(x) sub("category", colnm, x))
  repo_data <- join_tbl(repo_data, joined)
  repo_data
}

# Get file info
get_file_info <- function(proj) {
  query <- paste("SELECT
  file_info.repo_name AS repo_name,
                 loc.language AS language,
                 loc.code AS lines_of_code,
                 loc.comment as lines_comment,
                 file_info.size AS size
                 FROM (
                 SELECT
                 repo_name,
                 sha
                 FROM
                 ", table_str(proj, ds_gh, table_file_info), "
                 GROUP BY
                 repo_name,
                 sha,
                 size) AS file_info
                 INNER JOIN (
                 SELECT
                 sha,
                 language,
                 comment,
                 code
                 FROM
                 ", table_str(proj, ds_analysis, table_loc), "
                 GROUP BY
                 sha,
                 language,
                 comment,
                 code) AS loc
                 ON
                 file_info.sha = loc.sha", sep="")
  
  query_exec(query, project = proj, max_pages = Inf)
}

# Get test cases
get_test_cases_no_data <- function(proj) {
  # Query to join file size to test case table
  query <- paste("SELECT
               test_cases.repo_name AS repo_name,
               test_cases.path AS path,
               test_cases.language AS language,
               test_cases.lines AS lines,
               file_info.size AS size
               FROM (
               SELECT
               *
               FROM ", table_str(proj, ds_analysis, table_test_cases), ") AS test_cases
               INNER JOIN (
               SELECT
               sha,
               size
               FROM
               ", table_str(proj, ds_gh, table_file_info),
                 "GROUP BY
               sha,
               size ) AS file_info
               ON
               test_cases.sha = file_info.sha", sep="")
  
  fetch_query_res(query, proj) %>% filter(!language %in% non_lang_file_types)
}

##### Languages #####

# Import language properties
# Language properties are in the main dataset; are independent of actual data for the project
lang_exec_method <- get_table(proj_main, ds_lang, table_exec_method)
lang_paradigm <- get_table(proj_main, ds_lang, table_paradigm)
lang_type_system <- get_table(proj_main, ds_lang, table_type_system)
lang_type_system_bool <- as.tbl(lang_type_system) %>% 
  mutate(type_system_static = system == "static", 
         type_system_dynamic = system == "dynamic", 
         type_system_safe = safety == "safe", 
         type_system_unsafe = safety == "unsafe", 
         compatibility_nominative = compatibility == "nominative", 
         compatibility_structural = compatibility == "structural", 
         compatibility_duck = compatibility == "duck")

# Language features
lang_features <- c("interpreted", "compiled", "type_system_static", "type_system_dynamic", "type_system_safe",
                   "type_system_unsafe", "array", "declarative", "functional_impure", "functional_pure",
                   "imperative", "logic", "object_oriented", "procedural", "compatibility_nominative",
                   "compatibility_structural", "compatibility_duck")


##### Functions to join new analysis to a table #####


# Repo license
add_license <- function(proj, repo_data) {
  message("Adding repo licenses")
  join_tbl(repo_data, 
           get_table(proj, ds_gh, table_licenses) %>%
             select(repo_name, license)
  )
}

# Project duration
add_proj_duration <- function(proj, repo_data) {
  message("Adding project duration")
  join_tbl(repo_data, 
           get_table(proj, ds_analysis, table_proj_duration)
  )
}

# Gender of developers and paper authors
add_gender <- function(proj, repo_data) {
  message("Adding gender analysis")
  rtrn <- join_tbl(repo_data, 
                   get_table(proj, ds_analysis, table_gender_commit_authors) %>% 
                     rename(commit_authors_female = female,
                            commit_authors_male = male,
                            commit_authors_no_gender = no_gender,
                            team_type_gender = team_type,
                            shannon_commit_author_gender = shannon) %>%
                     mutate(commit_authors = commit_authors_male + commit_authors_female + commit_authors_no_gender))
  
  rtrn <- join_tbl(rtrn, 
                   get_table(proj, ds_analysis, table_gender_commits) %>% 
                     rename(commits_female = female,
                            commits_male = male,
                            commits_no_gender = no_gender,
                            shannon_commits_gender = shannon) %>%
                     mutate(commits = commits_female + commits_male + commits_no_gender))
  
  rtrn <- join_tbl(rtrn, 
                   get_table(proj, ds_analysis, table_gender_paper_authors) %>% 
                     rename(paper_authors_female = female,
                            paper_authors_male = male,
                            paper_authors_no_gender = no_gender,
                            team_type_paper_authors = team_type,
                            first_author_gender = first_author,
                            last_author_gender = last_author,
                            shannon_paper_authors = shannon) %>%
                     mutate(paper_authors = paper_authors_female + paper_authors_male + paper_authors_no_gender))
  rtrn
}

# Repo-level metrics from GitHub API
add_repo_metrics <- function(proj, repo_data) {
  message("Adding repo metrics")
  join_tbl(repo_data, 
           get_table(proj, ds_gh, table_repo_metrics) %>%
             select(repo_name, is_fork, stargazers_count, watchers_count, forks_count, subscribers_count))
}

# Journal articles publishing the repos
add_article_info <- function(proj, repo_data) {
  message("Adding article info")
  article_metadata <- get_table(proj, ds_lit_search, table_article_metadata) %>% 
    select(repo_name, iso_abbrev, year_pubmed, month_pubmed, day_pubmed, cited_by_pmc, cited_by_pmc_date) %>% 
    rename(journal = iso_abbrev, num_citations_pmc = cited_by_pmc, date_citations = cited_by_pmc_date) %>%
    mutate(date_pubmed = as.Date(paste(year_pubmed, month_pubmed, day_pubmed, sep = "-"))) %>%
    select(repo_name, journal, date_pubmed, num_citations_pmc, date_citations) %>%
    mutate(date_pubmed_plus_2_years = add_years(date_pubmed, 2)) %>% 
    mutate(weeks_since_pub_minus_2_years = difftime(date_citations, date_pubmed_plus_2_years, units = "weeks"))
  
  article_metadata$weeks_since_pub_minus_2_years <- sapply(article_metadata$weeks_since_pub_minus_2_years,
                                                           function(x) {if (x <= 0) NA else x})
  
  article_metadata <- article_metadata %>% 
    mutate(num_citations_per_week_pmc_minus_2_years = num_citations_pmc / weeks_since_pub_minus_2_years) %>% 
    select(repo_name, journal, date_pubmed, num_citations_pmc, num_citations_per_week_pmc_minus_2_years)
  
  join_tbl(repo_data, article_metadata)
}

add_file_info  <- function(proj, repo_data) {
  message("Adding file info")
  file_info <- get_file_info(proj)
  file_info_no_data <- file_info %>% filter(!language %in% non_lang_file_types)
  
  rtrn <- join_tbl(repo_data, 
                   file_info %>% 
                     group_by(repo_name) %>% 
                     summarize(
                       num_langs = length(unique(language)),
                       total_file_size = sum(as.numeric(size)), 
                       largest_file_size = max(as.numeric(size)), 
                       mean_file_size = mean(as.numeric(size)))
  )
  
  rtrn <- join_tbl(rtrn, 
                   file_info_no_data %>% 
                     group_by(repo_name) %>% 
                     summarize(
                       num_langs_no_data = length(unique(language)),
                       total_file_size_no_data = sum(as.numeric(size)), 
                       largest_file_size_no_data = max(as.numeric(size)), 
                       mean_file_size_no_data = mean(as.numeric(size)))
  )
  
  rtrn
}


add_init_commit  <- function(proj, repo_data) {
  message("Adding initial commit times")
  # Query to get summary of times when files were first committed
  query <- paste("
        SELECT
          COUNT(repo_name) AS num_files_same_commit_hour,
          repo_name,
          repo_duration_months + 1 as repo_num_months,
          file_commit_months_from_proj_start,
          file_commit_days_from_proj_start,
          file_commit_hours_from_proj_start
        FROM (
          SELECT
            project_duration.repo_name AS repo_name,
            project_duration.first_commit AS repo_first_commit,
            project_duration.last_commit AS repo_last_commit,
            DATETIME_DIFF(DATETIME(TIMESTAMP(project_duration.last_commit)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              HOUR) AS repo_duration_hours,
            DATETIME_DIFF(DATETIME(TIMESTAMP(project_duration.last_commit)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              DAY) AS repo_duration_days,
            DATETIME_DIFF(DATETIME(TIMESTAMP(project_duration.last_commit)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              MONTH) AS repo_duration_months,
            init_commit.init_commit_timestamp AS file_commit,
            DATETIME_DIFF(DATETIME(TIMESTAMP(init_commit.init_commit_timestamp)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              HOUR) AS file_commit_hours_from_proj_start,
            DATETIME_DIFF(DATETIME(TIMESTAMP(init_commit.init_commit_timestamp)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              DAY) AS file_commit_days_from_proj_start,
            DATETIME_DIFF(DATETIME(TIMESTAMP(init_commit.init_commit_timestamp)),
              DATETIME(TIMESTAMP(project_duration.first_commit)),
              MONTH) AS file_commit_months_from_proj_start
          FROM (
            SELECT
              repo_name,
              init_commit_timestamp
            FROM
              ", table_str_std_sql(proj, ds_gh, table_init_commit), ") AS init_commit
          INNER JOIN
            ", table_str_std_sql(proj, ds_analysis, table_proj_duration), " AS project_duration
          ON
            init_commit.repo_name = project_duration.repo_name)
        GROUP BY
          repo_name,
          repo_duration_hours,
          repo_duration_days,
          repo_duration_months,
          file_commit_hours_from_proj_start,
          file_commit_days_from_proj_start,
          file_commit_months_from_proj_start
        ORDER BY
          repo_name",
                 sep = "")
  
  # Pull down query results
  init_commit <- query_exec(query, project = proj, max_pages = Inf, use_legacy_sql = F)
  
  # Number of different days when new files were added
  rtrn <- join_tbl(repo_data, 
                   init_commit %>% 
                     select(repo_name, file_commit_days_from_proj_start) %>% 
                     group_by(repo_name) %>% 
                     summarise(num_days_new_files_added = n_distinct(file_commit_days_from_proj_start))
  )
  
  # Mean number of files added per day when new files were added
  rtrn <- join_tbl(rtrn, 
                   init_commit %>% 
                     group_by(repo_name, file_commit_days_from_proj_start) %>% 
                     summarise(files_added = sum(num_files_same_commit_hour)) %>% 
                     summarise(mean_new_files_per_day_with_new_files = mean(files_added))
  )
  
  # Mean day since project initial commit that new files were added
  rtrn <- join_tbl(rtrn, 
                   init_commit %>% 
                     group_by(repo_name) %>% 
                     summarise(mean_day_new_files_added = sum(num_files_same_commit_hour * file_commit_days_from_proj_start) / sum(num_files_same_commit_hour))
  )
  
  # Mean number of files added per month including months with no new files
  rtrn <- join_tbl(rtrn, 
                   init_commit %>% 
                     group_by(repo_name) %>% 
                     summarize(mean_files_added_per_month = sum(num_files_same_commit_hour / repo_num_months))
  )
  
  # Proportion of months with new files added
  rtrn <- join_tbl(rtrn, 
                   init_commit %>% 
                     group_by(repo_name) %>% 
                     summarise(months_with_new_files = n_distinct(file_commit_months_from_proj_start)) %>% 
                     inner_join(init_commit %>% 
                                  select(repo_name, repo_num_months) %>% 
                                  distinct(), by = "repo_name") %>% 
                     mutate(pct_months_new_files_added = months_with_new_files / repo_num_months) %>% 
                     select(repo_name, pct_months_new_files_added)
  )
  
  # Longest number of months in a row with new files added
  new_file_consecutive_months <- init_commit %>% 
    select(repo_name) %>% 
    distinct()
  new_file_consecutive_months$consecutive_months_with_new_files_added <- 
    sapply(new_file_consecutive_months$repo_name, function(repo) max_consecutive_months(init_commit, repo, "file_commit_months_from_proj_start"))
  new_file_consecutive_months$consecutive_months_no_new_files_added <- 
    sapply(new_file_consecutive_months$repo_name, function(repo) max_consecutive_months(init_commit, repo, "file_commit_months_from_proj_start", F))
  rtrn <- join_tbl(rtrn, new_file_consecutive_months)
  rtrn
}

# Outside contributions
add_outside_commits <- function(proj, repo_data) {
  message("Adding outside commits")
  commits_table_str <- table_str(proj, ds_gh, table_commits)
  
  commits <- fetch_query_res(paste("
                                     SELECT
                                     repo_name,
                                     committer_id,
                                     author_id
                                     FROM
                                     ", table_str(proj, ds_gh, table_commits), "
                                     GROUP BY
                                     repo_name,
                                     committer_id,
                                     author_id"), proj)
  
  # Number of commit authors who are never committers
  rtrn <- join_tbl(repo_data, 
                   as.tbl(commits) %>% 
                     select(repo_name, author_id) %>% 
                     anti_join(commits %>% select(repo_name, committer_id), 
                               by = c("repo_name", "author_id" = "committer_id")) %>% 
                     group_by(repo_name) %>% 
                     summarise(num_non_committing_authors = n())
  )
  
  rtrn$num_non_committing_authors <- sapply(rtrn$num_non_committing_authors, na_to_zero)
  
  
  # Percentage of commits with different author and committer
  query <- paste("
        SELECT
          num_commits.repo_name AS repo_name,
          num_commits_diff_author.num_commits / num_commits.num_commits as pct_commits_diff_author_committer
        FROM (
          SELECT
            repo_name,
            COUNT(repo_name) AS num_commits
          FROM
            ", commits_table_str, "
          GROUP BY
            repo_name) AS num_commits
        INNER JOIN (
          SELECT
            repo_name,
            COUNT(repo_name) AS num_commits
          FROM
            ", commits_table_str, "
          WHERE
            author_id != committer_id
          GROUP BY
            repo_name) AS num_commits_diff_author
        ON
          num_commits.repo_name = num_commits_diff_author.repo_name
        ", sep = "")
  
  rtrn <- join_tbl(rtrn, fetch_query_res(query, proj))
  rtrn$pct_commits_diff_author_committer <- sapply(rtrn$pct_commits_diff_author_committer, na_to_zero)
  rtrn
}

# Median and mean commit message length
add_commit_message <- function(proj, repo_data) {
  message("Adding commit message")
  commits_table_str <- table_str(proj, ds_gh, table_commits)
  query <- paste("
        SELECT
          repo_name,
          NTH(501, QUANTILES(LENGTH(commit_message), 1001)) AS median_commit_message_len,
          AVG(LENGTH(commit_message)) AS mean_commit_message_len
        FROM
          ", commits_table_str, "
        GROUP BY
          repo_name
        ", sep = "")
  join_tbl(repo_data, fetch_query_res(query, proj))
}

# Commit timing by month
add_commit_timing <- function(proj, repo_data) {
  message("Adding commit timing")
  query <- paste("
        SELECT
          COUNT(repo_name) AS num_commits_same_month,
          repo_name,
          DATETIME_DIFF(DATETIME(TIMESTAMP(repo_last_commit)),
            DATETIME(TIMESTAMP(repo_first_commit)),
            MONTH) + 1 AS repo_num_months,
          DATETIME_DIFF(DATETIME(TIMESTAMP(commit_timestamp)),
            DATETIME(TIMESTAMP(repo_first_commit)),
            MONTH) AS commit_months_from_proj_start
        FROM (
          SELECT
            first_last.repo_name AS repo_name,
            first_last.first_commit AS repo_first_commit,
            first_last.last_commit AS repo_last_commit,
            commits.author_commit_date AS commit_timestamp
          FROM (
            SELECT
              repo_name,
              author_commit_date
            FROM
              ", table_str_std_sql(proj, ds_gh, table_commits), ") AS commits
          INNER JOIN (
            SELECT
              repo_name,
              first_commit,
              last_commit
            FROM (
              SELECT
                repo_name,
                MIN(author_commit_date) AS first_commit,
                MAX(author_commit_date) AS last_commit
              FROM
                ", table_str_std_sql(proj, ds_gh, table_commits), "
              GROUP BY
                repo_name ) ) AS first_last
          ON
            commits.repo_name = first_last.repo_name )
        GROUP BY
          repo_name,
          repo_num_months,
          commit_months_from_proj_start
        ORDER BY
          repo_name,
          commit_months_from_proj_start
        ", sep = "")
  
  commit_months <- query_exec(query, project = proj, max_pages = Inf, use_legacy_sql = F)
  
  # Mean commits per month including months with no commits
  rtrn <- join_tbl(repo_data, 
                   commit_months %>% 
                     group_by(repo_name) %>% 
                     summarize(mean_commits_per_month = sum(num_commits_same_month / repo_num_months))
  )
  
  # Percentage of months with at least one commit
  rtrn <- join_tbl(rtrn, 
                   commit_months %>% 
                     group_by(repo_name) %>% 
                     summarise(months_with_commits = n_distinct(commit_months_from_proj_start)) %>% 
                     inner_join(commit_months %>% 
                                  select(repo_name, repo_num_months) %>% 
                                  distinct(), by = "repo_name") %>% 
                     mutate(pct_months_with_commits = months_with_commits / repo_num_months) %>% 
                     select(repo_name, pct_months_with_commits)
  )
  
  # Longest number of months in a row with commits
  commit_consecutive_months <- commit_months %>% 
    select(repo_name) %>% 
    distinct()
  commit_consecutive_months$consecutive_months_with_commits <- 
    sapply(commit_consecutive_months$repo_name, function(repo) max_consecutive_months(commit_months, repo, "commit_months_from_proj_start"))
  commit_consecutive_months$consecutive_months_no_commits <- 
    sapply(commit_consecutive_months$repo_name, function(repo) max_consecutive_months(commit_months, repo, "commit_months_from_proj_start", F))
  rtrn <- join_tbl(rtrn, commit_consecutive_months)
  
  # Were there commits after the paper appeared in PubMed?
  commits_after_article_in_pubmed <- rtrn %>% 
    select(repo_name, last_commit, date_pubmed) %>% 
    mutate(commits_after_article_in_pubmed = last_commit > date_pubmed) %>%
    select(repo_name, commits_after_article_in_pubmed)
  join_tbl(rtrn, commits_after_article_in_pubmed)
}


# Frequency of code chunks within repo
add_code_chunk_freq <- function(proj, repo_data) {
  message("Adding code chunk frequency")
  process_code_chunk_freq <- function(table_name, col_suffix) {
    
    query <- paste("SELECT repo_name, num_occurrences FROM [",
                   proj, ":", ds_analysis, ".", table_name, "]",
                   sep = "")
    
    code_chunk_freq <- query_exec(query, project = proj, max_pages = Inf)
    
    total_code_chunks <- code_chunk_freq %>%
      group_by(repo_name) %>%
      summarize(total_code_chunks = n())
    
    repeated_code_chunks <- code_chunk_freq %>%
      filter(num_occurrences > 1) %>%
      group_by(repo_name) %>%
      summarize(repeated_code_chunks = n())
    
    max_code_chunk_occurrence <- code_chunk_freq %>%
      group_by(repo_name) %>%
      summarise(max_code_chunk_occurrence = max(num_occurrences))
    
    mean_code_chunk_occurrence <- code_chunk_freq %>%
      group_by(repo_name) %>%
      summarise(mean_code_chunk_occurrence = mean(num_occurrences))
    
    join_data <- total_code_chunks %>%
      full_join(repeated_code_chunks, by = "repo_name") %>%
      full_join(max_code_chunk_occurrence, by = "repo_name") %>%
      full_join(mean_code_chunk_occurrence, by = "repo_name")
    
    colnames(join_data) <- sapply(colnames(join_data), function(x) {
      if(x == "repo_name") x
      else paste(x, "_", col_suffix, sep="")
    })
    
    join_data
    
  }
  
  # Do the work
  f_10_50 <- process_code_chunk_freq(table_code_chunk_freq_10_50, "10_50")
  f_5_80 <- process_code_chunk_freq(table_code_chunk_freq_5_80, "5_80")
  rtrn <- join_tbl(repo_data, f_10_50)
  rtrn <- join_tbl(rtrn, f_5_80)
  rtrn
}

# Amount of code by language
add_amt_code_by_lang <- function(proj, repo_data) {
  message("Adding amount of code by language")
  # Import table of language bytes by repo
  lang_bytes_by_repo <- get_table(proj, ds_analysis, table_lang_bytes_by_repo) 
  
  # Calculate total bytes per repo not including data file types
  total_bytes_by_repo_no_data <- lang_bytes_by_repo %>% 
    filter(!language %in% non_lang_file_types) %>%
    group_by(repo_name) %>%
    summarise(total_bytes_no_data = sum(total_bytes))
  
  rtrn <- repo_data
  # Add analysis for each top language
  for (lang in top_langs) {
    
    # Column names to add to repo data
    colname_exists <- paste("includes_", lang, sep = "")
    colname_bytes <- paste("bytes_", lang, sep = "")
    colname_pct <- paste("pct_bytes_no_data_", lang, sep = "")
    
    # Filter language bytes table for the language
    bytes_this_lang <- lang_bytes_by_repo %>% group_by(repo_name) %>% filter(language == lang)
    
    # Whether the repo includes the language or not
    rtrn[[colname_exists]] <- sapply(rtrn$repo_name, function(x) x %in% bytes_this_lang$repo_name)
    
    # Number of bytes of the language
    rtrn[[colname_bytes]] <- 
      sapply(rtrn$repo_name, 
             function(x) {
               a <- unlist(bytes_this_lang[which(bytes_this_lang$repo_name == x), "total_bytes"])
               if(length(a) > 0) a 
               else 0
             })
    
    # Percentage of bytes in this language not including data file types
    rtrn[[colname_pct]] <- 
      sapply(rtrn$repo_name, 
             function(x) {
               a <- unlist(bytes_this_lang[which(bytes_this_lang$repo_name == x), "total_bytes"])
               if(length(a) > 0) {
                 t <- unlist(total_bytes_by_repo_no_data[which(total_bytes_by_repo_no_data$repo_name == x), "total_bytes_no_data"])
                 a / t
               }
               else 0
             })
  }
  
  rtrn
}

# Lines of code by file
add_loc_by_file <- function(proj, repo_data) {
  message("Adding lines of code by file")
  file_info <- get_file_info(proj)
  file_info_no_data <- file_info %>% filter(!language %in% non_lang_file_types)
  loc_data_file_info <- loc_data(file_info, "", FALSE)
  rtrn <- join_tbl(repo_data, loc_data_file_info)
  rtrn <- columns_na_to_zero(rtrn, colnames(loc_data_file_info))
  
  loc_data_file_info_no_data <- loc_data(file_info_no_data, "_no_data", FALSE)
  rtrn <- join_tbl(rtrn, loc_data_file_info_no_data)
  rtrn <- columns_na_to_zero(rtrn, colnames(loc_data_file_info_no_data))
  
  for (lang in top_langs) {
    data <- loc_data(
      file_info %>% filter(language == lang), 
      paste("_", lang, sep = ""))
    rtrn <- join_tbl(rtrn, data)
    rtrn <- columns_na_to_zero(rtrn, colnames(data))
  }
  
  rtrn
}


# Test cases
add_test_cases <- function(proj, repo_data) {
  message("Adding test cases")
  test_cases_no_data <- get_test_cases_no_data(proj)
  
  # Add basic summary of test cases
  rtrn <- join_tbl(repo_data, test_cases_no_data %>% 
                     group_by(repo_name) %>% 
                     summarise(
                       num_test_cases_no_data = n(),
                       total_lines_test_cases_no_data = sum(lines),
                       total_size_test_cases_no_data = sum(size),
                       num_langs_test_cases_no_data = length(unique(language))))
  rtrn$total_lines_test_cases_no_data <- sapply(rtrn$total_lines_test_cases_no_data, na_to_zero)
  rtrn$total_size_test_cases_no_data <- sapply(rtrn$total_size_test_cases_no_data, na_to_zero)
  rtrn$num_langs_test_cases_no_data <- sapply(rtrn$num_langs_test_cases_no_data, na_to_zero)
  
  # Add percentages with respect to whole repo
  rtrn$pct_files_test_cases_no_data <- 
    rtrn$num_test_cases_no_data / rtrn$num_files_no_data
  rtrn$pct_lang_with_test_cases_no_data <- 
    rtrn$num_langs_test_cases_no_data / rtrn$num_langs_no_data
  rtrn$pct_lines_in_test_cases_no_data <-
    rtrn$total_lines_test_cases_no_data / rtrn$total_lines_of_code_no_data
  rtrn$pct_bytes_in_test_cases_no_data <-
    rtrn$total_size_test_cases_no_data / rtrn$total_file_size_no_data
  
  rtrn
}

# Language features
add_lang_features <- function(proj, repo_data) {
  message("Adding language features")
  file_info <- get_file_info(proj)
  file_info_no_data <- file_info %>% filter(!language %in% non_lang_file_types)
  test_cases_no_data <- get_test_cases_no_data(proj)
  rtrn <- repo_data
  # Join language properties to file info
  file_info_with_lang_no_data <- as.tbl(file_info_no_data) %>% 
    mutate(language = tolower(language)) %>% 
    select(repo_name, language, size) %>% 
    left_join(lang_exec_method, by = "language") %>% 
    left_join(lang_type_system, by = "language") %>% 
    left_join(lang_paradigm, by = "language") %>%
    mutate(type_system_static = system == "static") %>%
    mutate(type_system_dynamic = system == "dynamic") %>%
    mutate(type_system_safe = safety == "safe") %>%
    mutate(type_system_unsafe = safety == "unsafe") %>%
    mutate(compatibility_nominative = compatibility == "nominative") %>%
    mutate(compatibility_structural = compatibility == "structural") %>%
    mutate(compatibility_duck = compatibility == "duck")
  
  for(feat in lang_features) {
    rtrn <- add_file_counts_bool(rtrn, file_info_with_lang_no_data, feat)
  }
  
  # Amount of code in test cases for various language properties
  test_cases_by_lang_property <- as.tbl(test_cases_no_data) %>% 
    mutate(language = tolower(language)) %>% 
    left_join(lang_exec_method, by = "language") %>%
    left_join(lang_paradigm, by = "language") %>%
    left_join(lang_type_system_bool, by = "language")
  
  for(feat in lang_features) {
    rtrn <- add_test_case_code_amt_bool(rtrn, test_cases_by_lang_property, feat)
  }
  
  rtrn
}


# Topic modeling of paper abstracts
add_topic_modeling <- function(proj, repo_data) {
  # Run topic modeling of article abstracts
  # Only run for main dataset
  rtrn <- repo_data
  if(proj == proj_main) {
    message("Adding topic modeling")
    source("../src/R/document_classification/topics.R", local = TRUE)
    # Add each topic as a binary variable
    for(t in unique(abstract_top_topics$topic)) {
      colname <- paste("topic_", t, sep = "")
      df <- abstract_top_topics %>% filter(topic == t) %>% select(repo_name)
      df[[colname]] <- TRUE
      rtrn <- join_tbl(rtrn, df)
      rtrn[[colname]] <- sapply(rtrn[[colname]], na_to_false)
    }
  }
  rtrn
}

# Save table to a file
save_table <- function(proj, repo_data) {
  message("Saving local table")
  if(proj == proj_main) {
    saved_repo_features <- saved_repo_features_main
  } else {
    if(proj == proj_high_profile) {
      saved_repo_features <- saved_repo_features_high_prof
    } else {
      stop("proj not recognized")
    }
  }
  
  # Convert column names to valid headers
  rtrn <- repo_data
  colnames(rtrn) <- sapply(colnames(rtrn), format_lang_as_header)
  write.table(rtrn, file = saved_repo_features, quote = F, sep = "\t", row.names = F)
  rtrn
}


##### Pull in all data for a project and write to table on disk #####

compile_and_save_proj_data <- function(proj) {
  message(paste("\nGathering repo metrics for project:", proj, "\n"))
  repo_data <- data.frame(repo_name = character(0))
  repo_data <- add_license(proj, repo_data)
  repo_data <- add_proj_duration(proj, repo_data)
  repo_data <- add_gender(proj, repo_data)
  repo_data <- add_repo_metrics(proj, repo_data)
  repo_data <- add_article_info(proj, repo_data)
  repo_data <- add_file_info(proj, repo_data)
  repo_data <- add_init_commit(proj, repo_data)
  repo_data <- add_commit_message(proj, repo_data)
  repo_data <- add_commit_timing(proj, repo_data)
  #repo_data <- add_code_chunk_freq(proj, repo_data)
  repo_data <- add_amt_code_by_lang(proj, repo_data)
  repo_data <- add_loc_by_file(proj, repo_data)
  repo_data <- add_test_cases(proj, repo_data)
  repo_data <- add_lang_features(proj, repo_data)
  repo_data <- add_outside_commits(proj, repo_data)
  repo_data <- add_topic_modeling(proj, repo_data)
  repo_data <- save_table(proj, repo_data)
  repo_data
}

# Do the work
repo_data_high_prof <- compile_and_save_proj_data(proj_high_profile)
repo_data_main <- compile_and_save_proj_data(proj_main)

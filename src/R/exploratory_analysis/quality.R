# Environment setup
suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(tidyr))
source("~/Dropbox/Documents/Github_mining/src/R/project_info.R")

# Function to load duplicated chunks
load_dup_chunks <- function(table) {
  query <- paste("SELECT * FROM [", proj, ":", ds_analysis, ".", table, "] WHERE num_occurrences > 1", sep="")
  query_exec(query, project = proj)
}

# Function to sum duplicated lines of code
add_dup_loc <- function(dup_chunks, chunk_size) {
  total_loc_in_dup_chunks <- 
    dup_chunks %>% 
    group_by(repo_name) %>% 
    summarize(sum_dup_chunk_len = chunk_size * sum(num_occurrences)) %>%
    right_join(lines_of_code_by_repo, by = "repo_name")
  total_loc_in_dup_chunks[is.na(total_loc_in_dup_chunks)] <- 0
  total_loc_in_dup_chunks
}

# Load lines of code by repo 
lines_of_code_by_repo <- list_tabledata(project = proj, dataset = ds_analysis, table = table_loc_by_repo)

# Load duplicated code chunks
dup_chunks_10_50 <- load_dup_chunks(table_code_chunk_freq_10_50)
dup_chunks_5_80 <- load_dup_chunks(table_code_chunk_freq_5_80)

# Add up duplicated lines of code
dup_loc_10_50 <- add_dup_loc(dup_chunks_10_50, 10)
dup_loc_5_80 <- add_dup_loc(dup_chunks_5_80, 5)

# Function to identify unique lines of code in duplicated chunks
num_unique_dup_lines <- function(dup_chunks) {
  unique_dup_lines <- dup_chunks %>% 
    mutate(line = strsplit(code_chunk, "\n")) %>% 
    unnest(line) %>%
    select(repo_name, line) %>%
    distinct()
  unique_dup_lines %>%
    group_by(repo_name) %>%
    summarize(num_unique_dup_lines = n()) %>%
    arrange(-num_unique_dup_lines)
}

### Number of unique lines in dupicated chunks

num_unique_dup_lines_10_50 <- num_unique_dup_lines(dup_chunks_10_50)
num_unique_dup_lines_5_80 <- num_unique_dup_lines(dup_chunks_5_80)





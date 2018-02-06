rm(list=ls())

suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(httr))
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(optparse))

option_list = list(
  make_option(c("-p", "--project"), action = "store", type = 'character', help = "BigQuery project"),
  make_option(c("-r", "--repo_ds"), action = "store", type = 'character', help = "BigQuery dataset with commits table"),
  make_option(c("-l", "--lit_search_ds"), action = "store", type = 'character', help = "BigQuery dataset lit search data"),
  make_option(c("-c", "--commits"), action = "store", type = 'character', help = "BigQuery commits table"),
  make_option(c("-a", "--articles"), action = "store", type = 'character', help = "BigQuery article metadata table"),
  make_option(c("-o", "--out_ds"), action = "store", type = 'character', help = "BigQuery dataset to write genders to"),
  make_option(c("-g", "--gender_table"), action = "store", type = 'character', help = "BigQuery table to write genders to"),
  make_option(c("-k", "--key"), action = "store", type = 'character', help = "Genderize.io API key"))
opt = parse_args(OptionParser(option_list = option_list))

proj <- opt$p
ds_gh <- opt$r
ds_lit_search <- opt$l
table_commits <- opt$c
table_articles <- opt$a
genderize_api_key <- opt$k
dest_dataset <- opt$o
dest_table <- opt$g

# Get commit author and committer names from commits table
query <- paste("SELECT author_name, committer_name FROM [", 
               proj, ":", ds_gh, ".", table_commits, "] GROUP BY author_name, committer_name", 
               sep="")
raw_names_dev <- query_exec(query, project = proj, max_pages = Inf)

# Get paper author names from article metadata table
query <- paste("SELECT authors FROM [", 
               proj, ":", ds_lit_search, ".", table_articles, "]",
               sep = "")
author_lists <- query_exec(query, project = proj, max_pages = Inf)
raw_names_aut <- NULL
for(author_list in author_lists$authors) {
  authors <- sapply(author_list, function(x) trimws(unlist(strsplit(x, ";"))))
  raw_names_aut <- unname(c(raw_names_aut, authors))
}

# Function to get number of words in a string split on whitespace
num_tokens <- function(str) {
  tokens <- unlist(strsplit(str, "\\s+"))
  length(tokens)
}

# Function to get first word
first_word <- function(str) {
  tokens <- unlist(strsplit(str, "\\s+"))
  tokens[1]
}

# Clean the names
unique_names <- unique(c(raw_names_dev$author_name, raw_names_dev$committer_name, raw_names_aut))
clean_names <- unique_names[unname(sapply(unique_names, function(x) {
  nt <- num_tokens(x)
  first <- first_word(x)
  len <- nchar(first)
  nt > 1 && 
    nt < 6 && 
    nchar(first) > 1 &&
    substr(first, len, len) != "." &&
    substr(first, len, len) != ","
}))]

# Make data frame for genders
gender <- data.frame(full_name = clean_names)
gender[] <- lapply(gender, as.character)
gender$first_name <- unlist(sapply(gender$full_name, first_word))

# Function to replace special characters
mapping <- list('Š'='S', 'š'='s', 'Ž'='Z', 'ž'='z', 'À'='A', 'Á'='A', 'Â'='A', 'Ã'='A', 'Ä'='A', 'Å'='A', 
                'Æ'='A', 'Ç'='C', 'È'='E', 'É'='E', 'Ê'='E', 'Ë'='E', 'Ì'='I', 'Í'='I', 'Î'='I', 'Ï'='I', 
                'Ñ'='N', 'Ò'='O', 'Ó'='O', 'Ô'='O', 'Õ'='O', 'Ö'='O', 'Ø'='O', 'Ù'='U', 'Ú'='U', 'Û'='U', 
                'Ü'='U', 'Ý'='Y', 'Þ'='B', 'à'='a', 'á'='a', 'â'='a', 'ã'='a', 'ä'='a', 'å'='a', 
                'æ'='a', 'ç'='c', 'è'='e', 'é'='e', 'ê'='e', 'ë'='e', 'ì'='i', 'í'='i', 'î'='i', 'ï'='i', 
                'ð'='o', 'ñ'='n', 'ò'='o', 'ó'='o', 'ô'='o', 'õ'='o', 'ö'='o', 'ø'='o', 'ù'='u', 'ú'='u', 
                'û'='u', 'ý'='y', 'ý'='y', 'þ'='b', 'ÿ'='y')
from <- paste(names(mapping), collapse='')
to <- paste(mapping, collapse='')
replace_special <- function(name) {chartr(from, to, name)}

# Function to infer gender for a first name using genderize.io API
infer_gender <- function(first_name, retry = T) {
  # Send request
  url <- paste("https://api.genderize.io/?apikey=", genderize_api_key, "&name=", replace_special(first_name), sep = "")
  response <- GET(url)
  # Validate response
  if (http_error(response)) {
    # Try one more time
    if(retry) {
      Sys.sleep(15)
      infer_gender(first_name, F)
    } else {
      stop(
        sprintf(
          "API request failed [%s]: %s",
          response$status_code,
          response$url
        ),
        call. = FALSE
      )
    }
  } else {
    # Parse response
    parsed <- fromJSON(content(response, as = "text", encoding = "UTF-8"), simplifyVector = F)
    gender <- parsed$gender
    if(is.null(gender)) {
      # If first name is hyphenated, try the first two sub-parts
      tokens <- unlist(strsplit(first_name, "-"))
      if(length(tokens) > 1) {
        g1 <- infer_gender(tokens[1], T)
        g2 <- infer_gender(tokens[2], T)
        if(is.na(g1)) g2
        else if(is.na(g2)) g1
        else if(g1 == g2) g1
        else NA
      } else NA
    }
    else {
      prob <- parsed$probability
      if(prob >= 0.8) gender else NA
    }
  }
}

# Infer gender for first names
first_name_gender <- data.frame(first_name = unique(gender$first_name))
first_name_gender <- data.frame(lapply(first_name_gender, as.character), stringsAsFactors=FALSE)
inferred_gender <- unlist(apply(first_name_gender, c(1,2), infer_gender))
first_name_gender$gender <- inferred_gender

# Join gender calls to name table
gender <- gender %>% left_join(first_name_gender, by = "first_name")
gender[] <- lapply(gender, as.character)

# Write table to BigQuery
message(paste('Writing gender data to table [', proj, ':', dest_dataset, '.', dest_table, ']', sep = ''))
if (exists_table(proj, dest_dataset, dest_table)) {
  warning(paste('Overwriting existing table: [', proj, ':', dest_dataset, '.', dest_table, ']', sep = ''))
}
upload_job <- insert_upload_job(proj, dest_dataset, dest_table, values = gender, 
                                write_disposition = 'WRITE_TRUNCATE')


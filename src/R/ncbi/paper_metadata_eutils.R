rm(list=ls())

options(stringsAsFactors = F)

suppressPackageStartupMessages(library(RISmed))
suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(optparse))
suppressPackageStartupMessages(library(XML))
suppressPackageStartupMessages(library(RCurl))
suppressPackageStartupMessages(library(dplyr))

message('Getting article metadata from Eutils and uploading to BigQuery table...')

option_list = list(
  make_option(c("-p", "--project"), action = "store", type = 'character', help = "BigQuery project"),
  make_option(c("-d", "--dataset"), action = "store", type = 'character', help = "BigQuery dataset"),
  make_option(c("-i", "--in_table"), action = "store", type = 'character', help = "BigQuery table to read from"),
  make_option(c("-o", "--out_table"), action = "store", type = 'character', help = "BigQuery table to write to"))
opt = parse_args(OptionParser(option_list = option_list))

bq_project <- opt$p
bq_ds <- opt$d
bq_table_r <- opt$i
bq_table_w <- opt$o

message(paste('BigQuery project:', bq_project))
message(paste('BigQuery dataset:', bq_ds))
message(paste('BigQuery table to read:', bq_table_r))
message(paste('BigQuery table to write:', bq_table_w))

# Read repo name and minimal article info from BigQuery
metadata_by_repo <- list_tabledata(project = bq_project, dataset = bq_ds, table = bq_table_r) %>% filter(use_repo)

# Table of article data to fill in for each repo
article_data <- data.frame(num_res=NULL)

# Function to convert author list to a single string
aut_affil <- function(record) {
  ord <- order(order(Author(record)[[1]]$order))
  aut_df <- Author(record)[[1]][ord,]
  affil_vec <- unname(Affiliation(record)[[1]])[ord]
  full_name_vec <- aut_df %>%
    mutate(full_name = paste(ForeName, LastName)) %>% 
    select(full_name)
  rtrn <- NULL
  rtrn$authors <- paste(full_name_vec[[1]], collapse = "; ")
  rtrn$affiliations <- paste(affil_vec, collapse = "; ")
  rtrn
}

# Iterate through the repos
num_done <- 0
for (i in 1:nrow(metadata_by_repo)) {
  # Print progress
  num_done <<- num_done + 1
  if (num_done %% 100 == 0) {
    message(paste('Completed', num_done, 'records.'))
  }
  
  repo_name <- metadata_by_repo[i, "repo_name"]
  title <- metadata_by_repo[i, "title"]
  accession_num <- metadata_by_repo[i, "accession_num"]
  
  # Query EUtils
  # Number of results should be 1
  num_res <- 0
  # First search by uid
  if (!is.na(accession_num)) {
    query_txt <- paste(accession_num, "[uid]")
    search_query <- EUtilsSummary(query_txt)
    records <- EUtilsGet(search_query)
    num_res <- QueryCount(search_query)
  }
  if (num_res != 1) {
    # Try search by title
    query_txt <- paste(title, "[Title]")
    search_query <- EUtilsSummary(query_txt)
    records <- EUtilsGet(search_query)
    num_res <- QueryCount(search_query)
    if (num_res != 1) {
      if (num_res != 1) {
        message = paste('Skipping repo ', repo_name, '. Query returned ', num_res, ' results: ', query_txt, sep = "")
        message(message)
        warning(message)
        next
      }
    }
  }
  
  # Extract information from the record
  pmid <- PMID(records)
  nlm_unique_id <- NlmUniqueID(records)
  article_id <- ArticleId(records)
  journal <- Title(records)
  medline_ta <- MedlineTA(records)
  iso_abbrev <- ISOAbbreviation(records)
  volume <- Volume(records)
  issue <- Issue(records)
  title <- ArticleTitle(records)
  country <- Country(records)
  e_location_id <- ELocationID(records)
  author_affiliation <- aut_affil(records) # Author list and affiliations in order
  authors <- author_affiliation$authors
  affiliations <- author_affiliation$affiliations
  language <- Language(records)
  grant_id <- GrantID(records)
  agency <- Agency(records)
  acronym <- Acronym(records)
  registry_num <- RegistryNumber(records)
  pub_status <- PublicationStatus(records)
  year_received <- YearReceived(records)
  month_received <- MonthReceived(records)
  day_received <- DayReceived(records)
  year_accepted <- YearAccepted(records)
  month_accepted <- MonthAccepted(records)
  day_accepted <- DayAccepted(records)
  year_epublish <- YearEpublish(records)
  month_epublish <- MonthEpublish(records)
  day_epublish <- DayEpublish(records)
  year_ppublish <- YearPpublish(records)
  month_ppublish <- MonthPpublish(records)
  day_ppublish <- DayPpublish(records)
  year_pmc <- YearPmc(records)
  month_pmc <- MonthPmc(records)
  day_pmc <- DayPmc(records)
  year_pubmed <- YearPubmed(records)
  month_pubmed <- MonthPubmed(records)
  day_pubmed <- DayPubmed(records)
  abstract <- AbstractText(records)
  
  # Query eutils to get the number of citing articles in PMC
  url <- paste("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&linkname=pubmed_pmc_refs&id=", 
               pmid, sep="")
  page <- getURL(url)
  xml <- xmlTreeParse(page)
  xl <- xmlToList(xml)
  lsdb <- unlist(xl[which(rownames(xl) == "LinkSetDb"), which(colnames(xl) == "LinkSet")])
  cited_by_pmc <- sum(names(lsdb) == "Link.Id")
  
  # Today's date for citations
  cited_by_pmc_date <- Sys.Date()
  
  # Add the record to article data table
  article_data <- rbind(article_data, 
                        data.frame(repo_name, pmid, nlm_unique_id, article_id, journal, medline_ta,
                                   iso_abbrev, volume, issue, title, country, e_location_id, authors,
                                   affiliations, language, grant_id, agency, acronym, registry_num,
                                   pub_status, year_received, month_received, day_received,
                                   year_epublish, month_epublish, day_epublish, year_ppublish,
                                   month_ppublish, day_ppublish, year_pmc, month_pmc, day_pmc,
                                   year_pubmed, month_pubmed, day_pubmed, cited_by_pmc, 
                                   cited_by_pmc_date, abstract))
  
}


# Write the article data to a BigQuery table
message(paste('Writing article data to table [', bq_project, ':', bq_ds, '.', bq_table_w, ']', sep = ''))
if (exists_table(bq_project, bq_ds, bq_table_w)) {
  warning(paste('Overwriting existing table: [', bq_project, ':', bq_ds, '.', bq_table_w, ']', sep = ''))
}
upload_job <- insert_upload_job(bq_project, bq_ds, bq_table_w, values = article_data, 
                                write_disposition = 'WRITE_TRUNCATE')







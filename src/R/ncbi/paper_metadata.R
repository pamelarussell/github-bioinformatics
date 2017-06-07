rm(list=ls())

options(stringsAsFactors = F)

library(RISmed)
library(bigrquery)
library(optparse)
library(XML)
library(RCurl)

message('Getting article metadata and uploading to BigQuery table...')

option_list = list(
  make_option(c("-r", "--repos"), action = "store", type = 'character',
              help = "File containing list of repo names"),
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-t", "--table"), action="store", type='character', help="BigQuery table to write to"))
opt = parse_args(OptionParser(option_list=option_list))

repo_names_file <- opt$r # File of repo names
bq_project <- opt$p # Project
bq_ds <- opt$d # Dataset
bq_table <- opt$t # Comments table

message(paste('File of repo names:', repo_names_file))
message(paste('BigQuery project:', bq_project))
message(paste('BigQuery dataset:', bq_ds))
message(paste('BigQuery table:', bq_table))

# Read the repo names from file
repo_names <- read.table(repo_names_file, header = F, col.names = 'repo_name')

# Table of article data to fill in for each repo
article_data <- data.frame(num_res=NULL)

# Iterate through the repos
num_done <- 0
for(repo_name in repo_names$repo_name) {
  
  # Print progress
  num_done <<- num_done +1
  if(num_done %% 100 == 0) {
    message(paste('Completed', num_done, 'records.'))
  }
  
  # Query EUtils
  search_query <- EUtilsSummary(paste ('"github.com/', repo_name, '"[All Fields]', sep = ''))
  records <- EUtilsGet(search_query)
  query <- Query(records)
  
  # Number of results should be 1
  num_res <- QueryCount(search_query)
  if(num_res != 1) {
    message = paste('Skipping repo ', repo_name, '. Query ', query, ' returned ', num_res, ' results.')
    message(message)
    warning(message)
    next
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
  affiliation <- Affiliation(records)
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
  pmc_ids <- unlist(xl[which(rownames(xl) == "LinkSetDb"), which(colnames(xl) == "LinkSet")])
  cited_by_pmc <- length(pmc_ids)
  
  # Add the record to article data table
  article_data <- rbind(article_data, 
                        data.frame(repo_name, pmid, nlm_unique_id, article_id, journal, medline_ta,
                                   iso_abbrev, volume, issue, title, country, e_location_id,
                                   affiliation, language, grant_id, agency, acronym, registry_num,
                                   pub_status, year_received, month_received, day_received,
                                   year_epublish, month_epublish, day_epublish, year_ppublish,
                                   month_ppublish, day_ppublish, year_pmc, month_pmc, day_pmc,
                                   year_pubmed, month_pubmed, day_pubmed, cited_by_pmc, abstract))
  
}


# Write the article data to a BigQuery table
message(paste('Writing article data to table [', bq_project, ':', bq_ds, '.', bq_table, ']', sep = ''))
if(exists_table(bq_project, bq_ds, bq_table)) {
  warning(paste('Overwriting existing table: [', bq_project, ':', bq_ds, '.', bq_table, ']', sep = ''))
}
upload_job <- insert_upload_job(bq_project, bq_ds, bq_table, values = article_data, 
                  write_disposition = 'WRITE_TRUNCATE')







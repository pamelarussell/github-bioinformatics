
library(RISmed)
library(bigrquery)
library(optparse)
library(XML)
library(RCurl)
library(dplyr)
options(stringsAsFactors = F)

setwd("~/Documents/Github_mining/src/R/document_classification")
bq_project <- "github-bioinformatics-171721"
bq_ds <- "classification"
bq_table_mc <- "abstracts_to_classify_manually"
bq_table_gs <- "abstracts_gold_standard"

# If abstracts to classify have not already been pulled from PubMed and pushed to a BigQuery table, do that now
if(!exists_table(bq_project, bq_ds, bq_table_mc)) {
  # Query PubMed title/abstract for "github"
  search_query <- EUtilsSummary("github[Title/Abstract]")
  records <- EUtilsGet(search_query)
  query <- Query(records)
  num_res <- QueryCount(search_query)
  
  # Save the query results in a data frame
  results <- data.frame(pmid = PMID(records), title = ArticleTitle(records), abstract = AbstractText(records))
  
  # Write the query results to a BigQuery table
  upload_job <- insert_upload_job(bq_project, bq_ds, bq_table_mc, values = results, 
                                  write_disposition = 'WRITE_EMPTY')
  wait_for(upload_job)
}

# Read the abstracts to classify from the BigQuery table
abstracts_to_classify <- list_tabledata(project = bq_project, dataset = bq_ds, table = bq_table_mc)

# Get the current classification table from BigQuery
curr_table <- tryCatch({
  list_tabledata(project = bq_project, dataset = bq_ds, table = bq_table_gs)
}, error = function(e) {
  data.frame(bioinf = character(), pmid = character(), title = character(), abstract = character())
})

# Identify papers that have not already been classified
remaining_to_classify <- anti_join(abstracts_to_classify, curr_table, by = "pmid")
num_remaining_to_classify <- nrow(remaining_to_classify)

# Create a random order to look at remaining abstracts in
rand_ord <- sample(num_remaining_to_classify, num_remaining_to_classify, FALSE)

# Function to display text and get input from the console
get_answer <- function(row_num) {
  title <- remaining_to_classify[row_num, "title"]
  abstract <- remaining_to_classify[row_num, "abstract"]
  pmid <- remaining_to_classify[row_num, "pmid"]
  print("")
  print("")
  print(as.character(title))
  print("")
  print(as.character(abstract))
  print("")
  print("Is this bioinformatics (y/n)? If record is incomplete, type 'skip'. If done, type 'done'.")
  print("")
  answer <- readline()
  if(tolower(answer) == "y") data.frame(bioinf = "1", pmid = pmid, title = title, abstract = abstract)
  else if(tolower(answer) == "n") data.frame(bioinf = "0", pmid = pmid, title = title, abstract = abstract)
  else if(tolower(answer) == "done") "done"
  else if(tolower(answer) == "skip") "skip"
  else {
    print(paste("Invalid response: ", answer, ". Try again.", sep=""))
    get_answer(row_num)
  }
}

answers <- data.frame()
ans <- "na"

# Ask for the answers
for (i in 1:num_remaining_to_classify) {
  ans <- get_answer(rand_ord[i])
  if(ans[1] %in% c("0", "1")) {
    answers <- rbind(answers, ans)
  } else if(ans[1] == "skip") {
    next
  } else if(ans[1] == "done") {
    break
  } else {
    stop(paste("Invalid response:", ans))
  }
}

# Push the answers to BigQuery
if(nrow(answers) > 0) {
  upload_job <- insert_upload_job(bq_project, bq_ds, bq_table_gs, values = answers, 
                                  write_disposition = 'WRITE_APPEND')
  wait_for(upload_job)
}




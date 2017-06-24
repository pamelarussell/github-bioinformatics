
library(RISmed)
library(bigrquery)
library(optparse)
library(XML)
library(RCurl)
library(dplyr)
options(stringsAsFactors = F)

bq_project <- "github-bioinformatics-157418"
bq_ds <- "test_repos_analysis_results"
bq_table <- "manual_abstract_classification"

# Query PubMed title/abstract for "github"
search_query <- EUtilsSummary("github[Title/Abstract]")
records <- EUtilsGet(search_query)
query <- Query(records)
num_res <- QueryCount(search_query)

# Save the query results in a data frame
results <- data.frame(pmid = PMID(records), title = ArticleTitle(records), abstract = AbstractText(records))

# Get the current classification table from BigQuery
curr_table <- list_tabledata(project = bq_project, dataset = bq_ds, table = bq_table)

# Identify paper results that are not in the current table
missing_results <- anti_join(results, curr_table, by = "pmid")
num_missing_res <- nrow(missing_results)

# Create a random order to look at abstracts in
rand_ord <- sample(num_missing_res, num_missing_res, FALSE)

# Function to display text and get input from the console
get_answer <- function(row_num) {
  title <- missing_results[row_num, "title"]
  abstract <- missing_results[row_num, "abstract"]
  pmid <- missing_results[row_num, "pmid"]
  print("")
  print("")
  print(as.character(title))
  print("")
  print(as.character(abstract))
  print("")
  print("Is this a bioinformatics tool (y/n)? If done, type 'done'.")
  print("")
  answer <- readline()
  if(tolower(answer) == "y") data.frame(bioinf_tool = "1", pmid = pmid, title = title, abstract = abstract)
  else if(tolower(answer) == "n") data.frame(bioinf_tool = "0", pmid = pmid, title = title, abstract = abstract)
  else if(tolower(answer) == "done") "done"
  else {
    print(paste("Invalid response: ", answer, ". Try again.", sep=""))
    get_answer(row_num)
  }
}

answers <- data.frame()
ans <- "na"

# Ask for the answers
for (i in 1:num_missing_res) {
  ans <- get_answer(i)
  if(ans[1] != "done") {
    answers <- rbind(answers, ans)
  } else break
}

# Push the answers to BigQuery
upload_job <- insert_upload_job(bq_project, bq_ds, bq_table, values = answers, 
                                write_disposition = 'WRITE_APPEND')




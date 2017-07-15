rm(list=ls())
library("googlesheets")
suppressPackageStartupMessages(library("dplyr"))
library(RISmed)
library(tidytext)
library(tm)

get_abstract <- function(pmid_search_term) {
  query <- EUtilsSummary(pmid_search_term)
  if(QueryCount(query) != 1) {stop(paste("More than one record found for", pmid_search_term))}
  records <- EUtilsGet(query)
  AbstractText(records)
}

pmid_from_search_term <- function(search_term) {
  unlist(strsplit(search_term, "[", fixed = T))[1]
}

sheet <- gs_title("Abstract classification gold standard")
gs_data <- gs_read(sheet, ws = "Manual classification") %>%
  filter(Bioinformatics %in% c(0,1))
gs_data$PMID <- unlist(lapply(gs_data$`PubMed search term`, pmid_from_search_term))
gs_data$Abstract <- unlist(lapply(gs_data$`PubMed search term`, get_abstract))

gs_tidy <- gs_data %>% 
  select(PMID, Bioinformatics, Abstract) %>%
  unnest_tokens(Word, Abstract) %>%
  mutate(Stem = stemDocument(Word)) %>%
  count(Bioinformatics, Stem, sort = T) %>%
  ungroup() %>%
  bind_tf_idf(Stem, Bioinformatics, n) %>%
  arrange(desc(tf_idf))




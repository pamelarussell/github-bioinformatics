rm(list=ls())
suppressPackageStartupMessages(library(googlesheets))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(RISmed))
suppressPackageStartupMessages(library(tidytext))
suppressPackageStartupMessages(library(tm))
suppressPackageStartupMessages(library(caret))
suppressPackageStartupMessages(library(e1071))
suppressPackageStartupMessages(library(purrr))

# Get abstract for one paper
get_abstract <- function(pmid_search_term) {
  tryCatch({
    query <- EUtilsSummary(pmid_search_term)
    if(QueryCount(query) != 1) {stop(paste("More than one record found for", pmid_search_term))}
    records <- EUtilsGet(query)
    AbstractText(records)
  }, error = function(e) {
    NA
  })
}

# Get PMID from search term
pmid_from_search_term <- function(search_term) {
  unlist(strsplit(search_term, "[", fixed = T))[1]
}

# Gold standard Google spreadsheet
sheet <- gs_title("Abstract classification gold standard")

# Read gold standard data from the spreadsheet
data_all <- gs_read(sheet, ws = "Manual classification") %>%
  filter(Bioinformatics %in% c(0,1))
data_all$Bioinformatics <- factor(sapply(as.logical(as.integer(data_all$Bioinformatics)), function(x) if(x) "bioinf" else "not_bioinf"))

# Parse out the PMID
data_all$PMID <- unlist(lapply(data_all$`PubMed search term`, pmid_from_search_term))

# Get the abstracts from PubMed
data_all$Abstract <- unlist(lapply(data_all$`PubMed search term`, get_abstract))

# Make a corpus
corpus_all <- Corpus(VectorSource(data_all$Abstract)) %>%
  tm_map(content_transformer(tolower)) %>%
  tm_map(removeNumbers) %>%
  tm_map(removeWords, stopwords(kind="en")) %>%
  tm_map(removePunctuation) %>%
  tm_map(stripWhitespace)
dtm_all <- DocumentTermMatrix(corpus_all)

# Split into training and test sets
set.seed(1614)
train_idx <- createDataPartition(data_all$Bioinformatics, p = 0.75, list = F)
data_test <- data_all[-train_idx,]
data_train <- data_all[train_idx,]

# Tidy the data
data_train_tidy <- data_train %>%
  dplyr::select(PMID, Bioinformatics, Abstract) %>%
  unnest_tokens(Token, Abstract) %>%
  mutate(Stem = stemDocument(Token))

# Perform tf-idf on abstract text
tf_idf_train <- data_train_tidy %>%
  dplyr::count(Bioinformatics, Stem, sort = T) %>%
  ungroup() %>%
  bind_tf_idf(Stem, Bioinformatics, n) %>%
  arrange(desc(tf_idf))

# Get the top tf-idf tokens
top_tokens <- function(is_bioinf, n) {
  top_tokens <- tf_idf_train %>%
    filter(Bioinformatics == is_bioinf) %>%
    top_n(n, tf_idf) %>%
    dplyr::select(Stem)
  top_tokens[[1]]
}

# Classification function
num_top_tokens <- 10
predict_tfidf <- function(abstract) {
  unique_stems <- unique(unlist(strsplit(stemDocument(abstract), "\\s+")))
  top_pos_tokens <- top_tokens(T, num_top_tokens)
  top_neg_tokens <- top_tokens(F, num_top_tokens)
  every(top_neg_tokens, function(x) !(x %in% unique_stems)) || some(top_pos_tokens, function(x) x %in% unique_stems)
}

# Evaluate tf-idf classifier
conf_matrix_tfidf <- function(data) {
  pred <- sapply(data$Abstract, predict_tfidf)
  confusionMatrix(data = pred, reference = data$Bioinformatics)
}

accuracy <- function(conf_matrix) {
  conf_matrix$overall["Accuracy"]
}

conf_matrix_train <- conf_matrix_tfidf(data_train)
message(paste("tf-idf classifier: training set accuracy:", accuracy(conf_matrix_train)))









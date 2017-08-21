rm(list=ls())
suppressPackageStartupMessages(library(googlesheets))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(RISmed))
suppressPackageStartupMessages(library(tidytext))
suppressPackageStartupMessages(library(tm))
suppressPackageStartupMessages(library(caret))
suppressPackageStartupMessages(library(e1071))
suppressPackageStartupMessages(library(purrr))

##
## Functions to work with PubMed data
##

# Function to get abstract for one paper
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

# Function to get PMID from search term
pmid_from_search_term <- function(search_term) {
  unlist(strsplit(search_term, "[", fixed = T))[1]
}

##
## Load the gold standard data
##

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

##
## Build the test and training sets
##

# Split into training and test sets
set.seed(1614)
train_idx <- createDataPartition(data_all$Bioinformatics, p = 0.75, list = F)
data_test <- data_all[-train_idx,]
data_train <- data_all[train_idx,]

# Make corpora
corpus_test <- corpus_all[-train_idx]
corpus_train <- corpus_all[train_idx]
dtm_test <- dtm_all[-train_idx,]
dtm_train <- dtm_all[train_idx,]

# Identify terms that appear a minimum number of times in training corpus
dict <- findFreqTerms(dtm_train, lowfreq = 10)
train <- DocumentTermMatrix(corpus_train, list(dictionary = dict))
test <- DocumentTermMatrix(corpus_test, list(dictionary = dict))

# Convert numeric entries in dtm into factor indicating presence/absence
convert_counts <- function(x) {
  x <- ifelse(x > 0, 1, 0)
  x <- factor(x, levels = c(0, 1), labels = c("Absent", "Present"))
}
train <- train %>% apply(MARGIN=2, FUN=convert_counts)
test <- test %>% apply(MARGIN=2, FUN=convert_counts)

##
## Train Naive Bayes model
##

# Train the model
model_nb <- train(train, data_train$Bioinformatics, method = "nb", metric = "Accuracy", trControl = trainControl(method="cv", 10))

# Use the model to predict the classification on the test set
predict_nb_test <- predict(model_nb, test)
cm_nb_test <- confusionMatrix(predict_nb_test, data_test$Bioinformatics, positive="bioinf")
predict_nb_train <- predict(model_nb, train)
cm_nb_train <- confusionMatrix(predict_nb_train, data_train$Bioinformatics, positive="bioinf")

##
## tf-idf based classifier
##

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
    filter(if(is_bioinf) Bioinformatics == "bioinf" else Bioinformatics == "not_bioinf") %>%
    top_n(n, tf_idf) %>%
    dplyr::select(Stem)
  top_tokens[[1]]
}

# Classification function
top_pos_tokens <- top_tokens(T, 50)
top_neg_tokens <- top_tokens(F, 5)
predict_tfidf <- function(abstract) {
  unique_stems <- unique(unlist(strsplit(stemDocument(abstract), "\\s+")))
  # neg_ok <- every(top_neg_tokens, function(x) !(x %in% unique_stems))
  neg_ok <- sum(sapply(top_neg_tokens, function(x) x %in% unique_stems)) < 2
  pos_ok <- some(top_pos_tokens, function(x) x %in% unique_stems)
  # pos_ok <- sum(sapply(top_pos_tokens, function(x) x %in% unique_stems)) > 1
  b <- neg_ok && pos_ok
  if(b) factor("bioinf") else factor("not_bioinf")
}

# Evaluate tf-idf classifier
cm_tfidf <- function(data) {
  pred <- factor(sapply(data$Abstract, predict_tfidf), levels = c("bioinf", "not_bioinf"))
  confusionMatrix(data = pred, reference = data$Bioinformatics)
}

accuracy <- function(conf_matrix) {
  conf_matrix$overall["Accuracy"]
}

cm_tfidf_train <- conf_matrix_tfidf(data_train)
cm_tfidf_test <- conf_matrix_tfidf(data_test)

rm(data_train_tidy, test, train, train_idx, corpus_all, corpus_test, corpus_train, dict)


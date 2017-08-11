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
dict <- findFreqTerms(dtm_train, lowfreq = 20)
train <- DocumentTermMatrix(corpus_train, list(dictionary = dict))
test <- DocumentTermMatrix(corpus_test, list(dictionary = dict))

# Convert numeric entries in dtm into factor indicating presence/absence
convert_counts <- function(x) {
  x <- ifelse(x > 0, 1, 0)
  x <- factor(x, levels = c(0, 1), labels = c("Absent", "Present"))
}
train <- train %>% apply(MARGIN=2, FUN=convert_counts)
test <- test %>% apply(MARGIN=2, FUN=convert_counts)

# Train the model
model <- train(train, data_train$Bioinformatics, method = "nb", metric = "Accuracy", trControl = trainControl(method="cv", 10))

# Use the model to predict the classification on the test set
predict <- predict(model, test)
cm <- confusionMatrix(predict, data_test$Bioinformatics, positive="bioinf")




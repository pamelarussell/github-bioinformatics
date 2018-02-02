suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(tidytext))
suppressPackageStartupMessages(library(tm))
suppressPackageStartupMessages(library(topicmodels))
suppressPackageStartupMessages(library(tidyr))
suppressPackageStartupMessages(library(reshape2))
source("~/Dropbox/Documents/Github_mining/src/R/project_info.R")

# Import article metadata
article_data <- list_tabledata(project = proj, dataset = ds_lit_search, 
                               table = table_repo_and_article, max_pages = Inf) %>%
  filter(use_repo) %>% 
  mutate(journal = gsub("\\.", "", tolower(journal)))

# Map of journal to ISO abbreviation
journal_to_iso_abbrev <- list_tabledata(project = proj, dataset = ds_lit_search, 
                                        table = table_article_metadata, max_pages = Inf) %>%
  select(journal, iso_abbrev) %>%
  mutate(journal = gsub("\\.", "", tolower(journal)), iso_abbrev = gsub("\\.", "", tolower(iso_abbrev))) %>%
  unique()

# Also include the ISO abbreviation as a possible key
iso_to_iso <- journal_to_iso_abbrev %>% 
  mutate(x = iso_abbrev) %>% 
  select(iso_abbrev, x) %>% 
  rename(journal = iso_abbrev, iso_abbrev = x)

journal_to_iso_abbrev <- unique(rbind(journal_to_iso_abbrev, iso_to_iso))

# Add ISO abbrev to article_data
article_data <- article_data %>% left_join(journal_to_iso_abbrev, by = "journal")

# Make document term matrix
dtm <- article_data %>% 
  select(repo_name, abstract) %>% 
  unnest_tokens(word, abstract) %>%
  anti_join(stop_words) %>%
  count(repo_name, word, sort = TRUE) %>%
  ungroup() %>%
  cast_dtm(repo_name, word, n)

# Run latent dirichlet allocation
lda <- LDA(dtm, k = 8, control = list(seed = 1614))
topics <- tidy(lda, matrix = "beta") %>%
  mutate(topic = paste0("topic", topic))

# Terms that are highly associated with a single topic
topics_specialized <- topics %>% 
  group_by(term) %>% 
  mutate(max_beta = max(beta), second_beta = beta[order(beta, decreasing = T)][2]) %>% 
  filter(beta == max_beta & log2(beta / second_beta) > 2) %>% 
  select(topic, term, beta)

# Classify abstracts
abstract_top_topics <- tidy(lda, matrix = "gamma") %>% 
  mutate(topic = paste0("topic", topic)) %>%
  rename(repo_name = document) %>%
  group_by(repo_name) %>%
  filter(gamma > 0.25)

# Clean up
rm(iso_to_iso, journal_to_iso_abbrev, lda, dtm)







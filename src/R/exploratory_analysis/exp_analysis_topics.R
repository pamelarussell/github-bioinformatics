suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(tidytext))
suppressPackageStartupMessages(library(tm))
suppressPackageStartupMessages(library(topicmodels))
suppressPackageStartupMessages(library(tidyr))
source("~/Dropbox/Documents/Github_mining/src/R/exploratory_analysis/project_info.R")

# Import article metadata
article_data <- list_tabledata(project = proj, dataset = ds_lit_search, 
                               table = table_repo_and_article, max_pages = Inf) %>%
  filter(use_repo)

# Make document term matrix
dtm <- article_data %>% 
  select(repo_name, abstract) %>% 
  unnest_tokens(word, abstract) %>%
  anti_join(stop_words) %>%
  count(repo_name, word, sort = TRUE) %>%
  ungroup() %>%
  cast_dtm(repo_name, word, n)

# Run latent dirichlet allocation
lda <- LDA(dtm, k = 10, control = list(seed = 1614))
topics <- tidy(lda, matrix = "beta") %>%
  mutate(topic = paste0("topic", topic))

# Function to plot top terms
plot_top_terms <- function(topics) {
  top_terms <- topics %>%
    group_by(topic) %>%
    top_n(10, beta) %>%
    ungroup() %>%
    arrange(topic, -beta)
  
  top_terms %>%
    mutate(term = reorder(term, beta)) %>%
    ggplot(aes(term, beta, fill = factor(topic))) +
    geom_col(show.legend = FALSE) +
    facet_wrap(~ topic, scales = "free") +
    coord_flip()
}

# Terms that are highly associated with a single topic
topics_specialized <- topics %>% 
  group_by(term) %>% 
  mutate(max_beta = max(beta), second_beta = beta[order(beta, decreasing = T)][2]) %>% 
  filter(beta == max_beta & log2(beta / second_beta) > 2) %>% 
  select(topic, term, beta)

# Make plots
plot_top_terms(topics)
plot_top_terms(topics_specialized)

# Classify abstracts
abstract_top_topics <- tidy(lda, matrix = "gamma") %>% 
  rename(repo_name = document) %>%
  group_by(repo_name) %>%
  filter(gamma > 0.25)

# Count number of repos associated with each topic
num_repos_per_topic <- abstract_top_topics %>% 
  group_by(topic) %>% 
  summarize(total = n()) %>%
  arrange(-total)

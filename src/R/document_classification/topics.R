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
  select(topic, term, beta) %>%
  ungroup()

# Classify abstracts
abstract_top_topics <- tidy(lda, matrix = "gamma") %>% 
  mutate(topic = paste0("topic", topic)) %>%
  rename(repo_name = document) %>%
  group_by(repo_name) %>%
  filter(gamma > 0.25) %>%
  ungroup()

# Get top terms for each topic
top_terms <- topics_specialized %>%
  group_by(topic) %>%
  top_n(10, beta) %>%
  ungroup() %>%
  arrange(topic, -beta)

# Give the topics meaningful names
# Make sure the results are what we think before assigning names
terms_by_topic_num <- list(
  "topic1" = c("cancer", "drug", "type", "chromatin", "patients", "heterogeneity", "subtypes", "predictive", "breast", "epigenetic"),
  "topic2" = c("ms", "proteomics", "mass", "pride", "peptide", "spectrometry", "resolution", "microscopy", "peptides", "images"),
  "topic3" = c("variant", "ngs", "calling", "copy", "somatic", "illumina", "sv", "insertions", "calls", "exome"),
  "topic4" = c("genotype", "populations", "markers", "posterior", "rare", "scaffolding", "formula", "uncertainty", "variance", "controls"),
  "topic5" = c("metabolic", "domains", "residues", "translation", "supertree", "conformational", "pymol", "ppi", "homology", "sampled"),
  "topic6" = c("web", "interface", "application", "access", "researchers", "interactive", "ontology", "api", "browser", "graphical"),
  "topic7" = c("graph", "motifs", "tf", "bruijn", "motif", "mers", "synteny", "partitioning", "tfs", "draft"),
  "topic8" = c("rna", "seq", "transcript", "transcripts", "transcriptome", "rrna", "splicing", "mirna", "microbiome", "16s"))
for(i in 1:length(terms_by_topic_num)) {
  if(!all(top_terms %>% filter(topic == names(terms_by_topic_num)[i]) %>% select(term) == terms_by_topic_num[i])) {
    stop("Topic terms don't match expectation from previous analysis")
  }
}
rm(i)
# Assign a name to each topic
topic_translation <- list("topic1" = "Cancer and epigenetics",
                          "topic2" = "Proteomics and microscopy",
                          "topic3" = "Variant calling",
                          "topic4" = "Genetics and population analysis",
                          "topic5" = "Structure and molecular interaction",
                          "topic6" = "Web and graphical applications",
                          "topic7" = "Assembly and sequence analysis",
                          "topic8" = "Transcription and RNA-seq")
rm(terms_by_topic_num)

# Function to rename data in "topic" column of data frame
rename_topic <- function(data) {
  rtrn <- data
  rtrn$topic <- sapply(rtrn$topic, function(x) topic_translation[[x]])
  rtrn
}
top_terms <- rename_topic(top_terms)
abstract_top_topics <- rename_topic(abstract_top_topics)
topics <- rename_topic(topics)
topics_specialized <- rename_topic(topics_specialized)

# Count number of repos associated with each topic
num_repos_per_topic <- abstract_top_topics %>% 
  group_by(topic) %>% 
  dplyr::summarize(total = n()) %>%
  arrange(-total) %>%
  ungroup()

# Clean up
rm(iso_to_iso, journal_to_iso_abbrev, lda, dtm)







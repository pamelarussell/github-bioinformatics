# Calculate tf-idf for article abstracts
# Each "document" corresponds to one programming language and is
# all the abstracts for repos that have any code in that language,
# according to the "languages" table in the GitHub BigQuery dataset

rm(list=ls())

suppressWarnings(library(bigrquery))
suppressWarnings(library(optparse))
suppressWarnings(library(dplyr))
suppressWarnings(library(tidytext))
suppressWarnings(library(tidyr))
suppressWarnings(library(ggplot2))
suppressWarnings(library(hunspell))
suppressWarnings(library(scales))
suppressWarnings(library(gridExtra))
suppressWarnings(library(grid))
suppressWarnings(library(tm))

message('Calculating overrepresented words in article abstracts by programming language...')

# Command line options
option_list = list(
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-a", "--articles_table"), action="store", type='character', 
              help="BigQuery articles table"),
  make_option(c("-l", "--languages_table"), action="store", type='character', 
              help="BigQuery languages table"),
  make_option(c("-o", "--output"), action="store", type='character', help="Output pdf prefix")
)
opt = parse_args(OptionParser(option_list=option_list))

# Get command line arguments
proj <- opt$p # Project
ds <- opt$d # Dataset
tab_art <- opt$a # Articles table
tab_lang <- opt$l # Languages table
out_pdf_prefix <- opt$o # Output pdf

message(paste('BigQuery project:', proj))
message(paste('BigQuery dataset:', ds))
message(paste('BigQuery articles table:', tab_art))
message(paste('BigQuery languages table:', tab_lang))
message(paste('Output figure:', out_pdf_prefix))

# Query to join language to articles table
query <- paste('
                SELECT
                  repo_name,
                  language_name,
                  abstract
                FROM
                  [', proj, ':', ds, '.', tab_art, '] AS abstracts
                INNER JOIN (
                  SELECT
                    repo_name AS lang_repo_name,
                    language_name
                  FROM
                    [', proj, ':', ds, '.', tab_lang, ']) AS languages
                ON
                  abstracts.repo_name = lang_repo_name
                GROUP BY
                  repo_name,
                  language_name,
                  abstract
                ORDER BY
                  repo_name               
               ', sep = '')

# Run query
query_res <- query_exec(query, project = proj, max_pages = Inf)

# Function to get tf-idf by language
# ngram_n: N for ngrams (1 if single words)
# Filter_spellcheck: filter tokens with spellchecker
language_words_tfidf <- function(ngram_n, filter_spellcheck) {
  
  tokens <- query_res %>%
    select(language_name, abstract) %>%
    # Remove non-meaningful "languages"
    filter(language_name != 'HTML' & language_name != 'CSS' & language_name != 'Makefile' &
             language_name != 'TeX') %>%
    # Count number of abstracts per language
    group_by(language_name) %>%
    mutate(num_abstracts_for_lang = n()) %>%
    # Remove languages with too few abstracts
    filter(num_abstracts_for_lang > 25) %>%
    # Unnest tokens
    unnest_tokens(word, abstract, token = 'ngrams', n = ngram_n) %>%
    # Count number of times the word appears
    group_by(word, language_name) %>%
    mutate(n_word = n())
  
  # Remove words that don't pass spell checker
  if(filter_spellcheck) {
    tokens <- filter(tokens, hunspell_check(word))
  }
  
  # Stem
  tokens <- mutate(tokens, stem = stemDocument(word))
  #tokens <- mutate(tokens, stem = word) # This removes stemming
  
  # tf-idf by stem
  tfidf_stem <- tokens %>% 
    # Count number of times each stem occurs by language
    count(language_name, stem, sort = T) %>%
    ungroup() %>%
    # Add tf-idf
    bind_tf_idf(stem, language_name, n)
  
  # Join to tokens
  tokens <- left_join(tokens, tfidf_stem)
  
  # Reduce each stem to its most common word representative
  tokens <- tokens %>% 
    group_by(language_name, stem) %>% 
    slice(which.max(n_word)) %>%
    ungroup() %>%
    # Sort by tf-idf
    arrange(desc(tf_idf)) %>%
    # Convert to factors
    mutate(word = factor(word, levels = rev(unique(word)))) %>%
    mutate(language_name = factor(language_name, levels = sort(unique(language_name))))
  
  tokens
  
}


# Function to make a plot for one language
# top_tf_idf: output of top_words_tf_idf
# ngram_n: N for ngrams (1 if single words)
# filter_spellcheck: filter tokens with spellchecker
# lang: language
# axis_lim: Max axis value for plot
# num_top: Number of top words to get for the language
mk_plt <- function(top_tf_idf, ngram_n, filter_spellcheck, lang, axis_lim, num_top) {
  
  # Get data for this language
  lang_data <- top_tf_idf %>% 
    filter(language_name == lang) %>%
    # Get top n words
    # Returns more if there are ties
    top_n(num_top) %>%
    # Sort in descending order
    arrange(desc(tf_idf))
  
  # Make the plot
  ggplot(data = lang_data, aes(x = reorder(word, tf_idf), y = tf_idf)) +
    geom_col(fill = 'steelblue') +
    labs(title = lang, x = NULL, y = NULL) +
    scale_y_continuous(labels = comma, limits = c(0, axis_lim),
                       breaks = function(lims) {pretty(lims, 3)}) +
    theme(legend.position="none",
          axis.text.x = element_text(size = 14),
          axis.text.y = element_text(size = 14),
          plot.title = element_text(hjust = 0.5, size = 24)) + 
    coord_flip()
  
}

# Function to make plot for all languages
# ngram_n: N for ngrams (1 if single words)
# filter_spellcheck: filter tokens with spellchecker
# axis_lim: Max axis value for plot
# num_top: Number of top words to get for the language
mk_plt_all_langs <- function(ngram_n, filter_spellcheck, axis_lim, num_top) {
  # Open pdf device
  pdf(paste(out_pdf_prefix, '_', ngram_n, '.pdf', sep=''), width=17, height=17)
  # Get the data to plot
  top_tf_idf <- language_words_tfidf(ngram_n, filter_spellcheck)
  # Make a plot for each language
  plots <- lapply(sort(unique(top_tf_idf$language_name)), function(x) {
    mk_plt(top_tf_idf, ngram_n, filter_spellcheck, x, axis_lim, num_top)})
  # Arrange all the plots in a grid
  grid.arrange(grobs = plots, ncol = 3, top=textGrob("Top scoring tokens within abstracts by tf-idf", 
                                                     gp=gpar(fontsize=28, font = 8)))
  dev.off()
}

# Generate the plots for various n-grams
mk_plt_all_langs(1, T, 0.0025, 10)
mk_plt_all_langs(2, F, 0.0025, 10)
mk_plt_all_langs(3, F, 0.0025, 10)
mk_plt_all_langs(4, F, 0.0025, 10)


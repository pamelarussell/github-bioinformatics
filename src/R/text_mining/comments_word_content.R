rm(list=ls())

library(bigrquery)
library(optparse)
library(dplyr)
library(tidytext)
library(tidyr)
library(ggplot2)
library(hunspell)
library(scales)
library(gridExtra)
library(grid)

message('Calculating overrepresented words in comments by programming language...')

option_list = list(
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-c", "--comments_table"), action="store", type='character', 
              help="BigQuery comments table"),
  make_option(c("-l", "--lines_of_code_table"), action="store", type='character', 
              help="BigQuery lines of code table"),
  make_option(c("-o", "--output"), action="store", type='character', help="Output pdf")
)
opt = parse_args(OptionParser(option_list=option_list))

proj <- opt$p # Project
ds <- opt$d # Dataset
tab_com <- opt$c # Comments table
tab_loc <- opt$l # Lines of code table
out_pdf <- opt$o # Output pdf

message(paste('BigQuery project:', proj))
message(paste('BigQuery dataset:', ds))
message(paste('BigQuery comments table:', tab_com))
message(paste('BigQuery lines of code table:', tab_loc))
message(paste('Output figure:', out_pdf))

# Query to add language to comments table
query <- paste('
                  SELECT id, [language], comments
                  FROM
                  [', proj, ':', ds, '.', tab_com, '] AS comments
                  INNER JOIN (
                  SELECT id AS loc_id, [language] 
                  FROM [', proj, ':', ds, '.', tab_loc, ']) AS lines_of_code
                  ON comments.id = loc_id
                  GROUP BY id, [language], comments', 
               sep = '')

# Run query
query_res <- query_exec(query, project = proj, max_pages = Inf)

# tf-idf by language
language_words <- query_res %>%
  filter(language == 'R' | language == 'Java' | language == 'Perl' |
           language == 'MATLAB' | language == 'C' | language == 'Scala') %>%
  unnest_tokens(word, comments) %>%
  filter(hunspell_check(word)) %>%
  count(language, word, sort = T) %>%
  ungroup() %>%
  bind_tf_idf(word, language, n) %>%
  arrange(desc(tf_idf))

# Top words by tf-idf
top_tf_idf <- language_words %>%
  mutate(word = factor(word, levels = rev(unique(word)))) %>%
  mutate(language = factor(language, levels = sort(unique(language))))
  
# Function to make a plot for one language
mk_plt <- function(lang) {
  
  lang_data <- top_tf_idf %>% 
    filter(language == lang) %>%
    top_n(10) %>%
    arrange(desc(tf_idf))
  
  ggplot(data = lang_data, aes(x = reorder(word, tf_idf), y = tf_idf)) +
    geom_col(fill = 'steelblue') +
    labs(title = lang, x = NULL, y = NULL) +
    scale_y_continuous(labels = comma, limits = c(0, 0.006)) +
    theme(legend.position="none",
          axis.text = element_text(size = 14),
          plot.title = element_text(hjust = 0.5, size = 24)) + 
    coord_flip()
  
}

# Make plot for all languages
pdf(out_pdf, width=11, height=8.5)
plots <- lapply(sort(unique(top_tf_idf$language)), mk_plt)
grid.arrange(grobs = plots, ncol = 3, 
             top=textGrob("Top scoring words within comments by tf-idf", 
                          gp=gpar(fontsize=28, font = 8)))
dev.off()



  


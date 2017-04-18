rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)
library(optparse)

message('Calculating number of repos by pair of languages...')

option_list = list(
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-b", "--table_lang_bytes"), action="store", type='character', help="BigQuery table: bytes by language"),
  make_option(c("-l", "--table_lang_list_by_repo"), action="store", type='character', help="BigQuery table: language list by repo"),
  make_option(c("-o", "--output"), action="store", type='character', help="Output pdf")
)
opt = parse_args(OptionParser(option_list=option_list))

proj <- opt$p # Project
ds <- opt$d # Dataset
tabb <- opt$table_lang_bytes # Table of bytes by language
tabl <- opt$table_lang_list_by_repo # Table of language list by repo
pdf <- opt$o # Output pdf

message(paste('BigQuery project:', proj))
message(paste('BigQuery dataset:', ds))
message(paste('BigQuery table of bytes by language:', tabb))
message(paste('BigQuery table of language list by repo:', tabl))
message(paste('Output figure:', pdf))

# Access data on Bigquery
lang_bytes <- list_tabledata(project = proj, dataset = ds, table = tabb)
lang_by_repo <- list_tabledata(project = proj, dataset = ds, table = tabl)

# Identify languages
lang <- sort(lang_bytes$language_name)
nlang <- length(lang)
npair <- nlang * (nlang - 1) / 2

mkPair <- function(l1, l2) {
  paste(l1, l2, sep=", ")
}

# Make list of all possible language pairs
all_pairs <- apply(expand.grid(lang, lang), 1, function(x) {
      l1 <- as.character(x[1])
      l2 <- as.character(x[2])
      if(l1 < l2) {
        mkPair(l1, l2)
      }
      else NA
})
all_pairs <- all_pairs[which(!is.na(all_pairs))]

# Empty data frame of pair counts
pair_count <- data.frame(matrix(0, nrow = npair, ncol = 1), row.names = all_pairs)

# Function to update pair counts based on language list for one repo
update_pair_count <- function(cslist) {
  l <- unlist(strsplit(cslist, ',', fixed = T))
  l <- l[which(!is.na(l))]
  apply(expand.grid(l, l), 1, function(x) {
    l1 <- as.character(x[1])
    l2 <- as.character(x[2])
    if(l1 < l2) {
      pair_count[mkPair(l1, l2), 1] <<- pair_count[mkPair(l1, l2), 1] + 1
    }
  })
}

# Update the pair counts for all repos
x <- lapply(lang_by_repo$languages, update_pair_count)
rm(x)

# Sort pairs by number of repos
ord <- order(pair_count[,1], decreasing = T)
rn <- rownames(pair_count)
pair_count = data.frame(pair_count[order(pair_count[,1], decreasing = T),], row.names = rn[ord])
colnames(pair_count) <- c("numRepos")

# Get the top pairs
num_top_pairs <- 30
top_pairs <- pair_count[1:num_top_pairs,]
names(top_pairs) <- rownames(pair_count)[1:num_top_pairs]
top_pairs <- top_pairs[order(top_pairs)]

# Make barplot
pdf(pdf, height=8.5, width=11)
par(mar=c(5,12,4,2))
bp <- barplot(
  t(as.matrix(top_pairs)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main=paste("Number of repos including both languages (N=", nrow(lang_by_repo), ")", sep=""),
  cex.names = 0.9,
  xlim=c(0, max(top_pairs) + 20)
)
text(x=top_pairs, y=bp, label=top_pairs, pos = 4, cex=0.9)
invisible(dev.off())




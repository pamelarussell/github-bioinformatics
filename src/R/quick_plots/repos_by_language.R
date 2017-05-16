rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)
library(optparse)

message('Calculating number of repos by programming language...')

option_list = list(
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-c", "--table_lang_repo_count"), action="store", type='character', help="BigQuery table: language repo count"),
  make_option(c("-l", "--table_lang_list_by_repo"), action="store", type='character', help="BigQuery table: language list by repo"),
  make_option(c("-o", "--output"), action="store", type='character', help="Output pdf")
)
opt = parse_args(OptionParser(option_list=option_list))

proj <- opt$p # Project
ds <- opt$d # Dataset
tabc <- opt$table_lang_repo_count # Table of language repo count
tabl <- opt$table_lang_list_by_repo # Table of language list by repo
pdf <- opt$o # Output pdf

message(paste('BigQuery project:', proj))
message(paste('BigQuery dataset:', ds))
message(paste('BigQuery table of language repo count:', tabc))
message(paste('BigQuery table of language list by repo:', tabl))
message(paste('Output figure:', pdf))

# Access data on Bigquery
lang_by_repo <- list_tabledata(project = proj, dataset = ds, table = tabl)
table <- list_tabledata(project = proj, dataset = ds, table = tabc)
repo_count <- data.frame(table[,2], row.names = table[,1])

# Identify languages
lang <- sort(rownames(repo_count))
nlang <- length(lang)

# Sort languages by number of repos
ord <- order(repo_count[,1], decreasing = T)
rn <- rownames(repo_count)
repo_count = data.frame(repo_count[order(repo_count[,1], decreasing = T),], row.names = rn[ord])
colnames(repo_count) <- c("numRepos")

# Get the top languages
numtop_langs <- 30
top_langs <- repo_count[1:numtop_langs,]
names(top_langs) <- rownames(repo_count)[1:numtop_langs]
top_langs <- top_langs[order(top_langs)]

# Make barplot
pdf(pdf, height=8.5, width=11)
par(mar=c(5,12,4,2))
bp <- barplot(
  t(as.matrix(top_langs)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main=paste("Number of repos including language (N=", nrow(lang_by_repo), ")", sep=""),
  cex.names = 0.9,
  xlim=c(0, max(top_langs) + 50)
)
text(x=top_langs, y=bp, label=top_langs, pos = 4, cex=0.9)
invisible(dev.off())





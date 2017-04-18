rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)
library(optparse)

message('Calculating number of occurrences of "TODO: fix" by repo...')

option_list = list(
  make_option(c("-p", "--project"), action="store", type='character', help="BigQuery project"),
  make_option(c("-d", "--dataset"), action="store", type='character', help="BigQuery dataset"),
  make_option(c("-t", "--table"), action="store", type='character', help="BigQuery table"),
  make_option(c("-o", "--output"), action="store", type='character', help="Output pdf")
)
opt = parse_args(OptionParser(option_list=option_list))

proj <- opt$p # Project
ds <- opt$d # Dataset
tab <- opt$t # Table
pdf <- opt$o # Output pdf

message(paste('BigQuery project:', proj))
message(paste('BigQuery dataset:', ds))
message(paste('BigQuery table:', tab))
message(paste('Output figure:', pdf))

table <- list_tabledata(project = proj, dataset = ds, table = tab)
table <- table[order(-table$numOccurrences),]
num_top_repos <- nrow(table)
top_repos <- table$numOccurrences[1:num_top_repos]
names(top_repos) <- table$repo[1:num_top_repos]
top_repos <- top_repos[order(top_repos)]

# Make barplot
pdf(pdf, height=8.5, width=11)
par(mar=c(5,16,4,2))
bp <- barplot(
  t(as.matrix(top_repos)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Number of occurrences of 'TODO: fix' in source code"
)
invisible(dev.off())



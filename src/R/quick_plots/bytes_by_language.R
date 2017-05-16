rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)
library(optparse)

message('Calculating bytes of code by programming language...')

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

# Construct a vector of number of bytes per language
table <- list_tabledata(project = proj, dataset = ds, table = tab)
language <- table$language_name
bytes <- table$total_bytes
names(bytes) <- language
bytes <- bytes[order(-bytes)]

# Get the top languages
num_top_languages <- 25
top_languages <- bytes[1:num_top_languages]
names(top_languages) <- names(bytes)[1:num_top_languages]
top_languages <- top_languages[order(top_languages)]
# All other languages
others <- sum(bytes[1+num_top_languages:length(bytes)], na.rm=T)
new_names <- c("All others", names(top_languages))
top_languages <- c(others, top_languages)
names(top_languages) <- new_names

# Make barplot
pdf(pdf, height=8.5, width=11)
par(mar=c(5,12,4,2))
barplot(
  t(as.matrix(top_languages)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Total size of source files",
  axes=F
)
axis(1, at=c(0, 100000000, 200000000, 300000000), labels=c("0", "100Mb", "200Mb", "300Mb"))
invisible(dev.off())

message('Done calculating bytes of code by programming language. Wrote pdf.')




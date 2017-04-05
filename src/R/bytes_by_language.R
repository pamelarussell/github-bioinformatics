rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)
library(optparse)

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

# Construct a vector of number of bytes per language
table <- list_tabledata(project = proj, dataset = ds, table = tab)
language <- table$language_name
bytes <- table$total_bytes
names(bytes) <- language
bytes <- bytes[order(-bytes)]

# Get the top languages
numTopLanguages <- 25
topLanguages <- bytes[1:numTopLanguages]
names(topLanguages) <- names(bytes)[1:numTopLanguages]
topLanguages <- topLanguages[order(topLanguages)]
# All other languages
others <- sum(bytes[1+numTopLanguages:length(bytes)], na.rm=T)
newNames <- c("All others", names(topLanguages))
topLanguages <- c(others, topLanguages)
names(topLanguages) <- newNames

# Make barplot
pdf(pdf, height=8.5, width=11)
par(mar=c(5,12,4,2))
barplot(
  t(as.matrix(topLanguages)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Total size of source files",
  axes=F
)
axis(1, at=c(0, 100000000, 200000000, 300000000), labels=c("0", "100Mb", "200Mb", "300Mb"))
dev.off()






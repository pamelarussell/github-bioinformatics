rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)

project <- "github-bioinformatics-157418"

# Construct a vector of number of bytes per language
table <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "language_bytes")
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




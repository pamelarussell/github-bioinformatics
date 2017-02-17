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
num.top.languages <- 25
top.languages <- bytes[1:num.top.languages]
names(top.languages) <- names(bytes)[1:num.top.languages]
top.languages <- top.languages[order(top.languages)]
# All other languages
others <- sum(bytes[1+num.top.languages:length(bytes)], na.rm=T)
newNames <- c("All others", names(top.languages))
top.languages <- c(others, top.languages)
names(top.languages) <- newNames

# Make barplot
par(mar=c(5,12,4,2))
barplot(
  t(as.matrix(top.languages)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Total size of source files in bytes"
)



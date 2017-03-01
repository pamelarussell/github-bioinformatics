rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)

project <- "github-bioinformatics-157418"

table <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "num_occurrences_todo_fix_by_repo")
table <- table[order(-table$numOccurrences),]
numTopRepos <- nrow(table)
topRepos <- table$numOccurrences[1:numTopRepos]
names(topRepos) <- table$repo[1:numTopRepos]
topRepos <- topRepos[order(topRepos)]

# Make barplot
pdf('/Users/prussell/Documents/Github_mining/plots/test_repos/todo_fix_by_repo.pdf', height=8.5, width=11)
par(mar=c(5,16,4,2))
bp <- barplot(
  t(as.matrix(topRepos)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Number of occurrences of 'TODO: fix' in source code"
)
dev.off()



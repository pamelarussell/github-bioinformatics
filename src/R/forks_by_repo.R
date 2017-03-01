rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)

project <- "github-bioinformatics-157418"

table <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "num_forks_by_repo")
table <- table[order(-table$forks),]
numTopRepos <- 25
topRepos <- table$forks[1:numTopRepos]
names(topRepos) <- table$repo_name[1:numTopRepos]
topRepos <- topRepos[order(topRepos)]

# Make barplot
pdf('/Users/prussell/Documents/Github_mining/plots/test_repos/forks_by_repo.pdf', height=8.5, width=11)
par(mar=c(5,23,4,2))
bp <- barplot(
  t(as.matrix(topRepos)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main="Number of forks"
)
dev.off()


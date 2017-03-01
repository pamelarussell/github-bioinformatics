rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)

project <- "github-bioinformatics-157418"

# Access data on Bigquery
langByRepo <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "language_list_by_repo")
table <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "language_repo_count")
repoCount <- data.frame(table[,2], row.names = table[,1])

# Identify languages
lang <- sort(rownames(repoCount))
nlang <- length(lang)

# Sort languages by number of repos
ord <- order(repoCount[,1], decreasing = T)
rn <- rownames(repoCount)
repoCount = data.frame(repoCount[order(repoCount[,1], decreasing = T),], row.names = rn[ord])
colnames(repoCount) <- c("numRepos")

# Get the top languages
numTopLangs <- 30
topLangs <- repoCount[1:numTopLangs,]
names(topLangs) <- rownames(repoCount)[1:numTopLangs]
topLangs <- topLangs[order(topLangs)]

# Make barplot
pdf('/Users/prussell/Documents/Github_mining/plots/test_repos/repos_by_language.pdf', height=8.5, width=11)
par(mar=c(5,12,4,2))
bp <- barplot(
  t(as.matrix(topLangs)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main=paste("Number of repos including language (N=", nrow(langByRepo), ")", sep=""),
  cex.names = 0.9,
  xlim=c(0, max(topLangs) + 50)
)
text(x=topLangs, y=bp, label=topLangs, pos = 4, cex=0.9)
dev.off()





rm(list=ls())
options(stringsAsFactors=F)

library(bigrquery)

project <- "github-bioinformatics-157418"

# Access data on Bigquery
langBytes <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "language_bytes")
langByRepo <- list_tabledata(project = project, dataset = "test_repos_query_results", table = "language_list_by_repo")

# Identify languages
lang <- sort(langBytes$language_name)
nlang <- length(lang)
npair <- nlang * (nlang - 1) / 2

mkPair <- function(l1, l2) {
  paste(l1, l2, sep=", ")
}

# Make list of all possible language pairs
allPairs <- apply(expand.grid(lang, lang), 1, function(x) {
      l1 <- as.character(x[1])
      l2 <- as.character(x[2])
      if(l1 < l2) {
        mkPair(l1, l2)
      }
      else NA
})
allPairs <- allPairs[which(!is.na(allPairs))]

# Empty data frame of pair counts
pairCount <- data.frame(matrix(0, nrow = npair, ncol = 1), row.names = allPairs)

# Function to update pair counts based on language list for one repo
updatePairCount <- function(cslist) {
  l <- unlist(strsplit(cslist, ',', fixed = T))
  l <- l[which(!is.na(l))]
  apply(expand.grid(l, l), 1, function(x) {
    l1 <- as.character(x[1])
    l2 <- as.character(x[2])
    if(l1 < l2) {
      pairCount[mkPair(l1, l2), 1] <<- pairCount[mkPair(l1, l2), 1] + 1
    }
  })
}

# Update the pair counts for all repos
x <- lapply(langByRepo$languages, updatePairCount)
rm(x)

# Sort pairs by number of repos
ord <- order(pairCount[,1], decreasing = T)
rn <- rownames(pairCount)
pairCount = data.frame(pairCount[order(pairCount[,1], decreasing = T),], row.names = rn[ord])
colnames(pairCount) <- c("numRepos")

# Get the top pairs
numTopPairs <- 30
topPairs <- pairCount[1:numTopPairs,]
names(topPairs) <- rownames(pairCount)[1:numTopPairs]
topPairs <- topPairs[order(topPairs)]

# Make barplot
par(mar=c(5,12,4,2))
bp <- barplot(
  t(as.matrix(topPairs)),
  horiz = T,
  col = "darkorchid4",
  las=1,
  main=paste("Number of repos including both languages (N=", nrow(langByRepo), ")", sep=""),
  cex.names = 0.9,
  xlim=c(0, max(topPairs) + 20)
)
text(x=topPairs, y=bp, label=topPairs, pos = 4, cex=0.9)




suppressPackageStartupMessages(library(bigrquery))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(googlesheets))
suppressPackageStartupMessages(library(scales))
source("~/Dropbox/Documents/Github_mining/src/R/project_info.R")

# Load the data from BigQuery
repos_by_lang <- list_tabledata(project = proj, dataset = ds_analysis, table = "num_repos_by_lang") %>%
  mutate(language = tolower(language)) %>% 
  arrange(desc(num_repos))
lang_by_repo <- list_tabledata(project = proj, dataset = ds_analysis, table = "language_list_by_repo") %>%
  mutate(languages = tolower(languages))
lang_bytes <- list_tabledata(project = proj, dataset = ds_analysis, table = "bytes_by_language") %>% 
  mutate(language = tolower(language)) %>%
  group_by(language) %>%
  summarize(total_bytes = sum(total_bytes))
lang_bytes_by_repo <- list_tabledata(project = proj, dataset = ds_analysis, table = "language_bytes_by_repo") %>%
  mutate(language = tolower(language))


# Load language features from Google Sheet
lang_exec_method <- gs_read(gs_title("Execution style"), ws = "Execution style", col_names = c("language", "interpreted", "compiled")) %>%
  mutate(interpreted = as.logical(interpreted), compiled = as.logical(compiled))

lang_paradigm <- gs_read(gs_title("Paradigm"), ws = "Paradigm", col_names = c("language", "array", "declarative", "functional_impure",
                                                                              "functional_pure", "imperative", "logic", "object_oriented",
                                                                              "procedural")) %>%
  mutate(array = as.logical(array), declarative = as.logical(declarative), functional_impure = as.logical(functional_impure),
         functional_pure = as.logical(functional_pure), imperative = as.logical(imperative), logic = as.logical(logic),
         object_oriented = as.logical(object_oriented), procedural = as.logical(procedural))

lang_type_system <- gs_read(gs_title("Type system"), ws = "Type system", col_names = c("language", "system", "strength", "safety", "compatibility"))


# Number of repos by language
# Get the top languages
top_langs <- arrange(repos_by_lang[1:30,], num_repos)
top_langs$language <- factor(top_langs$language, levels = top_langs$language)


# Number of repos by language pair
# Identify languages
lang <- sort(lang_bytes$language)
nlang <- length(lang)
npair <- nlang * (nlang - 1) / 2

mkPair <- function(l1, l2) {
  paste(l1, l2, sep=", ")
}

# Make list of all possible language pairs
all_pairs <- apply(expand.grid(lang, lang), 1, function(x) {
  l1 <- as.character(x[1])
  l2 <- as.character(x[2])
  if(l1 < l2) {
    mkPair(l1, l2)
  }
  else NA
})
all_pairs <- all_pairs[which(!is.na(all_pairs))]

# Empty data frame of pair counts
pair_count <- data.frame(num_repos = matrix(0, nrow = npair, ncol = 1), 
                         row.names = all_pairs)

# Function to update pair counts based on language list for one repo
update_pair_count <- function(cslist) {
  l <- unlist(strsplit(cslist, ',', fixed = T))
  l <- l[which(!is.na(l))]
  apply(expand.grid(l, l), 1, function(x) {
    l1 <- as.character(x[1])
    l2 <- as.character(x[2])
    if(l1 < l2) {
      pair_count[mkPair(l1, l2), 1] <<- pair_count[mkPair(l1, l2), 1] + 1
    }
  })
}

# Update the pair counts for all repos
x <- lapply(lang_by_repo$languages, update_pair_count)
rm(x)

# Sort pairs by number of repos
pair_count$languages <- row.names(pair_count)
pair_count <- arrange(pair_count, desc(num_repos))

# Get the top pairs
top_pairs <- pair_count[1:30,]
top_pairs <- arrange(top_pairs, num_repos)
top_pairs$languages <- factor(top_pairs$languages, levels = top_pairs$languages)

# Total size of source files by language

# Construct a vector of number of bytes per language
language <- lang_bytes$language
bytes <- lang_bytes$total_bytes
names(bytes) <- language
bytes <- bytes[order(-bytes)]

# Get the top languages
num_top_languages <- 25
top_langs_bytes <- bytes[1:num_top_languages]
names(top_langs_bytes) <- names(bytes)[1:num_top_languages]
top_langs_bytes <- top_langs_bytes[order(top_langs_bytes)]
# All other languages
others <- sum(bytes[1+num_top_languages:length(bytes)], na.rm=T)
new_names <- c("All others", names(top_langs_bytes))
top_langs_bytes <- c(others, top_langs_bytes)
names(top_langs_bytes) <- new_names

# Functions to process language features

exec_method <- function(interpreted, compiled) {
  if(is.na(interpreted)) exec_method(FALSE, compiled)
  else if(is.na(compiled)) exec_method(interpreted, FALSE)
  else {
    if(interpreted && !compiled) "interpreted"
    else if(!interpreted && compiled) "compiled"
    else if(interpreted && compiled) "both"
    else NA
  }
}

paradigm <- function(array, declarative, functional_impure, functional_pure, imperative, logic,
                     object_oriented, procedural) {
  if (is.na(array)) paradigm(F, declarative, functional_impure, functional_pure, 
                             imperative, logic, object_oriented, procedural)
  else if (is.na(declarative)) paradigm(array, F, functional_impure, functional_pure, 
                                        imperative, logic, object_oriented, procedural)
  else if (is.na(functional_impure)) paradigm(array, declarative, F, functional_pure, 
                                              imperative, logic, object_oriented, procedural)
  else if (is.na(functional_pure)) paradigm(array, declarative, functional_impure, F, 
                                            imperative, logic, object_oriented, procedural)
  else if (is.na(imperative)) paradigm(array, declarative, functional_impure, functional_pure, 
                                       F, logic, object_oriented, procedural)
  else if (is.na(logic)) paradigm(array, declarative, functional_impure, functional_pure, 
                                  imperative, F, object_oriented, procedural)
  else if (is.na(object_oriented)) paradigm(array, declarative, functional_impure, functional_pure, 
                                            imperative, logic, F, procedural)
  else if (is.na(procedural)) paradigm(array, declarative, functional_impure, functional_pure, 
                                       imperative, logic, object_oriented, F)
  else {
    rtrn <- NULL
    if (array) rtrn <- c(rtrn, "array")
    if (declarative) rtrn <- c(rtrn, "declarative")
    if (functional_impure) rtrn <- c(rtrn, "functional_impure")
    if (functional_pure) rtrn <- c(rtrn, "functional_pure")
    if (imperative) rtrn <- c(rtrn, "imperative")
    if (logic) rtrn <- c(rtrn, "logic")
    if (object_oriented) rtrn <- c(rtrn, "object_oriented")
    if (procedural) rtrn <- c(rtrn, "procedural")
    if (is.null(rtrn)) NA
    else paste(rtrn, collapse = ", ")
  }
}

paradigm_abbrev <- function(paradigm) {
  gsub("array", "ARR", 
       gsub("declarative", "DCL", 
            gsub("functional_impure", "FNI", 
                 gsub("functional_pure", "FNP", 
                      gsub("imperative", "IMP", 
                           gsub("logic", "LOG",
                                gsub("object_oriented", "OOP",
                                     gsub("procedural", "PRC",
                                          gsub(", ", "-", paradigm)))))))))
}

# List repos with languages of both paradigms
repos_both_paradigms <- function(paradigm1, paradigm2) {
  if (paradigm1 == paradigm2) {
    stop("Can't pass two identical paradigms")
  }
  lang_features_by_repo %>% 
    group_by(repo_name) %>% 
    summarise(s1 = max(paradigm %in% c(paradigm1)), s2 = max(paradigm %in% c(paradigm2))) %>%
    filter(s1 == 1, s2 == 1)
}

# Number of repos with languages of both paradigms
num_repos_both_paradigms <- function(paradigm1, paradigm2) {
  nrow(repos_both_paradigms(paradigm1, paradigm2))
}

# Join language features to repo-level language data
# TODO !!!
lang_features_by_repo <- lang_bytes_by_repo %>%
  left_join(lang_type_system, by = "language") %>%
  left_join(lang_exec_method, by = "language") %>%
  left_join(lang_paradigm, by = "language")

lang_features_by_repo <- lang_features_by_repo %>%
  mutate(exec_method = apply(lang_features_by_repo[, c("interpreted", "compiled")], 1, function(row) exec_method(row[1], row[2]))) %>%
  mutate(paradigm = apply(lang_features_by_repo[, c("array", "declarative", "functional_impure",
                                                    "functional_pure", "imperative", "logic",
                                                    "object_oriented", "procedural")], 
                          1, function(row) paradigm(row[1], row[2], row[3], row[4], row[5],
                                                    row[6], row[7], row[8]))) %>%
  mutate(paradigm = paradigm_abbrev(paradigm)) %>%
  select(repo_name, language, total_bytes, exec_method, paradigm, system, strength, safety)

# Number of bytes by type system
bytes_by_type_system <- lang_features_by_repo %>% 
  group_by(system) %>% 
  summarise(total_bytes = sum(total_bytes)) %>%
  filter(system != "NA")

# Number of bytes by type system and strength
bytes_by_type_system_and_strength <- lang_features_by_repo %>% 
  group_by(system, strength) %>% 
  summarise(total_bytes = sum(total_bytes)) %>%
  filter(system != "NA") %>%
  mutate(desc = paste(strength, system))

# Number of bytes by execution method

bytes_by_exec_method <- lang_features_by_repo %>%
  group_by(exec_method) %>% 
  summarise(total_bytes = sum(total_bytes)) %>%
  filter(exec_method != "NA")

# Number of bytes by paradigm

bytes_by_paradigm <- lang_features_by_repo %>% 
  group_by(paradigm) %>% 
  summarise(total_bytes = sum(total_bytes)) %>%
  filter(paradigm != "NA")


# Analysis of how repos combine languages with different paradigms
paradigms <- unique(lang_features_by_repo %>% filter(!is.na(paradigm)) %>% select(paradigm))[[1]]
paradigm_pairs <- expand.grid(paradigms, paradigms) %>% 
  filter(Var1 != Var2) %>%
  rename(paradigm1 = Var1, paradigm2 = Var2)
paradigm_pairs$num_repos_both <- apply(paradigm_pairs, 1, function(row) num_repos_both_paradigms(row[1], row[2]))


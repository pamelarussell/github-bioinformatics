# A large-scale analysis of bioinformatics code on GitHub

## Summary

This repository contains the code used for "A large-scale analysis of bioinformatics code on GitHub" by Russell et al. (Citation TBA). If you want to reproduce the results or use parts of the code, see the paper supplement for complete instructions on environment and tool setup.

## Repository contents

#### `paper/`

- R markdown documents that generate the figures in the paper
- R markdown HTML reports

#### `src/`

###### `src/pipeline/`

- Perl pipeline that wraps all the data generation and analysis steps
- Sample pipeline config file

###### `src/python/`

- Mostly code that interacts with the GitHub API and the dataset on BigQuery. You shouldn't need to run any of this code from the command line, but rather should control it through the Perl pipeline.

###### `src/R/`

- Code used for the paper
    - Topic modeling of paper abstracts
    - Gender analysis
    - Paper metadata
- You need to specify the config file paths in project_info.R
- Exploratory analysis, including HTML reports

## Required software

#### Language versions



#### R packages

- See session info at the end of the R markdown reports for list of packages and versions

#### Python packages



#### Other tools



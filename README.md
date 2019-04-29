# A large-scale analysis of bioinformatics code on GitHub

## Summary

This repository contains the code used for "A large-scale analysis of bioinformatics code on GitHub" by Russell et al. ([article](https://doi.org/10.1371/journal.pone.0205898)). If you want to reproduce the results or use parts of the code, see the paper supplement for complete instructions on environment and tool setup.

## Repository contents

#### `paper/`

- R markdown documents that generated the figures in the paper
- Knitted HTML reports including the figures in the paper

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
- Exploratory analysis, including knitted reports

## Required software

- Python version >= 3.6.4
- R version >= 3.4.3
- Perl version >= 5.18.2
- [cloc version 1.72](https://github.com/AlDanial/cloc/releases/tag/v1.72)

## Data

Data extracted from the GitHub API and analyzed in the paper are available at [https://doi.org/10.17605/OSF.IO/UWHX8](https://doi.org/10.17605/OSF.IO/UWHX8). The following tables are included:

- Repository licenses for the main and high-profile projects
- Repository metrics for the main and high-profile projects
- Commit records for the main and high-profile projects. Personal identifying data such as names and email addresses have been removed. The full records can be reconstructed from the provided API reference for each record.
- File metadata for the main and high-profile projects
- File initial commit timestamps for the main and high-profile projects

File contents are not included due to the absence of explicit licenses for the majority of repositories. File contents can be reconstructed from the file metadata as explained in the paper.

## Citation

Russell PH, Johnson RL, Ananthan S, Harnke B, Carlson NE (2018) A large-scale analysis of bioinformatics code on GitHub. PLoS ONE 13(10): e0205898. [https://doi.org/10.1371/journal.pone.0205898](https://doi.org/10.1371/journal.pone.0205898)

## Contact

pamela.russell@gmail.com


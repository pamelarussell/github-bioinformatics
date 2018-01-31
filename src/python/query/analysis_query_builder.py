
#####  Functions to build queries against GitHub dataset tables


# Number of actors by repo
def build_query_num_actors_by_repo(proj, dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(*) AS num_actors
    FROM (
      SELECT
        repo_name,
        actor_id
      FROM
        [%s:%s.%s]
      GROUP BY
        repo_name,
        actor_id
      ORDER BY
        repo_name,
        actor_id ASC)
    GROUP BY
      repo_name
    ORDER BY
      num_actors DESC
    """ % (proj, dataset, table)


# Number of bytes of code by language
def build_query_bytes_by_language(proj, dataset, table_languages):
    return """
    SELECT
      language,
      sum (total_bytes) as total_bytes
    FROM
      [%s:%s.%s]
    GROUP BY
      language
    ORDER BY
      total_bytes DESC
    """ % (proj, dataset, table_languages)

# Number of bytes of code by language and repo
def build_query_bytes_by_lang_and_repo(proj, ds_loc, table_loc, ds_files, table_files):
    return """
    SELECT
      files.repo_name AS repo_name,
      loc.language AS language,
      SUM(files.size) AS total_bytes
    FROM (
      SELECT
        files.repo_name,
        loc.language,
        files.size
      FROM (
        SELECT
          *
        FROM
          [%s:%s.%s] AS loc
        INNER JOIN
          [%s:%s.%s] AS files
        ON
          loc.sha = files.sha ))
    GROUP BY
      repo_name,
      language
    ORDER BY
      repo_name    
  """ % (proj, ds_loc, table_loc, proj, ds_files, table_files)

# Number of repos with code in each language
def build_query_repo_count_by_language(proj, dataset, table_languages):
    return """
    SELECT
      language,
      COUNT(*) AS num_repos
    FROM
      [%s:%s.%s]
    GROUP BY
      1
    ORDER BY
      2 DESC
    """ % (proj, dataset, table_languages)
    
    
# List of languages by repo
def build_query_language_list_by_repo(proj, dataset, table_languages):
    return """
    SELECT
      repo_name,
      GROUP_CONCAT(language) languages
    FROM
      [%s:%s.%s]
    GROUP BY
      repo_name
    """ % (proj, dataset, table_languages)


# Number of languages by repo
def build_query_num_languages_by_repo(proj, dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(*) AS num_languages
    FROM
      [%s:%s.%s]
    GROUP BY
      1
    ORDER BY
      2 DESC    
    """ % (proj, dataset, table)


# "Test cases" (files containing "test" somewhere in the path or filename)
# Similar to heuristic used in "An Empirical Study of Adoption of Software Testing in Open Source Projects"
# Kochhar PS, Bissyandé TF, Lo D, Jiang L. An Empirical Study of Adoption of Software Testing in Open Source Projects. 2013 13th International Conference on Quality Software. 2013. pp. 103–112. doi:10.1109/QSIC.2013.57
# Only include files that have a language identified in lines_of_code table
def build_query_test_cases(proj, ds_files, table_files, ds_loc, table_loc):
    return """
    SELECT
      files.repo_name as repo_name,
      files.sha as sha,
      loc.language as language,
      files.path as path,
      loc.code as lines
    FROM
      [%s:%s.%s] AS files
    INNER JOIN
      [%s:%s.%s] AS loc
    ON
      files.sha = loc.sha
    WHERE
      LOWER(files.path) CONTAINS 'test'
    """ % (proj, ds_files, table_files, proj, ds_loc, table_loc)

# Number of test cases and total lines of code in test cases by repo
def build_query_test_cases_by_repo(proj, dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(*) AS num_test_cases,
      SUM(lines) AS total_lines_test_cases
    FROM (
      SELECT
        *
      FROM
        [%s:%s.%s])
    GROUP BY
      repo_name    
  """ % (proj, dataset, table)

# Number of bug fix commits and total commits by repo
# Bug fix commits are identified using the heuristic in "A Large Scale Study of Programming Languages  and Code Quality in Github"
# Ray B, Posnett D, Filkov V, Devanbu P. A large scale study of programming languages and code quality in github. Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering. ACM; 2014. pp. 155–165. doi:10.1145/2635868.2635922
def build_query_commit_types(proj, dataset, table_commits):
    return """
SELECT
  all_commits.repo_name AS repo_name,
  all_commits.num_commits AS num_commits,
  bug_fix_commits.num_bug_fix_commits AS num_bug_fix_commits
FROM (
  SELECT
    repo_name,
    COUNT(commit_sha) AS num_commits
  FROM
    [%s:%s.%s]
  GROUP BY
    repo_name) AS all_commits
LEFT OUTER JOIN (
  SELECT
    repo_name,
    COUNT(commit_sha) AS num_bug_fix_commits
  FROM
    [%s:%s.%s]
  WHERE
    LOWER(commit_message) NOT LIKE 'merge%%'
    AND (LOWER(commit_message) CONTAINS 'error'
      OR LOWER(commit_message) CONTAINS 'bug'
      OR LOWER(commit_message) CONTAINS 'fix'
      OR LOWER(commit_message) CONTAINS 'issue'
      OR LOWER(commit_message) CONTAINS 'mistake'
      OR LOWER(commit_message) CONTAINS 'incorrect'
      OR LOWER(commit_message) CONTAINS 'fault'
      OR LOWER(commit_message) CONTAINS 'defect'
      OR LOWER(commit_message) CONTAINS 'flaw')
  GROUP BY
    repo_name) AS bug_fix_commits
ON
  bug_fix_commits.repo_name = all_commits.repo_name    """ % (proj, dataset, table_commits, proj, dataset, table_commits)
    
    
# Project duration measured from first to last commit
def build_query_project_duration(proj, dataset, table):
    return """
    SELECT
      repo_name,
      first_commit,
      last_commit,
      (DATEDIFF(last_commit, first_commit) + 1) AS commit_span_days
    FROM (
      SELECT
        repo_name,
        MIN(author_commit_date) AS first_commit,
        MAX(author_commit_date) AS last_commit
      FROM
        [%s:%s.%s]
      GROUP BY
        repo_name )
    ORDER BY
      commit_span_days DESC    
    """ % (proj, dataset, table)
    
    
# Total number of lines of code by repo
# Only include files that have a language identified in lines_of_code table
def build_query_lines_of_code_by_repo(proj, ds_files, table_files, ds_loc, table_loc):
    return """
    SELECT
      files.repo_name AS repo_name,
      SUM(loc.code) AS lines_of_code
    FROM (
      SELECT
        repo_name,
        sha
      FROM
        [%s:%s.%s]) AS files
    INNER JOIN (
      SELECT
        sha,
        code
      FROM
        [%s:%s.%s]) AS loc
    ON
      files.sha = loc.sha
    GROUP BY
      repo_name
    ORDER BY
      lines_of_code DESC    
    """ % (proj, ds_files, table_files, proj, ds_loc, table_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

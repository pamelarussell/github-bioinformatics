from structure.bq_proj_structure import *



#####  Functions to build queries against GitHub dataset tables


# Number of actors by repo
def build_query_num_actors_by_repo(dataset, table):
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
    """ % (project_bioinf, dataset, table)


# Number of bytes of code by language
def build_query_bytes_by_language(dataset, table):
    return """
    SELECT
      language_name,
      sum (language_bytes) as total_bytes
    FROM
      [%s:%s.%s]
    WHERE
      language_name != "null"
    GROUP BY
      language_name
    ORDER BY
      total_bytes DESC
    """ % (project_bioinf, dataset, table)


# Number of repos with code in each language
def build_query_repo_count_by_language(dataset, table):
    return """
    SELECT
      language_name,
      COUNT(*) AS num_repos
    FROM
      [%s:%s.%s]
    WHERE
      language_name != "null"
    GROUP BY
      1
    ORDER BY
      2 DESC
    """ % (project_bioinf, dataset, table)
    
    
# List of languages by repo
def build_query_language_list_by_repo(dataset, table):
    return """
    SELECT
      repo_name,
      GROUP_CONCAT(language_name) languages
    FROM
      [%s:%s.%s]
    GROUP BY
      repo_name
    """ % (project_bioinf, dataset, table)


# Number of forks by repo
def build_query_num_forks_by_repo(dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(DISTINCT actor_id) AS forks
    FROM (
      SELECT
        type,
        repo_name,
        actor_id
      FROM
        [%s:%s.%s] AS events
      WHERE
        events.type = 'ForkEvent')
    GROUP BY
      1
    ORDER BY
      2 DESC
    """ % (project_bioinf, dataset, table)


# Number of occurrences of "TODO: fix" by repo
def build_query_num_todo_fix_by_repo(dataset, table):
    return """
    SELECT
      files_repo_name AS repo,
      SUM((LENGTH(content) - LENGTH(REPLACE(LOWER(content), 'todo: fix', '')))/LENGTH('todo: fix')) AS numOccurrences
    FROM (
      SELECT
        files_repo_name,
        contents_content AS content
      FROM
        [%s:%s.%s]
      WHERE
        NOT contents_binary
        AND LOWER(contents_content) CONTAINS 'todo: fix')
    GROUP BY
      1
    ORDER BY
      2 DESC
    """ % (project_bioinf, dataset, table)


# Number of languages by repo
def build_query_num_languages_by_repo(dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(*) AS num_languages
    FROM
      [%s:%s.%s]
    WHERE
      language_name != "null"
    GROUP BY
      1
    ORDER BY
      2 DESC    
    """ % (project_bioinf, dataset, table)


# Number of watch events by repo
def build_query_num_watch_events_by_repo(dataset, table):
    return """
    SELECT
      repo_name,
      COUNT(*) AS num_watchers
    FROM (
      SELECT
        repo_name,
        actor_id,
        type
      FROM
        [%s:%s.%s]
      WHERE
        type = 'WatchEvent'
      GROUP BY
        repo_name,
        actor_id,
        type
      ORDER BY
        repo_name,
        actor_id ASC)
    GROUP BY
      repo_name
    ORDER BY
      num_watchers DESC    
    """ % (project_bioinf, dataset, table)


# "Test cases" (files containing "test" somewhere in the path or filename)
# Similar to heuristic used in "An Empirical Study of Adoption of Software Testing in Open Source Projects"
# Only include files that have a language identified in lines_of_code table
def build_query_test_cases(ds_files, table_files, ds_loc, table_loc):
    return """
    SELECT
      files.repo_name,
      files.path
    FROM
      [%s:%s.%s] AS files
    INNER JOIN
      [%s:%s.%s] AS loc
    ON
      files.id = loc.id
    WHERE
      LOWER(files.path) CONTAINS 'test'
    """ % (project_bioinf, ds_files, table_files, project_bioinf, ds_loc, table_loc)













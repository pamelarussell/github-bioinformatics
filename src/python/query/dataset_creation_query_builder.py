
##### Functions to build queries against public GitHub data to extract data on specific repos


# Convert a list of repo names into a comma separated, lowercase, double quoted list for SQL queries
def comma_separated_lowercase_quoted_repo_names(repos):
    return ','.join(['"%s"' % repo.strip().lower() for repo in repos])
    
    
# Commits
# repos is a comma separated, double quoted list of repo names
def build_query_commits(project_bq_public_data, dataset_github_repos, table_github_repos_commits, repos):
    return """
    SELECT
      repo_name,
      commit,
      tree,
      parent,
      subject,
      message,
      author.name,
      author.email,
      author.date,
      committer.name,
      committer.email,
      committer.date,
      encoding
    FROM
      FLATTEN([%s:%s.%s], repo_name)
    WHERE
      lower(repo_name) IN ( %s )

    """ % (project_bq_public_data, dataset_github_repos, table_github_repos_commits, comma_separated_lowercase_quoted_repo_names(repos))
    
    
# Files
# repos is a comma separated, double quoted list of repo names
def build_query_files(project_bq_public_data, dataset_github_repos, table_github_repos_files, repos):
    return """
    SELECT
      *
    FROM
      [%s:%s.%s]
    WHERE
      lower(repo_name) IN ( %s )
    """  % (project_bq_public_data, dataset_github_repos, table_github_repos_files, comma_separated_lowercase_quoted_repo_names(repos))


# Contents
# repos is a comma separated, double quoted list of repo names
def build_query_contents(project_bq_public_data, dataset_github_repos, table_github_repos_files, 
                         table_github_repos_contents, repos):
    return """
        SELECT
      *
    FROM (
      SELECT
        *
      FROM (
        SELECT
          *
        FROM (
          SELECT
            *
          FROM
            [%s:%s.%s]
          WHERE
            lower(repo_name) IN ( %s )))) AS files
    LEFT JOIN (
      SELECT
        *
      FROM (
        SELECT
          *
        FROM (
          SELECT
            *
          FROM
            [%s:%s.%s]
          WHERE
            id IN (
            SELECT
              id
            FROM
              [%s:%s.%s]
            WHERE
              lower(repo_name) IN ( %s ) )))) AS contents
    ON
      files.id=contents.id

    """ % (project_bq_public_data, dataset_github_repos, table_github_repos_files, comma_separated_lowercase_quoted_repo_names(repos),
           project_bq_public_data, dataset_github_repos, table_github_repos_contents,
           project_bq_public_data, dataset_github_repos, table_github_repos_files, comma_separated_lowercase_quoted_repo_names(repos))
    
    
# Languages used in each repo
# repos is a comma separated, double quoted list of repo names
def build_query_languages(project_bq_public_data, dataset_github_repos, table_github_repos_languages, repos):
    return """
    SELECT
      *
    FROM
      [%s:%s.%s]
    WHERE
      lower(repo_name) IN ( %s )
    """ % (project_bq_public_data, dataset_github_repos, table_github_repos_languages, comma_separated_lowercase_quoted_repo_names(repos))
    
    
# License for each repo
# repos is a comma separated, double quoted list of repo names
def build_query_licenses(project_bq_public_data, dataset_github_repos, table_github_repos_licenses, repos):
    return """
    SELECT
      *
    FROM
      [%s:%s.%s]
    WHERE
      lower(repo_name) IN ( %s )
    """ % (project_bq_public_data, dataset_github_repos, table_github_repos_licenses, comma_separated_lowercase_quoted_repo_names(repos))
    
    
    
    
    
    
    
    
    
    
    
    
    
    
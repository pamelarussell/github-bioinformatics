import time


def unique_vals(client, proj, dataset, table, col_name):
    """ Returns the ordered set of unique values in a column of a BigQuery table
    
    Args:
        client: BigQuery-Python client
        proj: Project name
        dataset: Dataset name
        table: Table name
        col_name: Column name
    """
    if not client.check_table(dataset, table):
            return []
    res = run_bq_query(client, "SELECT %s FROM [%s:%s.%s] GROUP BY %s ORDER BY %s" % (col_name, proj, dataset, table, col_name, col_name), 120)
    return [rec[col_name] for rec in res]

def run_bq_query(client, query, timeout):
    """ Returns the results of a BigQuery query
    
    Args:
        client: BigQuery-Python bigquery client
        query: String query
        timeout: Query timeout time in seconds
        
    Returns:
        List of dicts, one per record; 
        dict keys are table field names and values are entries
    
    """
    
    job_id, _results = client.query(query, timeout=timeout)
    complete, row_count = client.check_job(job_id)
    if complete:
        results = client.get_query_rows(job_id)
        print('\nGot %s records' %row_count)
    else:
        raise RuntimeError('Query not complete')
    return(results)

def create_bq_table(client, dataset, table, schema):
    """ Create an empty BigQuery table
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        dataset: Dataset name
        table: Table name
        schema: List of dictionaries describing the schema
                Each dictionary has fields 'name', 'type', and 'mode'
                Example:
                    [{'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
                    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
                    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
                    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
                    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}]
    
    """
    
    print('Creating table %s.%s' % (dataset, table))
    exists = client.check_table(dataset, table)
    if exists:
        raise AssertionError("Table already exists: %s.%s" % (dataset,table))
    created = client.create_table(dataset, table, schema)
    # Check that the empty table was created
    exists = client.check_table(dataset, table)
    if not exists:
        raise RuntimeError('Table creation failed: %s.%s' % (dataset, table))

def delete_bq_table(client, dataset, table):
    """ Delete a BigQuery table if it exists
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        dataset: Dataset name
        table: Table name
    
    """
    
    exists = client.check_table(dataset, table)
    if exists:
        print('WARNING: Deleting existing table %s.%s' % (dataset, table))
        deleted = client.delete_table(dataset, table)
        if not deleted:
            raise RuntimeError('Table deletion failed: %s.%s' % (dataset, table))

    
def push_bq_records(client, dataset, table, records, sleep = 30, max_batch = 100):
    """ Push records to a BigQuery table
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        dataset: Dataset name
        table: Table name
        records: List of records to add
                 Each record is a dictionary with keys matching the schema    
        sleep: Time to sleep if first attempt raises BrokenPipeError, then try
                one more time
        max_batch: Max number of records to push at one time
    """
    if len(records) > max_batch:
        split = len(records) // 2
        push_bq_records(client, dataset, table, records[0:split], sleep, max_batch)
        push_bq_records(client, dataset, table, records[split:], sleep, max_batch)
    try:
        succ = client.push_rows(dataset, table, records)
        if not succ:
            raise RuntimeError('Push to BigQuery table was unsuccessful')
    except BrokenPipeError:
        print("BrokenPipeError while pushing %s records. Waiting %s seconds and trying again." % (len(records), sleep)) 
        time.sleep(sleep)
        push_bq_records(client, dataset, table, records, sleep, max_batch)

    
def run_query_and_save_results(client, query, res_dataset, res_table, timeout = 60):
    """ Run a query and save the results to a BigQuery table
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        query: The query to run
        res_dataset: Dataset to write results to
        res_table: Table to write results to
        timeout: Timeout
        
    """
    # Delete the results table if it exists
    delete_bq_table(client, res_dataset, res_table)
    # Run the query and write results to table
    print('\nRunning query and writing to table %s.%s:\n%s\n' % (res_dataset, res_table, query))
    job = client.write_to_table(query, res_dataset, res_table, allow_large_results = True, 
                                create_disposition = 'CREATE_IF_NEEDED', write_disposition = 'WRITE_EMPTY')
    client.wait_for_job(job, timeout)
    

    
    
    
    
    
    
    
    
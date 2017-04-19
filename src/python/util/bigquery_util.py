

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
    
    try:
        job_id, _results = client.query(query, timeout=timeout)
    except BigQueryTimeoutException:
        print('Query timeout')
    complete, row_count = client.check_job(job_id)
    if complete:
        results = client.get_query_rows(job_id)
        print('Got %s rows' %row_count)
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
    created = client.create_table(dataset, table, schema)
    # Check that the empty table was created
    exists = client.check_table(dataset, table)
    if not exists:
        raise RuntimeError('Table creation failed')

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

    
def push_bq_records(client, dataset, table, records):
    """ Push records to a BigQuery table
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        dataset: Dataset name
        table: Table name
        records: List of records to add
                 Each record is a dictionary with keys matching the schema
    
    """
    print('Pushing %s results to table %s.%s' % (len(records), dataset, table))
    succ = client.push_rows(dataset, table, records)
    if not succ:
        raise RuntimeError('Push to BigQuery table was unsuccessful')

    
def run_query_and_save_results(client, query, res_dataset, res_table):
    """ Run a query and save the results to a BigQuery table
    
    Args:
        client: BigQuery-Python client object with readonly set to false
                (https://github.com/tylertreat/BigQuery-Python)
        query: The query to run
        res_dataset: Dataset to write results to
        res_table: Table to write results to 
        
    """
    # Delete the results table if it exists
    delete_bq_table(client, res_dataset, res_table)
    # Run the query and write results to table
    print('Running query and writing to table %s.%s\n' % (res_dataset, res_table))
    client.write_to_table(query, res_dataset, res_table, allow_large_results = True)

    
    
    
    
    
    
    
    
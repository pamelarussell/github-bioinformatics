

def run_query(client, query, timeout):
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


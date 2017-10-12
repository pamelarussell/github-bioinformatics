import gspread
from oauth2client.service_account import ServiceAccountCredentials
from local_params import json_key_final_dataset

def get_repo_names(sheet):
    """
    Returns the sorted names of repositories marked with use_repo=1 in the Google sheet
    
    params:
        sheet: Name of Google Sheets file
        
    returns:
        Sorted list of repo names
        
    """
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_final_dataset, scope)
    client = gspread.authorize(creds)
     
    # Load repos from the spreadsheet
    records = client.open(sheet).get_worksheet(1).get_all_records()
    rtrn = list({rec["repo_name"] for rec in records if rec["use_repo"] == 1})
    rtrn.sort()
    return rtrn
    
    



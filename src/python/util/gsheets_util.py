import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_repo_names(sheet, json_key):
    """
    Returns the sorted names of repositories marked with use_repo=1 in the Google sheet
    
    params:
        sheet: Name of Google Sheets file
        json_key: JSON key file for Google credentials
        
    returns:
        Sorted list of repo names
        
    """
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
    client = gspread.authorize(creds)
    
     
    # Load repos from the spreadsheet
    try:
        records = client.open(sheet).get_worksheet(0).get_all_records()
        rtrn = list({rec["repo_name"] for rec in records if rec["use_repo"] == 1})
        rtrn.sort()
        print("Got %s repos." %(len(rtrn)))
        return rtrn
    except gspread.exceptions.SpreadsheetNotFound as e:
        print("\nSpreadsheet not found. Did you share the sheet with the client email in your JSON oauth file?")
        all_sheets = client.openall()
        for s in all_sheets:
            print(s.title)
        print("\n")
        raise e
    



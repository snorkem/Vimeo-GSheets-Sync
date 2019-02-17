#  Vimeo GSheet Sync v1.1 by Alex Fichera, 2019
#  Python script to grab all videos from a Vimeo account, add them to a
#  dataframe and write them to a Google Sheet.
#  USE: Install dependencies and modify the user defined variables

import vimeo
import pandas as pd
import pygsheets as pgs
import re
# Imports

######### USER DEFINED VARIABLES #########

# Vimeo API stuff
TOKEN = 'YOUR TOKEN STRING HERE'
KEY = 'YOUR KEY HERE''
SECRET = 'YOUR SECRET STRING HERE'

# Google Sheets API stuff here
sheetKey = 'GOOGLE SHEET ID'  # Target sheet to write data
clientSecret = 'YOUR CLIENT SECRET HERE'  # Path to client secret JSON file from
serviceFile = 'YOUR SERVICE FILE HERE'  # Path to service JSON file

# Vimeo data params.
maxVids = '100'
sortBy = '&ampsort=date=asc'
dataFields = 'name,uri,created_time'

############## Create Clients ##############

try:  # Initialize client
    client = vimeo.VimeoClient(
        token=TOKEN,
        key=KEY,
        secret=SECRET
    )
except:
    print("Error establishing Vimeo client")
    quit(1)

try:  # Initialize Google client
    gc = pgs.authorize(client_secret=clientSecret, service_file=serviceFile)
except:
    print('Error establishing Google client')
    quit(1)

######### Global Data Variables #########
# Get videos sorted by date created
vidUri = '/me/videos?per_page=' + maxVids + sortBy

# Initial Vimeo request stuff
vidListResponse = client.get(vidUri, params={'fields': dataFields})
response = vidListResponse.json()
firstPageUrl = response['paging']['first']
nextPageUrl = response['paging']['next']
lastPageUrl = response['paging']['last']
currPage = response['page']
pageData = response['data']
dates = []

###########################################################

def print_final_df(df, text):
    # Prints a dataframe to the console with some title text
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print('')
        print('********************************')
        print(text)
        print('********************************')
        print('-- Begin Dataframe --')
        print(df)
        print('-- End Dataframe --')
        print('')


def main():
    if pageData is None:
        print('No videos on first page. Quiting.')
        quit()
    elif pageData is not None:
        try:
            print('Fetching page ' + str(currPage) + ' of ' + lastPageUrl[-1])
            df = pd.DataFrame.from_dict(pageData)  # Initialize dataframe here
            print_final_df(df, 'Dateframe initialized!')
        except:
            print('Error initializing dataframe.')
            quit(1)

    # Get remaining pages and append to dataframe

    for page in range(2, int(lastPageUrl[-1]) + 1):
        print('Fetching page ' + str(page) + ' of ' + lastPageUrl[-1])
        pageTurn = nextPageUrl[:-1] + str(page)  # Remove last char from url and turn page
        newRequest = client.get(pageTurn)
        newData = newRequest.json().get('data')
        newDf = pd.DataFrame.from_dict(newData)
        try:
            # Add new data to dataframs
            df = df.append(newDf, ignore_index=True)
            print_final_df(newDf, 'Adding new data to dataframe:')
        except:
            print('Error adding new data to dataframe.')
            quit(1)

    # Cleanup the dates and urls
    df = df[['name', 'uri', 'created_time']]  # Re-order for clarity
    for dfitr, row in df.iterrows():
        uri = row['uri']
        urlCleanup = re.sub('/[^>]+/', '', uri)
        dateCleanup = row['created_time'][:-15]
        urlFix = 'https://vimeo.com/' + urlCleanup
        df.loc[dfitr, 'uri'] = urlFix
        df.loc[dfitr, 'created_time'] = dateCleanup


    # Print final dataframe
    print_final_df(df, 'Final Dataframe')

    # Try writing the dataframe to google sheet
    try:
        print('Writing dataframe to Google Sheet...')
        s = gc.open_by_key(sheetKey)
        wks = s.worksheet(property='index', value=0)  # Grab the first worksheet to use.
        wks.set_dataframe(df, start='A2', copy_head=False)

        # Commented out sheet sort call so that it doesn't screw up the initial date sort in JSON response
        # wks.sort_range(start='A2', end='B10000', basecolumnindex=0, sortorder='ASCENDING')

        print('Success! Open the Google Sheet.')
    except:
        print('Something went wrong with pygsheets')
        quit(1)

if __name__ == '__main__':
    main()

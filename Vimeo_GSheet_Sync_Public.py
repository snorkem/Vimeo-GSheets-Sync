#  Vimeo GSheet Sync v1.0 by Alex Fichera, 2019
#  Python script to grab all videos from a Vimeo account, add them to a
#  dataframe and write them to a Google Sheet.
#  USE: Install dependencies and modify the user defined variables

import vimeo
import pandas as pd
import pygsheets as pgs
import re
# Imports

############# USER DEFINED VARIABLES ##################

# Vimeo API stuff
TOKEN = 'YOUR TOKEN STRING HERE
KEY = 'YOUR KEY HERE'
SECRET = 'YOUR SECRET STRING HERE'

# Google Sheets API stuff here
sheetKey = 'GOOGLE SHEET ID'  # Target sheet to write data
clientSecret = 'YOUR CLIENT SECRET HERE'  # Path to client secret JSON file from
serviceFile = 'YOUR SERVICE FILE HERE'  # Path to service JSON file

############### Create Clients ##########

try: # Initialize client
    client = vimeo.VimeoClient(
        token=TOKEN,
        key=KEY,
        secret=SECRET
    )
except:
    print("Error establishing Vimeo client")
    quit(1)

try:# Initialize Google client
    gc = pgs.authorize(client_secret=clientSecret, service_file=serviceFile)
except:
    print('Error establishing Google client')
    quit(1)

############### Global Data Variables #########

# Vimeo data params.
maxVids = '100'
vidUri = '/me/videos?per_page=' + maxVids
dataFields = 'name,uri'

# Initial Vimeo request stuff
vidListResponse = client.get(vidUri, params={'fields': dataFields})
response = vidListResponse.json()
firstPageUrl = response['paging']['first']
nextPageUrl = response['paging']['next']
lastPageUrl = response['paging']['last']
currPage = response['page']
pageData = response['data']

###########################################################

def print_Final_Df(df, text):
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

if pageData is None:
    print('No videos on first page. Quiting')
    quit()
elif pageData is not None:
    try:
        print('Fetching page ' + str(currPage) + ' of ' + lastPageUrl[-1])
        df = pd.DataFrame.from_dict(pageData) # Initialize dataframe here
        print_Final_Df(df, 'Dateframe initialized!')
    except:
        print('data frame error')
        quit(1)

# Get all the pages and append to dataframe
for page in range(2, int(lastPageUrl[-1]) + 1):
    print('Fetching page ' + str(page) + ' of ' + lastPageUrl[-1])
    pageTurn = nextPageUrl[:-1] + str(page)  # Remove last char from url and turn page
    newRequest = client.get(pageTurn)
    newPage = newRequest.json()
    newData = newPage.get('data')
    # print(newData)
    # print(pageTurn)
    try:  # Add new data to dataframs
        newDf = pd.DataFrame.from_dict(newData)
        print_Final_Df(newDf, 'Adding new data to dataframe:')
        df = df.append(newDf, ignore_index=True)
    except:
        print('dataframe error')
        quit(1)

# Cleanup the urls
dfitr = df['uri'];
for dfitr, row in df.iterrows():
    uri = row['uri']
    urlCleanup = re.sub('/[^>]+/', '', uri)
    urlFix = 'https://vimeo.com/' + urlCleanup
    df.loc[dfitr, 'uri'] = urlFix

# Print final dataframe
print_Final_Df(df, 'Final Dataframe')

# Try writing the dataframe to google sheet
try:
    print('Writing dataframe to Google Sheet...')
    s = gc.open_by_key(sheetKey)
    wks = s.worksheet(property='index', value=0)  # Grab the first worksheet to use.
    wks.set_dataframe(df, start='A2', copy_head=False)
    # sort the sheet so it looks nice
    wks.sort_range(start='A2', end='B10000', basecolumnindex=0, sortorder='ASCENDING')
    print('Success! Open the Google Sheet.')
except:
    print('Something went wrong with pygsheets')
    quit(1)

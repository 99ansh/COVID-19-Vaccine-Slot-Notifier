
import pickle
from pymongo import MongoClient
import pandas as pd
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def get_users():
    client = MongoClient("mongodb://localhost:27017")

    db = client["temp"]
    users=db["users"]
    users.remove({})

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # The ID and range of a sample spreadsheet.
    with open("SPREADSHEET_ID.pickle","rb") as file:
        SPREADSHEET_ID = pickle.load(file)
    RANGE_NAME = 'B1:AR'

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    states_districts={}
    if not values:
        print('No data found.')
    else:
        i=0
        for row in values:
            if i==0:
                i+=1
                continue
            temp = list(filter(lambda a: a!="",row))
            print(temp)
            state = temp[3].strip()
            
            district = temp[4].strip()
            users.insert_one({"emailId":temp[0],"name":temp[1],"age":temp[2],"state":state,"district":district})
            if (state,district) not in states_districts:
                states_districts[(state,district)]=1
    return states_districts

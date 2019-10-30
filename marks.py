from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from apiclient import discovery

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CLIENT_SECRET_FILE = "client_secret.json"
SPREADSHEET_ID = '1ddelHaR10-7iKHH_ceaROjMFSJzhEOrOXSgGoS327-g'
RANGE_NAME = 'Sheet1!A2:F'

def get_marks_from_google_sheet(student_id):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CLIENT_SECRET_FILE, SCOPES)
    http = credentials.authorize(Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        return "NO MESSAGE FOUND"
    else:
        for row in values:
            if (row[0] == student_id):
                print(row[0])
                print(row[1])
                print(row[2])
                print(row[3])
                print(row[4])
                print(row[5])
        # search_string = '{}-'.format(session_id)
        # for row in values:
        #     if row[0].startswith(search_string):
        #         return_string = row[0]
        #         return_string = return_string[return_string.find('-') + 1:]
        #         return return_string

def main():
    student_id = '1111'
    row = get_marks_from_google_sheet(student_id)

if __name__ == '__main__':
    main()

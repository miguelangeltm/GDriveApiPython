"""
Drive API Python v1.2
Author: Miguel Angel Torres
v1.0: Sept 10 - 2021
v1.2: Sept 20 - 2021
Update: did the dataBaseSends function
       _____          _                             _____ _____                 _____       _   _                 
      |  __ \        (_)                      /\   |  __ \_   _|        _      |  __ \     | | | |                
      | |  | | _ __   _   __   __   ___      /  \  | |__) || |        _| |_    | |__) |   _| |_| |__   ___  _ __  
      | |  | || '__| | |  \ \ / /  / _ \    / /\ \ |  ___/ | |       |_   _|   |  ___/ | | | __| '_ \ / _ \| '_ \ 
      | |__| || |    | |   \ V /  |  __/   / ____ \| |    _| |_        |_|     | |   | |_| | |_| | | | (_) | | | |
      |_____/ |_|    |_|    \_/    \___|  /_/    \_\_|   |_____|               |_|    \__, |\__|_| |_|\___/|_| |_|
  ______  ______ ______ ______ ______ ______       ______    ______ ______ ______      __/ |                      
 |______||______|______|______|______|______|     |______|  |______|______|______|    |___/                       

# !Important:  pip install -r requirements.txt

"""

# Imports from PyDrive library
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
# Imports from Drive API v3
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
# Miscellaneous Imports
from datetime import datetime
from pymongo import MongoClient
import json
import sys

#Init Config Variables
credentials_path = 'credentials_module.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = Credentials.from_authorized_user_file('credentials_module.json', SCOPES)
client = MongoClient('mongodb://localhost:27017')


#[Pydrive] Login Function
def login():
    gAuth = GoogleAuth()
    gAuth.LoadCredentialsFile(credentials_path)

    if gAuth.access_token_expired:
        gAuth.Refresh()
        gAuth.SaveCredentialsFile(credentials_path)
    else:
        gAuth.Authorize()
    return GoogleDrive(gAuth)


def main():
        
    # Reset arg script. Delete collection
    args = sys.argv[1:]
    if len(args) == 1 and args[0] == '-reset':
        db = client['GoogleDriveFiles']
        print('*************************')
        print('***** FACTORY RESET ***** ')
        first_token ={"first_token": 0}
        with open("flagFirstToken.json", "w") as outfile:
            json.dump(first_token, outfile)
        print('First token = 0')
        db.files.drop()
        print("'files'" 'collection wiped')
        print('Factory reset finished.')
        print('*************************')
        print('*************************')
        sys.exit()

    #Creates a Google API instance
    drive = login() 
    #Creates a Drive API v3 service
    service = build('drive', 'v3', credentials=creds)
    #Get files from Drive API 
    get_files = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    var = open('flagFirstToken.json', 'r').read()
    json_object = json.loads(var)
    first_token = json_object["first_token"]
    if(first_token == 0):
        print('Storing Database...')
        dataBaseSends(get_files, 'insert')
        print('Database saved!')
        response = service.changes().getStartPageToken().execute()
        start_token = response.get('startPageToken') 
        page_token = {"page_token" : start_token}      
        first_token ={"first_token": 1}
        with open("flagFirstToken.json", "w") as outfile:
            json.dump(first_token, outfile)
        with open("pageToken.json", "w") as outfile:
            json.dump(page_token, outfile)
    else:
        var = open('pageToken.json', 'r').read()
        saved_start_page_token = json.loads(var)
        page_token = saved_start_page_token["page_token"]
        response = service.changes().getStartPageToken().execute()
        current_token = response.get('startPageToken')
        if(current_token == page_token):
         print('No changes detected. The database has already been saved')
         print('Current Token:', current_token)
        else:
            response = service.changes().getStartPageToken().execute()
            start_token = response.get('startPageToken')
            page_token = {"page_token" : start_token}
            with open("pageToken.json", "w") as outfile:
                json.dump(page_token, outfile)
            print('Actualizando Base de datos:')
            get_files = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
            dataBaseSends(get_files, 'upsert')

def saveChangePermission(permission_change):
    with open('ChangeLogs.txt', 'a') as f:
        f.write("\n")
        f.write("\n")
        f.write('\n'.join(permission_change))
        f.close()

def dataBaseSends(get_files, action):
    #Creates a Mongo Database (GoogleDriveFiles) and a Collection (col)        
    db = client['GoogleDriveFiles']
    col = db['files']
    list_of_files = []
    for f in get_files:
        permissions = f.GetPermissions() # Retrieve permissions from file in f 
        owners = f['owners']             # Retrieve owners' info from file in f 
        OwnerMail = owners[0]['emailAddress'] 
        # Detecting Public files:
        if(permissions[0]['type']=='anyone'):
        #Notification by Email
            f.InsertPermission({'type': 'user',
                                'value': OwnerMail,
                                'role': 'writer'},
                                sendNotificationEmails=True,
                                emailMessage='Public access Detected. Google Drive API has changed access to restricted')
            now = datetime.now()
            date_string = now.strftime("%d/%m/%Y %H:%M:%S")
            permission_change = ['>> Public access Detected. File Name: ',f['title'], 'Change to restricted at:', date_string]
            saveChangePermission(permission_change)
            #Changing Permission to restricted:
            permission_id = permissions[0]['id']
            f.DeletePermission(permission_id)
            #hasta aquí son iguales
        file_data = {'fileName': f['title'], 
                    'fileExtension': f.get('fileExtension'),
                    'Owner': owners[0]['displayName'],
                    'Access for' : permissions[0]['type'],
                    'modified': f['modifiedDate']
                    }
        list_of_files.append(file_data)
    if(action == 'insert'):
        col.insert_many(list_of_files)
    elif(action == 'upsert'):
        key = {'fileName': f['title']}
        value = { "$set": {"fileName": f['title'], "fileExtension": f.get('fileExtension'), "Owner": owners[0]['displayName'],"Access for" : permissions[0]['type'], "modified": f['modifiedDate'] } }
        db.files.update_many(key, value, upsert=True);

if __name__ == "__main__":
   
    print("""

       _____          _                             _____ _____                 _____       _   _                 
      |  __ \        (_)                      /\   |  __ \_   _|        _      |  __ \     | | | |                
      | |  | | _ __   _   __   __   ___      /  \  | |__) || |        _| |_    | |__) |   _| |_| |__   ___  _ __  
      | |  | || '__| | |  \ \ / /  / _ \    / /\ \ |  ___/ | |       |_   _|   |  ___/ | | | __| '_ \ / _ \| '_ \ 
      | |__| || |    | |   \ V /  |  __/   / ____ \| |    _| |_        |_|     | |   | |_| | |_| | | | (_) | | | |
      |_____/ |_|    |_|    \_/    \___|  /_/    \_\_|   |_____|               |_|    \__, |\__|_| |_|\___/|_| |_|
  ______  ______ ______ ______ ______ ______       ______    ______ ______ ______      __/ |                      
 |______||______|______|______|______|______|     |______|  |______|______|______|    |___/                       

# !Important:  Don't forget install requirements. Type on your console >> pip install -r requirements.txt

""")

    print('Drive API Python v1.2')
    print('Author: Miguel Angel Torres')
    print('Date: Sept 20 - 2021')
    main()


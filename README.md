## GDriveApiPython
A python app which connects Google Drive API with a MongoDB Database

### Project Info

The app developed in python makes an inventory of the belonging files to a user's Google Drive, making requests through the google API, and later creates a database in mongoDB with that info:

#### Relation diagram 
 
![image](https://user-images.githubusercontent.com/43521047/134109383-cd784453-4bb2-4798-834d-2954a01ba56c.png)

#### Database graphical representation

![image](https://user-images.githubusercontent.com/43521047/134111213-36b8daac-9042-4d4a-8943-f432cb960ccf.png)


### Requirements

:snake: Python 3.x

🍃 Mongo DB Community Server 5.0.2

🔑 Google Drive account key + Google API OAuth 2.0 keys  
> https://developers.google.com/drive/api/v3/enable-drive-api

You need to create client_secrets.json (google API keys) and credentials_module.json (Google Drive user keys) and writting on settings.yaml config file. 

### Usage

Just download the .zip file, enable your Google API console, grab the keys and that's all...

# Trellonotify
forked from https://github.com/cloudsavant/trellonotify-gcp-based 

A lightweight tool designed to seamlessly integrate with Trello, automatically generating Trello cards for upcoming tasks and events. Say goodbye to forgotten tasks and missed deadlines, and let Trellonotify keep your Trello boards up-to-date with timely reminders.

The cloud based version will be migrated into a containerized version. 

# Migration Plan
1. Migrate back to NAS and use the built-in scheduler (leave file-based DB).
2. Migrate file-based DB to a MySQL database.
3. Containerize the tool using Docker and run it with the NAS built-in scheduler.
4. Transition to a container-based scheduler and database to reduce dependency on NAS services.
5. Develop a simple Python-based admin UI for the database.

# Architecture
- Google Cloud Storage: to store data files
- Google Cloud Functions: to process data files
- Google Cloud Scheduler: to trigger cloud functions
- Google Secret Manager: to store secrets
- Slack: to send notifications
- Trello: to store tasks
- Terraform: to manage infrastructure

# Requirements
1. GCP account

# Setup
## Terraform setup on windows
- Download terraform.exe
- add to windows path

## GCP Project setup
'''
gcloud auth login
gcloud config set project xxxx
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com --project=trellonotify-401705
gcloud services enable cloudscheduler.googleapis.com --project=trellonotify-401705
gcloud services enable cloudresourcemanager.googleapis.com --project=trellonotify-401705
gcloud services enable iam.googleapis.com --project=trellonotify-401705
gcloud services enable secretmanager.googleapis.com --project=trellonotify-401705

'''

## Terraform setup with GCP
### Create Service account
1. In the GCP Console, go to "IAM & Admin" → "Service Accounts".
2. Create a new service account, and download the key as a JSON file.
2.1 For simplicity, we add project/editor role to this account. Later we can narrow it.
2.2 Create new key in JSON format
3. Set an environment variable named GOOGLE_APPLICATION_CREDENTIALS pointing to the path of the downloaded JSON key.
4. remember the email from service account: SERVICE_ACCOUNT_EMAIL
5. run 
'''gcloud projects add-iam-policy-binding trellonotify-401705 --member=serviceAccount:<SERVICE_ACCOUNT_EMAIL> --role=roles/cloudfunctions.admin

gcloud projects add-iam-policy-binding trellonotify-401705 --member=serviceAccount:<SERVICE_ACCOUNT_EMAIL> --role=roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding trellonotify-401705 --role roles/secretmanager.secretAccessor --member serviceAccount:trellonotify-401705@appspot.gserviceaccount.com
'''
6. Initialize your Terraform project using terraform init.

7. add secrets to project manually
- Add new version for TRELLO_LIST_ID
- Add new version for TRELLO_KEY
- Add new version for TRELLO_TOKEN

8. create Slack app
To send a message to Slack from a Google Cloud Function using Python, you can use the requests library to make an HTTP POST request to Slack's API. Here are the steps to achieve this:

- Create a Slack App:
    Go to the Slack API website (https://api.slack.com/).
    Create a new Slack App or use an existing one.
- Configure OAuth & Permissions:
    Part: OAuth Tokens for Your Workspace generate Bot User OAuth Token
    Part Scopes: grant your app the chat:write or chat:write.customize, chat:write.public scope, depending on your use case.
- Install the App:
    Install the Slack App to your workspace. This will generate an OAuth token that you'll use to authenticate your cloud function.

9. add secrets to project manually
- Add new version for SLACK_API_TOKEN
- Add new version for SLACK_CHANNEL_ID



# Application setup
## main.tf modification
- change google project id: xxxxx
- change source bucket name: xxxxx

## deploy.sh modification
- change source BUCKET_NAME: xxxxx

## python env
'''
virtualenv.exe trellonotify
.\trellonotify\Scripts\activate
.\trellonotify\Scripts\Activate.ps1

pip install google-cloud-storage
pip install google-cloud-secret-manager
pip freeze > app/requirements.txt
'''

# Application infrastructure setup
```
terraform -chdir=terraform init
terraform -chdir=terraform apply
```
# Application deployment
```
.\scripts\deploy.ps1
```

# upload data file to cloud
```
gcloud storage cp c:\Users\buxib\Downloads\db.csv gs://trellonotify-files-bucket/db.csv 
```

# download data file from cloud
```
gcloud storage cp  gs://trellonotify-files-bucket/db.csv c:\Users\buxib\Downloads\db.csv
```

# TODOs
## Narrow terraform service account roles
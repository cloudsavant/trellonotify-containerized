import logging
from google.cloud import secretmanager
from google.cloud import storage

import pandas as pd
import datetime
import requests
import json
import io
from io import BytesIO

pd.options.mode.chained_assignment = None

CSV_DATA_FILE = "db.csv"

def get_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    # Build the resource name of the secret version.
    name = f"projects/trellonotify-401705/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(name=name)

    # Return the decoded payload.
    return response.payload.data.decode('UTF-8')

def read_gcs_csv_to_dataframe(bucket_name, file_name):
    # Create a GCS client
    client = storage.Client()

    # Get the bucket and blob (file) references
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the blob content as a byte stream
    content_as_bytes = blob.download_as_bytes()

    # Use pandas to read the CSV content
    df = pd.read_csv(io.BytesIO(content_as_bytes))
    
    return df

def write_dataframe_to_gcs(df, bucket_name, file_name):
    """
    Writes a pandas DataFrame to a GCS bucket.

    Args:
    - df (pd.DataFrame): The DataFrame to write.
    - bucket_name (str): The name of the GCS bucket.
    - file_name (str): The destination file name in the GCS bucket.
    """
    
    # Create a GCS client
    client = storage.Client()

    # Get the bucket reference
    bucket = client.bucket(bucket_name)

    # Use BytesIO to capture the DataFrame's CSV output
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    # Create or overwrite the blob (file) in GCS
    blob = bucket.blob(file_name)
    blob.upload_from_file(buffer, content_type='text/csv')

# Trello list 
TRELLO_LIST_ID =  get_secret('TRELLO_LIST_ID')
TRELLO_ENDPOINT = 'https://api.trello.com/1/'

#function to bucket the days left info
def datedelta(delta):
    # TODO refactor something like this, it not works yet
    # bins = pd.IntervalIndex.from_tuples([(-1000, 0), (1, 10), (11, 30), (31, 60), (61, 90), (91, 1000)])
    # pd.cut(np.array([-1,2,11,31,61,91]), bins, labels=["-1", "10", "30", "60", "90", "91"] , retbins = True)
    if (delta < 0):
        return -1
    if (delta <= 1):
        return 1
    elif(delta <= 10):
        return 10
    elif(delta <= 30):
        return 30
    elif(delta <= 60):
        return 60
    elif(delta <= 90):
        return 90
    return 91

def create_trello_card(card_name, card_description, due_date, list_id):
    create_card_endpoint = TRELLO_ENDPOINT + "cards"
    date_str = due_date.strftime("%b %d %Y %H:%M:%S")
    jsonObj = {"key":  get_secret('TRELLO_KEY'),
               "token":  get_secret('TRELLO_TOKEN'),
               "idList": list_id,
               "name": card_name,
               "desc": card_description,
               "due": date_str
               }
    new_card_Json = requests.post(create_card_endpoint, json=jsonObj)
    jsonStr = json.dumps(new_card_Json.json(), indent=1)
    new_card = json.loads(jsonStr)
    return new_card['id']

def create_recurring_row(row):
    enddate = datetime.datetime.strptime(row['enddate'], "%Y-%m-%d")
    new_enddate = enddate + datetime.timedelta(days=row['recurring_days'])

    noticabletill = datetime.datetime.strptime(
        row['noticabletill'], "%Y-%m-%d")
    new_noticabletill = noticabletill + \
        datetime.timedelta(days=row['recurring_days'])

    new_row = row.copy()
    new_row['enddate'] = new_enddate.strftime("%Y-%m-%d")
    new_row['noticabletill'] = new_noticabletill.strftime("%Y-%m-%d")
    new_row['id'] = row['id']+100

    return new_row

# generate output for one bucket
def generate_output_rows4group(df, group):
    output = "\t id:{} active:{} where: {} {} enddate:{} noticable till: {}"
    output_rows = df[df['days'] == group].apply(
        lambda row: output.format(
            row['id'], row['active'], row['company'],
            row['contract'],  row['enddate'], row['noticabletill']),
        axis=1)
    return '' if output_rows.empty else '\n'.join(output_rows)


def send_message_to_slack(message):
    # Replace with your Slack API token and channel ID
    slack_token = get_secret('SLACK_API_TOKEN')
    channel_id = get_secret('SLACK_CHANNEL_ID')

    url = "https://slack.com/api/chat.postMessage"

    # Create the payload for the request
    payload = {
        "channel": channel_id,
        "text": message,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {slack_token}",
    }

    # Send the message to Slack
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        return "Message sent to Slack successfully"
    else:
        return "Failed to send message to Slack"



def test_function(request):
    # loading db
    df_original = read_gcs_csv_to_dataframe("trellonotify-files-bucket", CSV_DATA_FILE)

    #converting db, using only active rows, generating days left column
    df = df_original[df_original['active'] == True]
    df['delta'] = pd.to_datetime(df['noticabletill']) - \
        pd.to_datetime(datetime.date.today())
    df['days'] = df['delta'].dt.days

    # converting days to buckets (<0, 0-1, 1-10, 11-30, 31-60, 61-90, <90)
    df['days'] = df.days.apply(datedelta)

    #get 1 day and 10 day tickets
    todolist = df[(df['days'] == 1) | (df['days'] == 10)]

    todolist = todolist.fillna('')
    tickets_created =[]
    for _ , todo in todolist.iterrows():
        name = '#%s - %s' % (todo['id'], todo['contract'])
        description = '%s\nenddate: %s' % (
            todo['notice_period-description'], todo['enddate'])
        duedate = datetime.datetime.strptime(todo['noticabletill'], "%Y-%m-%d")
        #print(todo['trello-ticket-id'])
        if todo['trello-ticket-id']:
            msg = 'Skipping todo: %s' % todo['id']
            logging.info(msg)
            send_message_to_slack(msg)
            continue 
        ticket_id = create_trello_card(
            name, description, duedate, TRELLO_LIST_ID)
        #print('creating ticket for todo id:%s - ticket_id:%s' % (todo['id'], ticket_id))
        
        # updating row with ticket_id
        df_original.loc[df_original.id == todo['id'], 'trello-ticket-id'] = ticket_id
        tickets_created.append(str(todo['id']))

        if todo['recurring'] == True:
            new_row = create_recurring_row(todo)
            # add new row to dataframe
            df_original.loc[-1] = new_row

        # deactivating row
        df_original.loc[df_original.id == todo['id'],
                        'active'] = False

    # saving all data back to db file
    write_dataframe_to_gcs(df_original, "trellonotify-files-bucket", CSV_DATA_FILE)

    daygroups = {-1: 'overdue', 1: '1 day time', 10: '10 day time'}#, 30: '30 day time',60: '60 day time', 90: '90 day time', 91: '90+ day time'}
    output = 'tickets created:' + ','.join(tickets_created) + '\n'
    logging.info(f"{output}")
    send_message_to_slack(output)

    for daygroup in daygroups.keys(): 
        msg = f"{daygroups[daygroup]}\n{generate_output_rows4group(df, daygroup)}"
        print(msg)
        send_message_to_slack(msg)

    # Send the message to Slack using the imported function
    message = 'All done, exiting"!'
    result = send_message_to_slack(message)
    
    logging.info(result)

    return message, 200

if __name__ == "__main__":
    # This block is for local testing and will not be executed in GCP environment
    test_function(None)
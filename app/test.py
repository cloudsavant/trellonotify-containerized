import logging
from google.cloud import secretmanager
from google.cloud import storage

def get_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    # Build the resource name of the secret version.
    name = f"projects/trellonotify-401705/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(name=name)
    print(f'response={response}')
    # Return the decoded payload.
    return response.payload.data.decode('UTF-8')

def read_and_log_gcs_file(bucket_name, file_name):
    # Create a client
    client = storage.Client()

    # Get the bucket and blob (file) references
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the file content as a string
    file_content = blob.download_as_text()

    # Log the content
    print(file_content)

def test_function(request):
    """ Cloud Function to be triggered by HTTP.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        str: The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    logging.info('Hello in GCP nnnnnnn')
    resp = get_secret('TRELLO_LIST_ID')
    print(f'resp={resp}')
    logging.info(f'resp={resp}')
    read_and_log_gcs_file("trellonotify-files-bucket", "test-data.txt")
    return 'Logged "Hello in GCP"!', 200

if __name__ == "__main__":
    # This block is for local testing and will not be executed in GCP environment
    print('main called')
    test_function(None)
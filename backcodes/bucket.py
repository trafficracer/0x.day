import boto3
from botocore.config import Config

ACCESS_KEY = "2EF872A62061001F28F7"
SECRET_KEY = "qq1EjmvKg2WcTor8Zo3COVPksEPfsSFN0NNfqmwc"
FILEBASE_ENDPOINT = "https://s3.filebase.com"

s3_client = boto3.client(
    's3',
    endpoint_url=FILEBASE_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version='s3v4')
)

try:
    response = s3_client.list_buckets()
    print("Buckets:", response['Buckets'])
except Exception as e:
    print("Error:", e)

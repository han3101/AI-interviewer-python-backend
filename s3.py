import logging
import boto3
import mimetypes, os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_ENPOINT = os.environ.get('CLOUDFLARE_ENDPOINT')
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
ACCESS_KEY = os.environ.get('ACCESS_KEY')

# print(ACCESS_KEY_ID)
# print(CLOUDFLARE_ENPOINT)
# ACCESS_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')

s3 = boto3.resource('s3',
  endpoint_url = CLOUDFLARE_ENPOINT,
  aws_access_key_id = ACCESS_KEY_ID,
  aws_secret_access_key = ACCESS_KEY
)

# print('Buckets:')
# for bucket in s3.buckets.all():
#   print(' - ', bucket.name)

# print('Objects:')
# for item in bucket.objects.all():
#   print(' - ', item.key)


def upload_file(file_url: str, bucket: str, object_name: str=None):
    """Upload a file to an S3 bucket

    :param file_url: Path of file to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    # TODO proper naming convention, probably based on event_id
    if object_name is None:
        object_name = os.path.basename(file_url)

    # Create boto3 client
    try:
        s3_client = s3.meta.client
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False
    

    # Upload the file
    try:
        with open(file_url, 'rb') as file_data:
            response = s3_client.put_object(Bucket=bucket, Key=object_name, Body=file_data)
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

def download_file(bucket_name: str, object_name: str, local_file_path: str):

    # Create boto3 client
    try:
        s3_client = s3.meta.client
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False
    
    # Get Object Type
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_name)
        object_type = response.get('ContentType')
    except Exception as e:
        print(f"An error occurred while getting object content type: {e}")
        object_type = None

    # Add object_type extension to file_path
    if object_type:
        extension = mimetypes.guess_extension(object_type)
        if extension:
            local_file_path = f"{local_file_path}{extension}"

    # Download the file
    try:
        s3_client.download_file(bucket_name, object_name, local_file_path)
        print(f'Successfully downloaded {object_name} to {local_file_path}')
        return True
    except ClientError as e:
        logging.error(e)
        return False

    


# Generates a url which can be passed into streamer for transcription
def create_presigned_url(bucket_name: str, object_name: str, expiration: int=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Create boto3 client
    try:
        s3_client = s3.meta.client
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    # Generate a presigned URL for the S3 object
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


# Delete object
def delete_file(bucket_name: str, object_name: str):
    
    # Create boto3 client
    try:
        s3_client = s3.meta.client
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False
    
    # Delete object
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        return True

    except Exception as e:
        print(f"An error occurred while deleting the object: {e}")
        return False

# FILE_PATH = "pre_recorded_audio/begin_interview.mp3"
# upload = upload_file(FILE_PATH, "apriora", "test1.mp3")
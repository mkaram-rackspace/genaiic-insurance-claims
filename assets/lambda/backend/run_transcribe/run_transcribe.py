import json
import boto3
import os
import logging
import time
from urllib.parse import unquote_plus

#########################
#       CONSTANTS
#########################

S3_BUCKET = os.environ["BUCKET_NAME"]

LOGGER = logging.Logger("TEXTRACT", level=logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


def lambda_handler(event, context):
    # parse event
    if "requestContext" in event:
        LOGGER.info("Received HTTP request.")
        body = json.loads(event["body"])
    else:  # step functions invocation
        body = event["body"]
    LOGGER.info(f"Received input: {body}")


    # Initialize AWS clients
    transcribe = boto3.client('transcribe')
    s3 = boto3.client('s3')
    
    # Get the S3 bucket and file key from the event
    source_key = body["file_name"]
    
    # Get environment variables
    output_bucket = os.environ['OUTPUT_BUCKET']
    
    try:
        # Create a unique job name (using timestamp to avoid conflicts)
        job_name = f"transcription_{int(time.time())}"
        
        # Get the file extension
        file_extension = source_key.split('.')[-1].lower()
        
        # Construct the S3 URI for the source audio file
        media_uri = f"s3://{S3_BUCKET}/{source_key}"
        
        # Start transcription job
        output_key = f"transcripts/{source_key.split('/')[-1]}.txt"

        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat=file_extension,
            LanguageCode='en-US',  # You can modify this based on your audio language
            OutputBucketName=output_bucket,
            OutputKey=output_key
        )
        
        # Wait for the transcription job to complete
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)
        
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            output_location = f"s3://{output_bucket}/transcripts/{source_key.split('/')[-1]}.txt"

            obj = s3.get_object(Bucket=output_bucket, Key=output_key)
            data = obj["Body"].read().decode('utf8')
            json_data = json.loads(data)
            content = json_data["results"]["transcripts"][0]["transcript"]
            response = s3.put_object(
                Bucket=output_bucket,
                Key = f"transcripts/{source_key.split('/')[-1]}_plain.txt",
                Body=content.encode('utf-8'))

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'message': 'Transcription completed successfully',
                    'jobName': job_name,
                    'outputLocation': output_location,
                    'content': content,
                    'output': json_data
                })
            }
        else:
            raise Exception("Transcription job failed")
            
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing transcription',
                'error': str(e)
            })
        }

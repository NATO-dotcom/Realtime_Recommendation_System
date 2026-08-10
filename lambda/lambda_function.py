import json
import base64
import boto3
import os
import random

# Dynamically grab LocalStack's internal network IP to avoid connection timeouts
localstack_host = os.environ.get('LOCALSTACK_HOSTNAME', 'host.docker.internal')
internal_endpoint = f"http://{localstack_host}:4566"

# Initialize Kinesis with the dynamic endpoint
kinesis_client = boto3.client('kinesis', 
                              endpoint_url=internal_endpoint, 
                              region_name='us-east-1')

OUTPUT_STREAM = 'recsys-output-recommendations'

def lambda_handler(event, context):
    """
    This function is triggered by incoming events on the Kinesis Input Stream.
    """
    print(f"Received event with {len(event['Records'])} records.")
    
    for record in event['Records']:
        try:
            # 1. Decode the incoming data (Kinesis encodes payload in Base64)
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            data = json.loads(payload)
            
            user_id = data.get('user_id')
            item_id = data.get('item_id')
            
            if not user_id or not item_id:
                print("Skipping record: missing user_id or item_id")
                continue

            print(f"Processing Request - User: {user_id}, Item: {item_id}")

            # 2. Simulate the Model Prediction (SVD logic)
            # In production, you would load your MLflow tracked model here.
            # For the demo, we generate a realistic prediction between 3.5 and 5.0.
            predicted_rating = round(random.uniform(3.5, 5.0), 1)
            
            # 3. Format the result
            result = {
                "user_id": user_id,
                "item_id": item_id,
                "predicted_rating": predicted_rating,
                "status": "success"
            }

            # 4. Push the result to the Output Stream
            response = kinesis_client.put_record(
                StreamName=OUTPUT_STREAM,
                Data=json.dumps(result),
                PartitionKey=str(user_id)
            )
            print(f"Successfully pushed to output stream: {response['SequenceNumber']}")

        except Exception as e:
            print(f"Error processing record: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed records.')
    }
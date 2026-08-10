import json
import boto3

# Connect to LocalStack's Kinesis endpoint
kinesis = boto3.client('kinesis', endpoint_url='http://localhost:4566', region_name='us-east-1')

payload = {
    "user_id": 42,
    "item_id": 101
}

print("Sending user event to recsys-input-events stream...")
response = kinesis.put_record(
    StreamName='recsys-input-events',
    Data=json.dumps(payload),
    PartitionKey=str(payload['user_id'])
)

print(f"✅ Event sent successfully! Sequence Number: {response['SequenceNumber']}")

import json
import base64
import boto3
import time

# Connect to LocalStack's Kinesis endpoint
kinesis = boto3.client('kinesis', endpoint_url='http://localhost:4566', region_name='us-east-1')
STREAM_NAME = 'recsys-output-recommendations'

print(f"Connecting to {STREAM_NAME}...")

# 1. Describe the stream to find its Shard ID
response = kinesis.describe_stream(StreamName=STREAM_NAME)
shard_id = response['StreamDescription']['Shards'][0]['ShardId']

# 2. Get a Shard Iterator to tell Kinesis we want the oldest unread records
shard_iterator_response = kinesis.get_shard_iterator(
    StreamName=STREAM_NAME,
    ShardId=shard_id,
    ShardIteratorType='TRIM_HORIZON' # Start from the oldest available record
)
shard_iterator = shard_iterator_response['ShardIterator']

print("Listening for recommendations...")

# 3. Continuously poll the stream for new records
while True:
    record_response = kinesis.get_records(
        ShardIterator=shard_iterator,
        Limit=100
    )
    
    for record in record_response['Records']:
        # Kinesis stores the payload as Base64 encoded bytes, so we must decode it
        payload_bytes = record['Data']
        payload_str = payload_bytes.decode('utf-8')
        prediction = json.loads(payload_str)
        
        print("\n🔔 New Recommendation Received!")
        print(json.dumps(prediction, indent=2))
    
    # Get the next iterator for the next polling cycle
    shard_iterator = record_response['NextShardIterator']
    
    # Polling too fast can hit AWS limits; pause briefly
    time.sleep(2)

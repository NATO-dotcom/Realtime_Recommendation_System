import json
import boto3
import time
import random

# Connect to LocalStack's Kinesis endpoint
kinesis = boto3.client('kinesis', endpoint_url='http://localhost:4566', region_name='us-east-1')

print("🚀 Starting live traffic simulation... (Press Ctrl+C to stop)")

try:
    while True:
        # Generate random user and movie IDs
        payload = {
            "user_id": random.randint(1, 1000),
            "item_id": random.randint(1, 500)
        }

        response = kinesis.put_record(
            StreamName='recsys-input-events',
            Data=json.dumps(payload),
            PartitionKey=str(payload['user_id'])
        )

        # Print just the last 10 characters of the Sequence Number to keep the terminal clean
        short_seq = response['SequenceNumber'][-10:]
        print(f"📡 Sent User: {payload['user_id']:<4} | Item: {payload['item_id']:<3} | Seq: ...{short_seq}")
        
        # Pause randomly between 0.5 and 2 seconds
        time.sleep(random.uniform(0.5, 2.0))

except KeyboardInterrupt:
    print("\n🛑 Traffic simulation stopped.")

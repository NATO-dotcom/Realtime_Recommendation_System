import boto3
import json
import sys

def test_kinesis_stream():
    print("Initiating CI/CD Integration Test...")
    
    # Connect to the LocalStack instance running inside the GitHub Action runner
    kinesis = boto3.client(
        'kinesis',
        endpoint_url='http://localhost:4566',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    test_event = {
        'user_id': 'ci_cd_test_user_001',
        'action': 'view',
        'item_id': 'test_item_999'
    }
    
    try:
        response = kinesis.put_record(
            StreamName='recsys-input-events',
            Data=json.dumps(test_event),
            PartitionKey='user_id'
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ SUCCESS: Test event accepted by Kinesis. Shard ID: {response['ShardId']}")
            sys.exit(0)  # Tells GitHub Actions the test passed
        else:
            print("❌ ERROR: Stream responded with non-200 status.")
            sys.exit(1)  # Tells GitHub Actions to fail the build
            
    except Exception as e:
        print(f"❌ TEST FAILED: Could not connect to Kinesis stream. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_kinesis_stream()

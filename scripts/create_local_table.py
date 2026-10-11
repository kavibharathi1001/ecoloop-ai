import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://127.0.0.1:8000",
    region_name="ap-south-1",
    aws_access_key_id="local",
    aws_secret_access_key="local",
)

table_name = "EcoLoopActions-local"

try:
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "sessionId", "KeyType": "HASH"},
            {"AttributeName": "createdAt", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "sessionId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "S"},
            {"AttributeName": "actionId", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "ActionIdIndex",
                "KeySchema": [
                    {"AttributeName": "actionId", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Created DynamoDB Local table: {table_name}")

except ClientError as exc:
    if exc.response["Error"]["Code"] == "ResourceInUseException":
        print(f"Table already exists: {table_name}")
    else:
        raise
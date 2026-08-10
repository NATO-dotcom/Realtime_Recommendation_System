terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# aws provider
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    kinesis = "http://localhost:4566"
    iam     = "http://localhost:4566"
    lambda  = "http://localhost:4566"
  }
}
# 1. The Input Stream (Frontend apps send user clicks here)
resource "aws_kinesis_stream" "input_stream" {
  name             = "recsys-input-events"
  shard_count      = 1
  retention_period = 24
}

# 2. The Output Stream (Lambda pushes recommendations here)
resource "aws_kinesis_stream" "output_stream" {
  name             = "recsys-output-recommendations"
  shard_count      = 1
  retention_period = 24
}

# 3. IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "recsys_lambda_kinesis_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# 4. Give Lambda permission to read/write to Kinesis and log to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_kinesis_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
# 5. Define the AWS Lambda Function
resource "aws_lambda_function" "recsys_processor" {
  filename         = "../../lambda/lambda_function.zip"
  function_name    = "recsys-stream-processor"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = filebase64sha256("../../lambda/lambda_function.zip")

  environment {
    variables = {
      STAGE = "dev"
    }
  }
}

# 6. Event Source Mapping (Connect Kinesis Input Stream -> Lambda Trigger)
resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn  = aws_kinesis_stream.input_stream.arn
  function_name     = aws_lambda_function.recsys_processor.arn
  starting_position = "LATEST"
  batch_size        = 100
}
#!/usr/bin/env bash
# One-time AWS setup for storage and alerts (Step 7). Daily ingest itself runs on the laptop
# (infra/register_daily_task.ps1) because data.gov.in refuses connections from AWS.
# Usage: BUCKET=<bucket> ALERT_EMAIL=<email> ./infra/setup_aws.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}" "${ALERT_EMAIL:?set ALERT_EMAIL}"
REGION=$(aws configure get region)

echo "== S3 bucket $BUCKET"
aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration file://infra/s3-lifecycle.json

echo "== Alert topic"
TOPIC=$(aws sns create-topic --name mandi-alerts --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC" --protocol email --notification-endpoint "$ALERT_EMAIL" >/dev/null

echo "Done. Confirm the SNS email, then add to .env: S3_BUCKET=$BUCKET and ALERT_TOPIC_ARN=$TOPIC"

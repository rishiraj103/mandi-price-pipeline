#!/usr/bin/env bash
# One-time AWS setup for daily ingestion (Step 7).
# Prerequisite (run yourself, never save the key in a file):
#   aws ssm put-parameter --name /mandi/api_key --type SecureString --value <key>
# Usage: BUCKET=<bucket> ALERT_EMAIL=<email> ./infra/setup_aws.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}" "${ALERT_EMAIL:?set ALERT_EMAIL}"
REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
fill() { sed -e "s/BUCKET/$BUCKET/g" -e "s/ACCOUNT/$ACCOUNT/g" -e "s/REGION/$REGION/g" "$1"; }

echo "== S3 bucket $BUCKET"
aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration file://infra/s3-lifecycle.json

echo "== IAM roles"
aws iam create-role --role-name lambda-ingest-role \
  --assume-role-policy-document file://infra/policies/lambda-trust.json >/dev/null
aws iam put-role-policy --role-name lambda-ingest-role --policy-name ingest \
  --policy-document "$(fill infra/policies/lambda-ingest-policy.json)"
aws iam create-role --role-name scheduler-ingest-role \
  --assume-role-policy-document file://infra/policies/scheduler-trust.json >/dev/null
aws iam put-role-policy --role-name scheduler-ingest-role --policy-name invoke \
  --policy-document "$(fill infra/policies/scheduler-invoke-policy.json)"
sleep 10   # new roles take a few seconds before Lambda can assume them

echo "== Lambda"
./infra/deploy_ingest.sh

echo "== Schedule 07:00 Asia/Kolkata"
aws scheduler create-schedule --name ingest-daily-7am \
  --schedule-expression "cron(0 7 * * ? *)" --schedule-expression-timezone Asia/Kolkata \
  --flexible-time-window Mode=OFF \
  --target "Arn=arn:aws:lambda:$REGION:$ACCOUNT:function:ingest_daily,RoleArn=arn:aws:iam::$ACCOUNT:role/scheduler-ingest-role" >/dev/null

echo "== Alerts"
TOPIC=$(aws sns create-topic --name mandi-alerts --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC" --protocol email --notification-endpoint "$ALERT_EMAIL" >/dev/null
aws cloudwatch put-metric-alarm --alarm-name ingest-daily-errors \
  --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=ingest_daily \
  --statistic Sum --period 300 --evaluation-periods 1 --threshold 0 \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching \
  --alarm-actions "$TOPIC"

echo "Done. Confirm the SNS subscription email sent to $ALERT_EMAIL."

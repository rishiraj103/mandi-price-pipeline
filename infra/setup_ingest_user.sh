#!/usr/bin/env bash
# Least-privilege IAM user for the laptop's daily ingest: may only write raw/ and publish the alert.
# Stores its key as AWS CLI profile "mandi-ingest"; ingest/daily.py uses it when INGEST_AWS_PROFILE is set.
# Usage: BUCKET=<bucket> ./infra/setup_ingest_user.sh   then add INGEST_AWS_PROFILE=mandi-ingest to .env
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}"
REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
fill() { sed -e "s/BUCKET/$BUCKET/g" -e "s/ACCOUNT/$ACCOUNT/g" -e "s/REGION/$REGION/g" "$1"; }

aws iam create-user --user-name mandi-ingest >/dev/null
aws iam put-user-policy --user-name mandi-ingest --policy-name ingest \
  --policy-document "$(fill infra/policies/ingest-user-policy.json)"
read -r KEY SECRET < <(aws iam create-access-key --user-name mandi-ingest \
  --query "AccessKey.[AccessKeyId,SecretAccessKey]" --output text | tr -d '\r')   # Windows CLI adds \r
aws configure set aws_access_key_id "$KEY" --profile mandi-ingest
aws configure set aws_secret_access_key "$SECRET" --profile mandi-ingest
aws configure set region "$REGION" --profile mandi-ingest
echo "Profile mandi-ingest ready (key stored in ~/.aws/credentials, not printed)."

#!/usr/bin/env bash
# One-time AWS setup for the transform and Athena (Step 8). Run after setup_aws.sh.
# Usage: BUCKET=<bucket> ./infra/setup_transform.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}"
REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
fill() { sed -e "s/BUCKET/$BUCKET/g" -e "s/ACCOUNT/$ACCOUNT/g" -e "s/REGION/$REGION/g" "$1"; }

echo "== IAM role"
aws iam create-role --role-name lambda-transform-role \
  --assume-role-policy-document file://infra/policies/lambda-trust.json >/dev/null
aws iam put-role-policy --role-name lambda-transform-role --policy-name transform \
  --policy-document "$(fill infra/policies/lambda-transform-policy.json)"
sleep 10

echo "== Lambda"
./infra/deploy_transform.sh

echo "== S3 trigger on raw/**/_manifest.json"
aws lambda add-permission --function-name transform_day --statement-id s3-manifest \
  --action lambda:InvokeFunction --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET" --source-account "$ACCOUNT" >/dev/null
aws s3api put-bucket-notification-configuration --bucket "$BUCKET" --notification-configuration "{
  \"LambdaFunctionConfigurations\": [{
    \"LambdaFunctionArn\": \"arn:aws:lambda:$REGION:$ACCOUNT:function:transform_day\",
    \"Events\": [\"s3:ObjectCreated:*\"],
    \"Filter\": {\"Key\": {\"FilterRules\": [{\"Name\": \"prefix\", \"Value\": \"raw/\"},
                                          {\"Name\": \"suffix\", \"Value\": \"_manifest.json\"}]}}}]}"

echo "== Athena workgroup (100 MB scan limit per query)"
aws athena create-work-group --name mandi --configuration \
  "ResultConfiguration={OutputLocation=s3://$BUCKET/athena-results/},EnforceWorkGroupConfiguration=true,BytesScannedCutoffPerQuery=104857600,PublishCloudWatchMetricsEnabled=true"

echo "== dim_date calendar"
aws s3 cp data/model/dim_date/dim_date.parquet "s3://$BUCKET/model/dim_date/dim_date.parquet"

echo "Done. Next: S3_BUCKET=$BUCKET python -m tools.run_athena sql/athena_ddl/*.sql"

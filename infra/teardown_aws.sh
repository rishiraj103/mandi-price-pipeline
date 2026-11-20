#!/usr/bin/env bash
# Delete everything the setup scripts created. Irreversible: save screenshots/results first.
# Usage: BUCKET=<bucket> ./infra/teardown_aws.sh
set -uo pipefail   # no -e: keep going if something is already gone
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}"
read -r -p "Delete ALL mandi pipeline resources and s3://$BUCKET? Type the bucket name: " answer
[ "$answer" = "$BUCKET" ] || { echo "aborted"; exit 1; }

powershell -Command "Unregister-ScheduledTask -TaskName mandi-ingest-daily -Confirm:\$false"

aws lambda delete-function --function-name transform_day
aws logs delete-log-group --log-group-name /aws/lambda/transform_day
aws iam delete-role-policy --role-name lambda-transform-role --policy-name transform
aws iam delete-role --role-name lambda-transform-role

TOPIC=$(aws sns list-topics --query "Topics[?ends_with(TopicArn,':mandi-alerts')].TopicArn" --output text)
[ -n "$TOPIC" ] && aws sns delete-topic --topic-arn "$TOPIC"

aws glue delete-database --name mandi                     # tables and views go with it
aws athena delete-work-group --work-group mandi --recursive-delete-option

# empty every object version and delete marker, then the bucket
python - "$BUCKET" <<'PY'
import sys, boto3
boto3.resource("s3").Bucket(sys.argv[1]).object_versions.delete()
PY
aws s3api delete-bucket --bucket "$BUCKET"
echo "Teardown finished. Check Billing in a week."

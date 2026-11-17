#!/usr/bin/env bash
# Build the transform_day zip and create or update the Lambda (pandas/pyarrow come from the AWS SDK for pandas layer).
# Usage: BUCKET=<bucket> ./infra/deploy_transform.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${BUCKET:?set BUCKET}"
PY=${PY:-python}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
LAYER=$(aws ssm get-parameters-by-path --path /aws/service/aws-sdk-pandas --recursive \
  --query "Parameters[?contains(Name,'py3.12/x86_64')].[Name,Value]" --output text | sort -V | tail -1 | cut -f2)

rm -rf build/transform build/transform.zip
$PY -m pip install -q pyyaml -t build/transform \
    --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
mkdir -p build/transform/config
cp -r transform build/transform/
cp config/commodities.yml config/regions.yml build/transform/config/
find build/transform -name __pycache__ -type d -prune -exec rm -rf {} +
(cd build/transform && $PY -m zipfile -c ../transform.zip .)

if aws lambda get-function --function-name transform_day >/dev/null 2>&1; then
  aws lambda update-function-code --function-name transform_day --zip-file fileb://build/transform.zip >/dev/null
else
  aws lambda create-function --function-name transform_day --runtime python3.12 \
    --handler transform.lambda_transform.handler --memory-size 1024 --timeout 300 \
    --role "arn:aws:iam::$ACCOUNT:role/lambda-transform-role" --layers "$LAYER" \
    --environment "Variables={S3_BUCKET=$BUCKET}" \
    --zip-file fileb://build/transform.zip >/dev/null
fi
aws lambda wait function-updated-v2 --function-name transform_day
echo "transform_day deployed with $LAYER"

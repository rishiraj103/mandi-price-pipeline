#!/usr/bin/env bash
# Build the ingest_daily zip and create or update the Lambda.
# Usage: BUCKET=<bucket> ./infra/deploy_ingest.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1   # stop Git Bash rewriting /mandi/... into Windows paths
: "${BUCKET:?set BUCKET}"
PY=$(realpath "$(command -v "${PY:-python}")")   # absolute: the zip step runs in a subfolder
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

rm -rf build/ingest build/ingest.zip
# Linux wheels for the Lambda runtime (Python 3.12, x86_64)
$PY -m pip install -q requests pyyaml -t build/ingest \
    --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
mkdir -p build/ingest/config
cp -r ingest build/ingest/
cp config/commodities.yml build/ingest/config/
find build/ingest -name __pycache__ -type d -prune -exec rm -rf {} +
(cd build/ingest && $PY -m zipfile -c ../ingest.zip .)

if aws lambda get-function --function-name ingest_daily >/dev/null 2>&1; then
  aws lambda update-function-code --function-name ingest_daily --zip-file fileb://build/ingest.zip >/dev/null
else
  aws lambda create-function --function-name ingest_daily --runtime python3.12 \
    --handler ingest.lambda_ingest.handler --memory-size 256 --timeout 300 \
    --role "arn:aws:iam::$ACCOUNT:role/lambda-ingest-role" \
    --environment "Variables={S3_BUCKET=$BUCKET}" \
    --zip-file fileb://build/ingest.zip >/dev/null
fi
aws lambda wait function-updated-v2 --function-name ingest_daily
echo "ingest_daily deployed"

"""Read and write files on local disk or S3 (paths starting with s3://)."""
import io
from pathlib import Path

import pandas as pd


def _s3(path):
    import boto3
    bucket, key = path[5:].split("/", 1)
    return boto3.client("s3"), bucket, key


def list_files(prefix, suffix):
    if prefix.startswith("s3://"):
        s3, bucket, key = _s3(prefix)
        pages = s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=key)
        return sorted(f"s3://{bucket}/{o['Key']}" for p in pages for o in p.get("Contents", [])
                      if o["Key"].endswith(suffix))
    return sorted(str(p).replace("\\", "/") for p in Path(prefix).glob(f"*{suffix}"))


def read_bytes(path):
    if path.startswith("s3://"):
        s3, bucket, key = _s3(path)
        try:
            return s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except s3.exceptions.NoSuchKey:
            return None
    p = Path(path)
    return p.read_bytes() if p.exists() else None


def write_bytes(path, data):
    if path.startswith("s3://"):
        s3, bucket, key = _s3(path)
        s3.put_object(Bucket=bucket, Key=key, Body=data)
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def read_parquet(path):
    data = read_bytes(path)
    return None if data is None else pd.read_parquet(io.BytesIO(data))


def write_parquet(df, path):
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    write_bytes(path, buf.getvalue())

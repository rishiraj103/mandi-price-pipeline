import io
import unittest
from unittest import mock

import pandas as pd
from botocore.exceptions import ClientError

from transform import storage


def parquet_body(df):
    return {"Body": io.BytesIO(storage._to_bytes(df)), "ETag": '"v1"'}


class TestUpdateParquet(unittest.TestCase):
    def test_retries_when_another_writer_wins(self):
        s3 = mock.Mock()
        s3.get_object.side_effect = lambda **_: parquet_body(pd.DataFrame({"k": [1]}))
        conflict = ClientError({"Error": {"Code": "PreconditionFailed"}}, "PutObject")
        s3.put_object.side_effect = [conflict, None]
        merge = mock.Mock(side_effect=lambda df: df)

        with mock.patch.object(storage, "_s3", return_value=(s3, "bucket", "dim.parquet")):
            storage.update_parquet("s3://bucket/dim.parquet", merge)

        self.assertEqual(merge.call_count, 2)  # re-read and re-merged after the conflict
        self.assertEqual(s3.put_object.call_args.kwargs["IfMatch"], '"v1"')


if __name__ == "__main__":
    unittest.main()

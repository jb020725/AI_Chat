from __future__ import annotations

import io
import os
from typing import Optional

from google.cloud import storage


def get_client() -> storage.Client:
	# Uses default credentials in Cloud Run / ADC locally
	return storage.Client()


def upload_bytes(bucket_name: str, blob_path: str, data: bytes, content_type: Optional[str] = None) -> None:
	client = get_client()
	bucket = client.bucket(bucket_name)
	blob = bucket.blob(blob_path)
	blob.upload_from_file(io.BytesIO(data), rewind=True, content_type=content_type)


def download_bytes(bucket_name: str, blob_path: str) -> Optional[bytes]:
	client = get_client()
	bucket = client.bucket(bucket_name)
	blob = bucket.blob(blob_path)
	if not blob.exists():
		return None
	buf = io.BytesIO()
	blob.download_to_file(buf)
	buf.seek(0)
	return buf.read()


def blob_exists(bucket_name: str, blob_path: str) -> bool:
	client = get_client()
	bucket = client.bucket(bucket_name)
	blob = bucket.blob(blob_path)
	return blob.exists()

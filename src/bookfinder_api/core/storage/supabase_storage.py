import os
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def bucket_name() -> str:
    return os.getenv("SUPABASE_BUCKET", "bookfinder")


def object_path() -> str:
    return os.getenv("SUPABASE_OBJECT_PATH", "books.csv")


def upload_csv(bytes_data: bytes) -> None:
    supabase = get_supabase()
    bucket = supabase.storage.from_(bucket_name())
    path = object_path()
    opts = {"content-type": "text/csv"}

    try:
        bucket.upload(path, bytes_data, file_options=opts)
    except Exception:
        bucket.update(path, bytes_data, file_options=opts)


def download_csv() -> bytes:
    supabase = get_supabase()
    res = supabase.storage.from_(bucket_name()).download(object_path())
    return res

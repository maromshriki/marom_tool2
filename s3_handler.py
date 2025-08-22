from __future__ import annotations
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from utils import get_common_tags, tags_list_to_dict, CREATED_BY_KEY, CREATED_BY_VAL

def _s3_client(session: boto3.Session, region: str | None):
    # region for bucket operations
    return session.client("s3", region_name=region)

def create_bucket(session: boto3.Session, name: str, region: str | None, public: bool, confirm: str | None, owner: str | None):
    s3 = _s3_client(session, region)
    if public and confirm != "yes":
        raise RuntimeError("Public bucket requires explicit confirmation: pass --confirm yes")

    create_args = {"Bucket": name}
    # In us-east-1, do not set LocationConstraint
    if region and region != "us-east-1":
        create_args["CreateBucketConfiguration"] = {"LocationConstraint": region}

    s3.create_bucket(**create_args)

    # Tag bucket
    s3.put_bucket_tagging(Bucket=name, Tagging={"TagSet": get_common_tags(owner)})

    # Block public access by default
    if not public:
        s3.put_public_access_block(
            Bucket=name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
    else:
        # If public is requested, ensure public access block is removed
        try:
            s3.delete_public_access_block(Bucket=name)
        except ClientError:
            pass  # if not set, ignore
    return {"Bucket": name, "Public": public}

def _bucket_has_cli_tag(s3, bucket: str) -> bool:
    try:
        tags = s3.get_bucket_tagging(Bucket=bucket)["TagSet"]
    except ClientError as e:
        # If no tags found, or access denied
        raise PermissionError(f"Cannot read tags for bucket '{bucket}': {e}")
    t = tags_list_to_dict(tags)
    return t.get(CREATED_BY_KEY) == CREATED_BY_VAL

def upload_file(session: boto3.Session, region: str | None, bucket: str, key: str, file_path: str):
    s3 = _s3_client(session, region)
    if not _bucket_has_cli_tag(s3, bucket):
        raise PermissionError("Upload allowed only to CLI-created buckets")
    s3.upload_file(file_path, bucket, key)
    return {"Bucket": bucket, "Key": key, "Status": "uploaded"}

def list_buckets(session: boto3.Session):
    s3 = _s3_client(session, None)
    resp = s3.list_buckets()
    out = []
    for b in resp.get("Buckets", []):
        name = b["Name"]
        try:
            tags = s3.get_bucket_tagging(Bucket=name)["TagSet"]
            if tags_list_to_dict(tags).get(CREATED_BY_KEY) == CREATED_BY_VAL:
                out.append({"Name": name})
        except ClientError:
            # Skip buckets we can't tag-read
            continue
    return out

import boto3
import json
from utils import get_common_tags

def get_s3_client(profile=None, region=None):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("s3")

def create_bucket(bucket_name, public=False, owner=None, profile=None, region=None):
    s3 = get_s3_client(profile, region)
    tags = get_common_tags(owner)

    create_params = {"Bucket": bucket_name}

    if region and region != "us-east-1":
        create_params["CreateBucketConfiguration"] = {"LocationConstraint": region}

    try:
        s3.create_bucket(**create_params)

        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={"TagSet": tags}
        )

        if public:
            s3.put_bucket_acl(Bucket=bucket_name, ACL="public-read")

        print(f" Created bucket {bucket_name} in {region or 'default region'}")

    except Exception as e:
        print(json.dumps({"ok": False, "result": {"error": str(e)}}, indent=2))

def upload_file(bucket_name, file_path, profile=None, region=None):
    s3 = get_s3_client(profile, region)
    try:
        s3.upload_file(file_path, bucket_name, file_path.split("/")[-1])
        print(f" Uploaded {file_path} to {bucket_name}")
    except Exception as e:
        print(json.dumps({"ok": False, "result": {"error": str(e)}}, indent=2))

def list_buckets(profile=None, region=None):
    s3 = get_s3_client(profile, region)
    try:
        resp = s3.list_buckets()
        buckets = []
        for b in resp.get("Buckets", []):
            tags = []
            try:
                tagset = s3.get_bucket_tagging(Bucket=b["Name"])["TagSet"]
                tags = {t["Key"]: t["Value"] for t in tagset}
            except:
                continue

            if tags.get("CreatedBy") == "platform-cli":
                buckets.append({"Name": b["Name"], "Tags": tags})

        print(json.dumps(buckets, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "result": {"error": str(e)}}, indent=2))

from __future__ import annotations
import argparse, sys, json
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from utils import get_common_tags
import ec2_handler as ec2h
import s3_handler as s3h
import route53_handler as r53h

def make_session(profile: str | None, region: str | None):
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    return boto3.Session(region_name=region)

def print_result(ok: bool, payload: dict | list | str):
    print(json.dumps({"ok": ok, "result": payload}, indent=2, ensure_ascii=False))

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(prog="platform-cli", description="AWS CLI helper for EC2/S3/Route53 with enforced rules and tagging.")
    p.add_argument("--profile", help="AWS profile to use (credentials via roles/profiles)")
    p.add_argument("--region", help="AWS region (overrides default profile region)")
    p.add_argument("--owner", help="Owner tag value (default: current OS user)")

    sp = p.add_subparsers(dest="resource", required=True)

    # EC2
    ec2 = sp.add_parser("ec2", help="Manage EC2 instances created by this CLI")
    ec2_sp = ec2.add_subparsers(dest="action", required=True)

    ec2_create = ec2_sp.add_parser("create", help="Create instance (types: t3.micro | t2.small; cap: 2 running)")
    ec2_create.add_argument("--type", required=True, choices=sorted(ec2h.EC2_ALLOWED_TYPES))
    ec2_create.add_argument("--os", default="ubuntu", choices=["ubuntu", "amazon-linux"], help="Base AMI OS (default: ubuntu)")

    ec2_start = ec2_sp.add_parser("start", help="Start an instance created by this CLI")
    ec2_start.add_argument("--id", required=True, help="EC2 instance-id")

    ec2_stop = ec2_sp.add_parser("stop", help="Stop an instance created by this CLI")
    ec2_stop.add_argument("--id", required=True, help="EC2 instance-id")

    ec2_list = ec2_sp.add_parser("list", help="List instances created by this CLI")

    # S3
    s3 = sp.add_parser("s3", help="Manage S3 buckets created by this CLI")
    s3_sp = s3.add_subparsers(dest="action", required=True)

    s3_create = s3_sp.add_parser("create", help="Create bucket (private by default; for public require --confirm yes)")
    s3_create.add_argument("--name", required=True, help="Bucket name (globally unique)")
    s3_create.add_argument("--public", action="store_true", help="Make bucket public (requires --confirm yes)")
    s3_create.add_argument("--confirm", help="Must be 'yes' if --public used")

    s3_upload = s3_sp.add_parser("upload", help="Upload file to CLI-created bucket")
    s3_upload.add_argument("--bucket", required=True)
    s3_upload.add_argument("--key", required=True)
    s3_upload.add_argument("--file", required=True, dest="file_path")

    s3_list = s3_sp.add_parser("list", help="List buckets created by this CLI")

    # Route53
    r53 = sp.add_parser("route53", help="Manage Route53 hosted zones/records created by this CLI")
    r53_sp = r53.add_subparsers(dest="action", required=True)

    z_create = r53_sp.add_parser("create-zone", help="Create a hosted zone")
    z_create.add_argument("--name", required=True, help="Zone name (e.g., example.com.)")

    z_list = r53_sp.add_parser("list-zones", help="List hosted zones created by this CLI")

    rec_list = r53_sp.add_parser("list-records", help="List records in a CLI-created zone")
    rec_list.add_argument("--zone-id", required=True)

    rec_upsert = r53_sp.add_parser("upsert-record", help="Create/Update a DNS record in a CLI-created zone")
    rec_upsert.add_argument("--zone-id", required=True)
    rec_upsert.add_argument("--name", required=True)
    rec_upsert.add_argument("--type", required=True, choices=["A","AAAA","CNAME","TXT","MX","SRV","NS","SOA","PTR"])
    rec_upsert.add_argument("--ttl", type=int, default=300)
    rec_upsert.add_argument("--values", required=True, help="Comma-separated values (e.g., 1.2.3.4,5.6.7.8)")

    rec_delete = r53_sp.add_parser("delete-record", help="Delete a DNS record from a CLI-created zone")
    rec_delete.add_argument("--zone-id", required=True)
    rec_delete.add_argument("--name", required=True)
    rec_delete.add_argument("--type", required=True, choices=["A","AAAA","CNAME","TXT","MX","SRV","NS","SOA","PTR"])
    rec_delete.add_argument("--values", required=True, help="Comma-separated values")

    args = p.parse_args(argv)

    session = make_session(args.profile, args.region)

    try:
        if args.resource == "ec2":
            if args.action == "create":
                res = ec2h.create_instance(session, args.type, args.os, args.owner)
                print_result(True, res)
            elif args.action == "start":
                res = ec2h.start_instance(session, args.id)
                print_result(True, res)
            elif args.action == "stop":
                res = ec2h.stop_instance(session, args.id)
                print_result(True, res)
            elif args.action == "list":
                res = ec2h.list_instances(session)
                print_result(True, res)

        elif args.resource == "s3":
            if args.action == "create":
                res = s3h.create_bucket(session, args.name, args.region, args.public, args.confirm, args.owner)
                print_result(True, res)
            elif args.action == "upload":
                res = s3h.upload_file(session, args.region, args.bucket, args.key, args.file_path)
                print_result(True, res)
            elif args.action == "list":
                res = s3h.list_buckets(session)
                print_result(True, res)

        elif args.resource == "route53":
            if args.action == "create-zone":
                res = r53h.create_zone(session, args.name, args.owner)
                print_result(True, res)
            elif args.action == "list-zones":
                res = r53h.list_zones(session)
                print_result(True, res)
            elif args.action == "list-records":
                res = r53h.list_records(session, args.zone_id)
                print_result(True, res)
            elif args.action == "upsert-record":
                values = [v.strip() for v in args.values.split(",") if v.strip()]
                res = r53h.upsert_record(session, args.zone_id, args.name, args.type, args.ttl, values)
                print_result(True, res)
            elif args.action == "delete-record":
                values = [v.strip() for v in args.values.split(",") if v.strip()]
                res = r53h.delete_record(session, args.zone_id, args.name, args.type, values)
                print_result(True, res)

    except (ClientError, BotoCoreError) as e:
        print_result(False, {"error": str(e)})
        sys.exit(2)
    except (ValueError, PermissionError, RuntimeError) as e:
        print_result(False, {"error": str(e)})
        sys.exit(2)

if __name__ == "__main__":
    main()

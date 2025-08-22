from __future__ import annotations
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4
from utils import get_common_tags, tags_list_to_dict, CREATED_BY_KEY, CREATED_BY_VAL

def _r53_client(session: boto3.Session):
    return session.client("route53")

def _strip_zone_id(zid: str) -> str:
    return zid.split("/")[-1]

def create_zone(session: boto3.Session, name: str, owner: str | None):
    r53 = _r53_client(session)
    hz = r53.create_hosted_zone(Name=name, CallerReference=str(uuid4()))["HostedZone"]
    zid = _strip_zone_id(hz["Id"])
    r53.change_tags_for_resource(
        ResourceType="hostedzone",
        ResourceId=zid,
        AddTags=get_common_tags(owner)
    )
    return {"Id": zid, "Name": hz["Name"]}

def _ensure_cli_zone(r53, hosted_zone_id: str):
    zid = _strip_zone_id(hosted_zone_id)
    tags = r53.list_tags_for_resource(ResourceType="hostedzone", ResourceId=zid)["ResourceTagSet"]["Tags"]
    t = tags_list_to_dict(tags)
    if t.get(CREATED_BY_KEY) != CREATED_BY_VAL:
        raise PermissionError("Zone is not managed by platform-cli")
    return zid

def list_zones(session: boto3.Session):
    r53 = _r53_client(session)
    zones = r53.list_hosted_zones()["HostedZones"]
    out = []
    for z in zones:
        zid = _strip_zone_id(z["Id"])
        tags = r53.list_tags_for_resource(ResourceType="hostedzone", ResourceId=zid)["ResourceTagSet"]["Tags"]
        if tags_list_to_dict(tags).get(CREATED_BY_KEY) == CREATED_BY_VAL:
            out.append({"Id": zid, "Name": z["Name"]})
    return out

def list_records(session: boto3.Session, hosted_zone_id: str):
    r53 = _r53_client(session)
    zid = _ensure_cli_zone(r53, hosted_zone_id)
    out = []
    paginator = r53.get_paginator("list_resource_record_sets")
    for page in paginator.paginate(HostedZoneId=zid):
        for rr in page.get("ResourceRecordSets", []):
            out.append({
                "Name": rr.get("Name"),
                "Type": rr.get("Type"),
                "TTL": rr.get("TTL"),
                "Values": [v.get("Value") for v in rr.get("ResourceRecords", [])] if rr.get("ResourceRecords") else rr.get("AliasTarget"),
            })
    return out

def upsert_record(session: boto3.Session, hosted_zone_id: str, name: str, rtype: str, ttl: int, values: list[str]):
    r53 = _r53_client(session)
    zid = _ensure_cli_zone(r53, hosted_zone_id)
    r53.change_resource_record_sets(
        HostedZoneId=zid,
        ChangeBatch={
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": name, "Type": rtype, "TTL": ttl,
                    "ResourceRecords": [{"Value": v} for v in values]
                }
            }]
        }
    )
    return {"HostedZoneId": zid, "Action": "UPSERT", "Name": name, "Type": rtype}

def delete_record(session: boto3.Session, hosted_zone_id: str, name: str, rtype: str, values: list[str]):
    r53 = _r53_client(session)
    zid = _ensure_cli_zone(r53, hosted_zone_id)
    r53.change_resource_record_sets(
        HostedZoneId=zid,
        ChangeBatch={
            "Changes": [{
                "Action": "DELETE",
                "ResourceRecordSet": {
                    "Name": name, "Type": rtype,
                    "ResourceRecords": [{"Value": v} for v in values]
                }
            }]
        }
    )
    return {"HostedZoneId": zid, "Action": "DELETE", "Name": name, "Type": rtype}

from __future__ import annotations
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict
from utils import get_common_tags, tags_list_to_dict, CREATED_BY_KEY, CREATED_BY_VAL

EC2_ALLOWED_TYPES = {"t3.micro", "t2.small"}

def _ec2_client(session: boto3.Session):
    return session.client("ec2")

def latest_ami(session: boto3.Session, os_choice: str):
    ec2 = _ec2_client(session)
    if os_choice == "ubuntu":
        owners = ["099720109477"]  # Canonical
        name_prefix = "ubuntu/images/hvm-ssd/ubuntu-*-*-amd64-server-*"
        filters = [{"Name": "name", "Values": [name_prefix]}, {"Name": "state", "Values": ["available"]}]
    else:
        owners = ["137112412989"]  # Amazon
        # Amazon Linux 2 x86_64
        name_prefix = "amzn2-ami-hvm-*-x86_64-gp2"
        filters = [{"Name": "name", "Values": [name_prefix]}, {"Name": "state", "Values": ["available"]}]

    imgs = ec2.describe_images(Owners=owners, Filters=filters)["Images"]
    if not imgs:
        raise RuntimeError("No AMI found for requested OS")
    imgs.sort(key=lambda x: x["CreationDate"], reverse=True)
    return imgs[0]["ImageId"]

def _running_cli_instances_count(ec2) -> int:
    resp = ec2.describe_instances(Filters=[
        {"Name": f"tag:{CREATED_BY_KEY}", "Values": [CREATED_BY_VAL]},
        {"Name": "instance-state-name", "Values": ["pending", "running"]},
    ])
    return sum(len(r["Instances"]) for r in resp.get("Reservations", []))

def create_instance(session: boto3.Session, instance_type: str, os_choice: str, owner: str | None):
    if instance_type not in EC2_ALLOWED_TYPES:
        raise ValueError(f"instance_type must be one of {sorted(EC2_ALLOWED_TYPES)}")

    ec2 = _ec2_client(session)
    if _running_cli_instances_count(ec2) >= 2:
        raise RuntimeError("Hard cap reached: 2 running CLI instances already exist")

    ami = latest_ami(session, os_choice)
    tags = get_common_tags(owner)
    tag_spec = [{"ResourceType": "instance", "Tags": tags},
                {"ResourceType": "volume", "Tags": tags}]

    res = ec2.run_instances(
        ImageId=ami,
        InstanceType=instance_type,
        MinCount=1, MaxCount=1,
        TagSpecifications=tag_spec
    )
    inst = res["Instances"][0]
    return {"InstanceId": inst["InstanceId"], "State": inst["State"]["Name"], "AMI": ami, "Type": instance_type}

def _instance_has_cli_tag(ec2, instance_id: str) -> bool:
    d = ec2.describe_instances(InstanceIds=[instance_id])
    insts = [i for r in d.get("Reservations", []) for i in r.get("Instances", [])]
    if not insts:
        raise RuntimeError(f"Instance not found: {instance_id}")
    tags = tags_list_to_dict(insts[0].get("Tags", []))
    return tags.get(CREATED_BY_KEY) == CREATED_BY_VAL

def start_instance(session: boto3.Session, instance_id: str):
    ec2 = _ec2_client(session)
    if not _instance_has_cli_tag(ec2, instance_id):
        raise PermissionError("Start allowed only for CLI-created instances")
    ec2.start_instances(InstanceIds=[instance_id])
    return {"InstanceId": instance_id, "Action": "start", "Status": "initiated"}

def stop_instance(session: boto3.Session, instance_id: str):
    ec2 = _ec2_client(session)
    if not _instance_has_cli_tag(ec2, instance_id):
        raise PermissionError("Stop allowed only for CLI-created instances")
    ec2.stop_instances(InstanceIds=[instance_id])
    return {"InstanceId": instance_id, "Action": "stop", "Status": "initiated"}

def list_instances(session: boto3.Session):
    ec2 = _ec2_client(session)
    resp = ec2.describe_instances(Filters=[
        {"Name": f"tag:{CREATED_BY_KEY}", "Values": [CREATED_BY_VAL]}
    ])
    out = []
    for r in resp.get("Reservations", []):
        for i in r.get("Instances", []):
            out.append({
                "InstanceId": i.get("InstanceId"),
                "State": i.get("State", {}).get("Name"),
                "Type": i.get("InstanceType"),
                "PrivateIp": i.get("PrivateIpAddress"),
                "PublicIp": i.get("PublicIpAddress"),
            })
    return out

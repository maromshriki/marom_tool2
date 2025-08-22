import getpass

CREATED_BY_KEY = "CreatedBy"
CREATED_BY_VAL = "platform-cli"
OWNER_KEY = "Owner"


def get_common_tags(owner: str | None = None):
    if not owner:
        try:
            owner = getpass.getuser()
        except Exception:
            owner = "unknown"
    return [
        {"Key": CREATED_BY_KEY, "Value": CREATED_BY_VAL},
        {"Key": OWNER_KEY, "Value": owner},
    ]


def is_cli_tags_dict(tag_dict: dict) -> bool:
    return tag_dict.get(CREATED_BY_KEY) == CREATED_BY_VAL


def tags_list_to_dict(tags: list[dict]) -> dict:
    d = {}
    for t in tags or []:
        k = t.get("Key")
        v = t.get("Value")
        if k is not None:
            d[k] = v
    return d

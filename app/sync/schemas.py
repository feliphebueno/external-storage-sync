POST_SYNC_OBJECT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "oeid": {"type": "string"},
        "ref_id": {"type": "string"},
        "file_name": {"type": "string"},
        "file_type": {"type": "string"},
    },
    "required": ["oeid", "ref_id", "file_name", "file_type"],
}

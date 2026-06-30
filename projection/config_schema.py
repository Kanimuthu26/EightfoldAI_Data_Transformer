from typing import Dict, Any
import jsonschema

PROJECTION_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "from": {"type": "string"},
                    "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "string[]", "object"]},
                    "required": {"type": "boolean"},
                    "normalize": {"type": "string", "enum": ["E.164", "canonical", "YYYY-MM", "upper", "lower"]}
                },
                "required": ["path"],
                "additionalProperties": False
            }
        },
        "include_confidence": {"type": "boolean"},
        "include_provenance": {"type": "boolean"},
        "on_missing": {"type": "string", "enum": ["null", "omit", "error"]}
    },
    "required": ["fields"],
    "additionalProperties": False
}

def validate_projection_config(config: Dict[str, Any]) -> bool:
    """
    Validates a projection runtime config against the JSON Schema.
    Raises jsonschema.ValidationError on failure.
    """
    jsonschema.validate(instance=config, schema=PROJECTION_CONFIG_SCHEMA)
    return True

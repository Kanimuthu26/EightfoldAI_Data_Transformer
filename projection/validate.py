from typing import Dict, Any, List

def validate_projected_output(projected: Dict[str, Any], fields_config: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates a projected profile dict against the requested schema types in fields_config.
    If a field has an invalid type, it is set to None (null) rather than invented or causing a crash.
    """
    validated = projected.copy()

    for field_conf in fields_config:
        name = field_conf.get("path")
        expected_type = field_conf.get("type", "string")
        
        if name not in validated:
            continue
            
        val = validated[name]
        if val is None:
            continue

        is_valid = True
        
        if expected_type == "string":
            is_valid = isinstance(val, str)
        elif expected_type == "number":
            is_valid = isinstance(val, (int, float)) and not isinstance(val, bool)
        elif expected_type == "boolean":
            is_valid = isinstance(val, bool)
        elif expected_type == "array" or expected_type == "string[]":
            is_valid = isinstance(val, list)
            if is_valid and expected_type == "string[]":
                # Ensure all elements are strings
                if not all(isinstance(x, str) for x in val):
                    # Filter out non-strings or invalidate
                    validated[name] = [str(x) for x in val]
                    continue
        elif expected_type == "object":
            is_valid = isinstance(val, dict)

        if not is_valid:
            # Fall back to None instead of crashing
            validated[name] = None

    return validated

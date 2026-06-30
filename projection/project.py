import re
from typing import Dict, Any, List, Optional
from engine.canonical import CanonicalProfile
from engine.normalize import normalize_phone, normalize_date, normalize_skill

def resolve_path(profile: CanonicalProfile, path: str) -> Any:
    """
    Resolves a path reference on a CanonicalProfile object.
    Supports:
    - Scalar fields: "full_name", "headline"
    - Array indexes: "emails[0]", "phones[1]"
    - List mapping: "skills[].name", "experience[].company"
    - Nested dict: "location.city", "links.linkedin"
    """
    if not path:
        return None

    # 1. List mapping, e.g. "skills[].name"
    if "[]." in path:
        parts = path.split("[].")
        if len(parts) == 2:
            list_field, sub_field = parts
            lst = getattr(profile, list_field, None)
            if isinstance(lst, list):
                res = []
                for item in lst:
                    # Might be objects or dicts
                    if hasattr(item, sub_field):
                        val = getattr(item, sub_field)
                    elif isinstance(item, dict):
                        val = item.get(sub_field)
                    else:
                        val = None
                    if val is not None:
                        res.append(val)
                return res
            return None

    # 2. Indexed array, e.g. "emails[0]"
    match_idx = re.match(r'^(\w+)\[(\d+)\]$', path)
    if match_idx:
        field, idx_str = match_idx.groups()
        idx = int(idx_str)
        lst = getattr(profile, field, None)
        if isinstance(lst, list) and 0 <= idx < len(lst):
            return lst[idx]
        return None

    # 3. Nested dictionary path, e.g. "location.city"
    if "." in path:
        parts = path.split(".")
        if len(parts) == 2:
            obj_field, sub_field = parts
            obj = getattr(profile, obj_field, None)
            if isinstance(obj, dict):
                return obj.get(sub_field)
            elif hasattr(obj, sub_field):
                return getattr(obj, sub_field)
            return None

    # 4. Standard scalar field
    if hasattr(profile, path):
        return getattr(profile, path)

    return None

def apply_normalize_override(val: Any, norm_type: str) -> Any:
    if val is None:
        return None

    if isinstance(val, list):
        return [apply_normalize_override(item, norm_type) for item in val]

    if norm_type == "E.164":
        return normalize_phone(str(val))
    elif norm_type == "YYYY-MM":
        return normalize_date(val)
    elif norm_type == "canonical":
        return normalize_skill(str(val))
    elif norm_type == "upper":
        return str(val).upper()
    elif norm_type == "lower":
        return str(val).lower()
        
    return val

def project_profile(profile: CanonicalProfile, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Projects a single CanonicalProfile into a dict view specified by config.
    """
    projected = {}
    on_missing = config.get("on_missing", "null")  # "null" | "omit" | "error"
    fields_config = config.get("fields", [])

    for field_conf in fields_config:
        path_name = field_conf.get("path")
        from_path = field_conf.get("from") or path_name
        is_required = field_conf.get("required", False)
        norm_override = field_conf.get("normalize")

        # Resolve raw value from canonical profile
        raw_val = resolve_path(profile, from_path)

        # Apply normalizer override if present
        if norm_override and raw_val is not None:
            raw_val = apply_normalize_override(raw_val, norm_override)

        # Handle missing values
        if raw_val is None or raw_val == [] or raw_val == "":
            if is_required and on_missing == "error":
                raise ValueError(f"Required field '{path_name}' resolved to empty/missing.")
            
            if on_missing == "omit":
                continue
            else:  # "null" policy
                projected[path_name] = None
        else:
            projected[path_name] = raw_val

    # Toggle confidence and provenance fields at top level
    if config.get("include_confidence", False):
        projected["overall_confidence"] = round(profile.overall_confidence, 2)
        
    if config.get("include_provenance", False):
        projected["provenance"] = [p.to_dict() for p in profile.provenance]

    return projected

def _extract_types(obj: object) -> set[str]:
    """Extract @type values from a single JSON-LD object."""
    if not isinstance(obj, dict):
        return set()

    raw_type = obj.get("@type")
    if raw_type is None:
        return set()

    if isinstance(raw_type, str):
        return {raw_type}
    if isinstance(raw_type, list):
        return {t for t in raw_type if isinstance(t, str)}

    return set()


def json_ld_contains_type(json_ld_objects: list, expected_types: set[str]) -> bool:
    """Check if any JSON-LD object contains one of the expected @type values.

    Supports:
    - dict objects
    - list of dicts
    - nested @graph structures
    - @type as string or list of strings
    """
    for item in json_ld_objects:
        if isinstance(item, dict):
            if _extract_types(item) & expected_types:
                return True
            graph = item.get("@graph")
            if isinstance(graph, list):
                for entry in graph:
                    if _extract_types(entry) & expected_types:
                        return True
        elif isinstance(item, list):
            for sub in item:
                if isinstance(sub, dict):
                    if _extract_types(sub) & expected_types:
                        return True
                    graph = sub.get("@graph")
                    if isinstance(graph, list):
                        for entry in graph:
                            if _extract_types(entry) & expected_types:
                                return True
    return False

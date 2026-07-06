from app.schemas import Issue


def detect_invalid_json_ld(parsed: dict, location: str) -> list[Issue]:
    if parsed.get("invalid_json_ld_count", 0) > 0:
        return [
            Issue(
                id="invalid_json_ld",
                severity="medium",
                category="structured_data",
                location=location,
                description=(
                    "One or more JSON-LD structured data blocks could"
                    " not be parsed as valid JSON."
                ),
            )
        ]
    return []

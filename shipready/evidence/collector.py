"""Evidence normalization and secret redaction."""

from __future__ import annotations

import re
from typing import Any

SECRET_KEY = re.compile(
    r"(authorization|cookie|password|passwd|secret|token|api[_-]?key|"
    r"idempotency-key)",
    re.IGNORECASE,
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
INLINE_SECRET = re.compile(
    r"(?i)\b(authorization|password|passwd|secret|token|api[_-]?key)"
    r"(\s*[:=]\s*)(['\"]?)[^,\s'\"}]+(['\"]?)"
)


def redact(value: Any, key: str | None = None) -> Any:
    """Return JSON-safe evidence with common credentials removed."""
    if key and SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(name): redact(item, str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        redacted = BEARER.sub("Bearer [REDACTED]", value)
        return INLINE_SECRET.sub(r"\1\2\3[REDACTED]\4", redacted)
    return value

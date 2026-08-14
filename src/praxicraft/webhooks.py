"""Local helpers for Assess webhook receivers."""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(secret: str, body: bytes, header_sig: str) -> bool:
    """Verify an ``X-Praxicraft-Signature`` header.

    Assess signs the raw request body with HMAC-SHA256 using the webhook
    secret (``whsec_…``). The canonical header value is ``sha256=<hex>``.
    Legacy test pings that sent raw hex (without the prefix) are also accepted.

    Returns ``False`` for missing/invalid inputs or mismatched signatures.
    Never raises on bad attacker-controlled signature strings.
    """
    if not isinstance(secret, str) or not secret:
        return False
    if not isinstance(body, (bytes, bytearray)):
        return False
    if not isinstance(header_sig, str) or not header_sig:
        return False

    expected = _sign_body(secret, bytes(body))
    try:
        if header_sig.startswith("sha256="):
            return hmac.compare_digest(header_sig, expected)

        legacy = expected.removeprefix("sha256=")
        return hmac.compare_digest(header_sig, legacy) or hmac.compare_digest(
            header_sig, expected
        )
    except (TypeError, ValueError):
        # compare_digest raises when lengths differ — treat as invalid signature.
        return False


def _sign_body(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

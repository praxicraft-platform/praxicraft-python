from __future__ import annotations

import hashlib
import hmac

from praxicraft.webhooks import verify_signature


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_signature_valid() -> None:
    secret = "whsec_test_secret"
    body = b'{"event":"webhook.test"}'
    assert verify_signature(secret, body, _sign(secret, body)) is True


def test_verify_signature_rejects_tamper() -> None:
    secret = "whsec_test_secret"
    body = b'{"event":"webhook.test"}'
    bad = _sign(secret, b'{"event":"other"}')
    assert verify_signature(secret, body, bad) is False


def test_verify_signature_accepts_legacy_hex() -> None:
    secret = "whsec_test_secret"
    body = b'{"event":"webhook.test"}'
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, digest) is True


def test_verify_signature_empty_inputs() -> None:
    assert verify_signature("", b"{}", "sha256=abc") is False
    assert verify_signature("whsec_x", b"{}", "") is False
    assert verify_signature("whsec_x", "not-bytes", "sha256=abc") is False  # type: ignore[arg-type]

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not actually sleep during SDK retry backoff in unit tests."""
    import praxicraft._retry as retry_mod

    monkeypatch.setattr(retry_mod, "sleep_fn", lambda _seconds: None)

"""Organisation resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

from praxicraft.types import Org

if TYPE_CHECKING:
    from praxicraft._client import Client


class OrgResource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def retrieve(self) -> Org:
        """``GET /org/`` — workspace summary (plan + invite quota).

        Useful before bulk invites: check ``invites_remaining``.
        """
        return self._client.get("/org/")

    def stats(self, *, params: Mapping[str, Any] | None = None) -> Any:
        """``GET /org/stats/`` — aggregate hiring analytics."""
        return self._client.get("/org/stats/", params=params)

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Self, TypeVar
from uuid import UUID

from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)


@dataclass
class ExpandedEdge:
    edge_name: str
    fields: list[str | ExpandedEdge] | None = None
    group: str | None = None
    groups: list[str] | None = None


class Ent(ABC, Generic[VC]):
    @property
    @abstractmethod
    def id(self) -> UUID:
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        pass

    @classmethod
    @abstractmethod
    async def gen(cls, vc: VC, ent_id: UUID | str) -> Self | None:
        pass

    @classmethod
    @abstractmethod
    async def genx(cls, vc: VC, ent_id: UUID | str) -> Self:
        pass

    @abstractmethod
    async def to_json(
        self,
        fields: list[str | ExpandedEdge] | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        """
        This function is used to build a JSON-friendly representation of the Ent
        that can be passed, for example, to `json.dumps`, or Quart's `jsonify`
        functions.
        Note that the `id`, `created_at`, and `updated_at` fields are always
        included by default (unless overriden using `fields`).

        `fields`: you can specify the exact list of fields you'd like to include
        in the JSON representation of the Ent. Note: if including an EdgeField,
        it will be represented by `<edge_name>_id` and have the edge ID as value
        unless expanded.
        If you want to expand data for an edge, pass an ExpandedEdge object and
        specify which subfields or groups you need. You can fetch the fields
        recursively, but beware of the database load since each level will trigger
        a fetch in the database.
        Edges are fetched using the ViewerContext that was used to load the
        current Ent.
        Example:
        ```
        await ent_user.to_json(fields=[
            "id",
            "created_at",
            "username",
            ExpandedEdge(
                edge_name="team",
                fields=[
                    "id",
                    "name",
                    ExpandedEdge(edge_name="company", fields=["id", "name"]),
                ],
            ),
        ])
        # Returns {
        #     "id": 123,
        #     "created_at": "2025-11-09T04:02:14.278622",
        #     "username": "vdurmont",
        #     "team": {
        #         "id": 456,
        #         "name": "The Best Team",
        #         "company": {
        #             "id": 789,
        #             "name": "Big Corp, Inc.",
        #         }
        #     }
        # }
        ```

        `group`: optional group of fields that the user can pass in order to only
        select the fields that will match the key. This is based on the `.json(...)`
        attribute of each Ent Field.
        Example:
        ```
        # If the group "small" contains `username` and `avatar_url`.
        await ent_user.to_json(group="small")
        # Returns {
        #     "id": 123,
        #     "created_at": "2025-11-09T04:02:14.278622",
        #     "updated_at": "2025-11-09T04:02:14.278622",
        #     "username": "vdurmont",
        #     "avatar_url": "https://entpy.dev/vincent.png",
        # }
        await ent_user.to_json()
        # Returns {
        #     "id": 123,
        #     "created_at": "2025-11-09T04:02:14.278622",
        #     "updated_at": "2025-11-09T04:02:14.278622",
        #     "username": "vdurmont",
        #     "avatar_url": "https://entpy.dev/vincent.png",
        #     "status": "HAPPY",
        #     "team_id": 456,
        # }
        ```
        """
        pass

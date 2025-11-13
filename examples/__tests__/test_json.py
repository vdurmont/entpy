from generated.ent_child import EntChildExample
from generated.ent_test_object import EntTestObjectExample
from generated.ent_test_sub_object import EntTestSubObjectExample
from evc import ExampleViewerContext
from entpy import ExpandedEdge


async def test_base_json(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    result = await child.to_json()

    expected = {
        "id": str(child.id),
        "created_at": child.created_at.isoformat(),
        "updated_at": child.updated_at.isoformat(),
        "name": child.name,
        "parent_id": str(child.parent_id),
    }

    assert result == expected


async def test_fields_json(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    parent = await child.gen_parent()
    result = await child.to_json(
        fields=[
            "id",
            "name",
            ExpandedEdge(
                edge_name="parent",
                fields=[
                    "created_at",
                    "grand_parent",
                ],
            ),
        ]
    )

    expected = {
        "id": str(child.id),
        "name": child.name,
        "parent": {
            "created_at": parent.created_at.isoformat(),
            "grand_parent_id": str(parent.grand_parent_id),
        },
    }

    assert result == expected


async def test_groups_json(
    vc: ExampleViewerContext,
) -> None:
    sub = await EntTestSubObjectExample.gen_create(vc)
    obj = await EntTestObjectExample.gen_create(vc=vc, optional_sub_object_id=sub.id)
    req = await obj.gen_required_sub_object()
    result = await obj.to_json(group="small")

    expected = {
        "id": str(obj.id),
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat(),
        "username": obj.username,
        "optional_sub_object_id": str(sub.id),
        "required_sub_object": {
            "id": str(req.id),
            "created_at": req.created_at.isoformat(),
            "updated_at": req.updated_at.isoformat(),
            "email": req.email,
        },
    }

    assert result == expected

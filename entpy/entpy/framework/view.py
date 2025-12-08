from sqlalchemy import MetaData, Table
from sqlalchemy.sql.selectable import Selectable
from sqlalchemy_utils.view import create_view as create_view_orig


def create_view(
    name: str,
    selectable: Selectable,
    metadata: MetaData,
) -> Table:
    metadata.info.setdefault("views", {})[name] = selectable
    return create_view_orig(  # type: ignore[no-any-return]
        name,
        selectable,
        metadata,
        cascade_on_drop=False,
        replace=True,
    )

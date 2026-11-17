from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

from entpy.framework.imported_object import ImportedObject


@dataclass(frozen=True)
class ComputedApiFieldsConfig:
    """Serialized values that are not columns, and the function computing them.

    `models` maps a tier to the Pydantic model holding the values that tier
    adds; each model subclasses the one of the tier below it. `resolver` names
    an async function taking the list of Ents being serialized and the tier,
    and returning one instance per Ent of the model for that tier. It is named
    by import path because it imports the generated Ent.
    """

    models: dict[Enum, type[BaseModel]]
    resolver: ImportedObject

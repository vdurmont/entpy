# EntPy

EntPy is a data access and privacy framework that augments SQLAlchemy, providing you a central place to safely access and manage your data.

Its purpose and name is directly "inspired" from the framework of the same name at Meta.

# IMPORTANT

This is very much a work in progress. I only built the features I need for my own projects. If you need something else, definitely let me know and I'll try to send a quick PR.

In any case, you can use on of the 2 escape hatches:
```python
# 1. Access a specific model directly
ent = await EntMyObject.gen(vc, ent_id)
ent.model # This is the raw SQLAlchemy object

# 2. Use SQLAlchemy
from entities.ent_my_object import EntMyObjectModel

session = await generate_session()
model = await session.get(EntMyObjectModel, ent_id)
```

# Getting started

To get started with EntPy, you should first create an Ent. In order to do so, you need to create the definition file (or Ent Schema). Here is a short example, and you can see all the details in the `Schema API` section.


```python
# In `./schemas/ent_my_object_schema.py`
from entpy.framework import Field, Schema, StringField

class EntMyObjectSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("my_field", length=100).not_null(),
        ]
```

Run the gencode script (see `Gencode` section below for details):

```bash
uv run python ent_gencode.py
```

The framework will generate a file in `./entities/ent_my_object.py` that contains:
- `EntMyObject`, the main class you will use to access the data
- `EntMyObjectQuery`, a utility class that wraps the SQL Alchemy query API and enables you to query ents
- `EntMyObjectMutator`, a utility class to handle mutations (creation, update, deletion) for your ent in a safe way
- `EntMyObjectExample`, a utility class for your tests to generate ents pre-popualted with test/example data

# Using Ents

## ViewerContext

A `ViewerContext` (or VC) is a class that holds information about the identity of the person/service that is currently executing the code. It is used heavily in EntPrivacy to determine if the current viewer can access/modify the data.

There are 2 special ViewerContexts:
- `omniscient`, which means you can see everything
- `all_powerful`, which means you can see and do everything

Those VCs should be used as little as possible and only in situations where it is absolutely impossible to have the real identity of the viewer.

## Reading an Ent

You have 2 ways to load an Ent:
- Use `gen` to load an Ent and return `None` if it doesn't exist.
- Use `genx` to load an Ent and raise and error if it doesn't exist.

Both will check your privacy rules and only return the Ent if it can be accessed.

```python
optional_ent = await EntMyObject.gen(vc, ent_id)
ent = await EntMyObject.genx(vc, ent_id)
```

## Querying Ents

If you want to perform a more complex query to find one or more Ents, you can use the query API:
```python
from ent_my_object import EntMyObject, EntMyObjectModel
from ent_my_other_object import EntMyOtherObjectModel

ents = (
    await EntMyObject.query(vc)
    .where(EntMyObjectModel.happiness_level == 3)
    .where(EntMyObjectModel.sadness_level < 5)
    .join(EntMyOtherObjectModel, EntMyOtherObjectModel.id == EntMyObjectModel.other_id)
    .where(EntMyOtherObjectModel.some_other_field == "yolo")
    .order_by(EntMyObjectModel.id.desc())
    .limit(10)
    .gen()
)
```

The EntQuery wraps the SQL Alchemy query API so you can use the models to query everything!

You can also query for counts. Watch out! We do not run privacy rules when counting...
```python
number = (
    await EntMyObject.query_count(vc)
    .where(EntMyObjectModel.happiness_level == 3)
    .gen()
)
```

## Creating an Ent

```python
ent = await EntMyObjectMutator.create(
    vc=vc,
    field1=val1,
    field2=val2,
).gen_savex()
print(f"Created ent {ent.id}")
```

Note that in order to make testing easier, Ents generate an "example" class that can be used like this:
```python
ent = await EntMyObjectExample.gen_create(vc)
# Boom!
# An ent has been created, all it's fields have been populated appropriately, any edge has been created recursively, you are ready to use it fully.
```

You can also choose to customize one or more fields:
```python
ent = await EntMyObjectExample.gen_create(
    vc=vc,
    field42=value,
)
```

## Updating an Ent

```python
mut = await EntMyObjectMutator.update(vc, ent)
mut.field1 = new_value
ent = await mut.gen_savex()
print(f"Updated ent {ent.id}")
```

## Deleting an Ent

At the moment, we only support "HARD" deletes, meaning that the record is dropped from the DB.

```python
await EntMyObjectMutator.delete(vc, ent).gen_save()
print(f"It's gone!")
```

# Schema API

## Descriptors

EntPy expects you to write "descriptors" for your data objects. It then uses those descriptors to generate all the code necessary to define and access the data in the database, to handle privacy, to handle session management, etc.

Descriptors can be `Schemas`, which are essentially concrete classes, or `Patterns`, which are abstract classes that schemas can implement.

At the minimum, a descriptor will require you to implement the `get_fields` function where you return the list of fields that this object has.

## Fields

Fields have a set of common attributes, such as:
- `not_null()`, which indicates that the field is not optional
- `example(...)`, which enables the developer to provide an example for what the data for this field will look like. It is used in the `EntExample` when generating data for the tests and is mandatory for required fields (that have been marked `not_null`).
- `dynamic_example(lambda: ...)`, which is a more advanced version of `example()` that enables the developer to provide a dyanamically set example. It is useful for mandatory fields that have to be unique to make sure that each example has a different value.
- `default`, which is something that some fields support and allows you to define a default value for the field in case none is provided.
- `unique()`, which sets a unique index on that field and generates additional functions to get an Ent from that field: `gen_from_xxxx` and `genx_from_xxxx`.

Then, we have a list of field types that are provided by the framework:
- `DatetimeField` that stores a datetime object. Note that we store all datetime with tz=UTC.

```python
DatetimeField("my_date")
```
- `EdgeField` stores a reference to another Ent.

```python
EdgeField("my_object", EntMyOtherObjectSchema)
```
This field will be stored in the database as `my_object_id: UUID` and we will also generate a utility function `async def gen_my_object(self) -> EntMyOtherObject` to easily load the edge.

Note that you should not use a field name that ends with `_id`, this will be added for you automatically.
- `EnumField` that stores a python enum.

```python
from enum import Enum

class EnumClass(Enum):
    VAL1 = "VAL1"
    VAL2 = "VAL2"

EnumField("my_enum", EnumClass)
```
- `IntField` that stores an integer.

```python
IntField("my_int")
```
- `JsonField` that stores a JSON object. The second argument after the field name is the python type to which the content of the JsonField will be casted.

```python
JsonField("my_json", "list[str]")
JsonField("my_json_2", "dict[str, str]")
JsonField("my_json_3", "dict[str, Any]")
```
- `StringField` that stores a string. You need to pass the length of the string.

```python
StringField("my_string", 100).example("Hello!")
```
- `TextField` that stores a large string.

```python
TextField("my_large_text")
```

# Gencode

// TODO write me: explain how the gencode works, and how to configure your gencode script

When you add EntPy to your project, you should write your own "gencode" file. It is the script that will get executed to generate the code based on your schemas and patterns.

Here is a sample file:

```python
#!/usr/bin/env python3

from gencode.generator import run

if __name__ == "__main__":
    run(
        schemas_directory="./examples",
        output_directory="./examples/generated",
        base_import="from examples.database import Base",
        session_getter_import="from examples.database import get_session",
        session_getter_fn_name="get_session",
    )
```

Here are some details for the arguments:
- `schemas_directory`: the directory in which the schemas and patterns will be stored. This is what EntPy will scan when trying to generate the code.
- `output_directory`: the directory in which the generated code will be stored.
- `base_import`: an import statement to be used to import the `Base` model from SQLAlchemy in your project. See `examples/database.py` for an example.
- `session_getter_import`: an import statement used to import a function that will enable the framework to obtain a database session. See `examples/database.py` for an example.
- `session_getter_fn_name`: the name of the function imported above.

# Contributing

Before contributing to this repository, it is recommended to add the pre-commit hook:

```bash
cd .git/hooks
ln -s ../../hooks/pre-commit .
```

Always run `ruff` and `mypy` before committing:

```bash
uv run ruff format
uv run ruff check
uv run mypy .
```

Run the tests:

```bash
PYTHONPATH=. uv run pytest examples/__tests__
```

Run the examples with:

```bash
PYTHONPATH=. uv run python examples/run_gencode.py
```

Build the project:

```bash
uv build
```

The artifacts (tar.gz for the source distribution and wheel) are available in `./dist`.

It can be installed in another project with:

```bash
uv add <path to the artifact>/entpy-<version>-py3-none-any.whl
```

# Todolist

- validation for field names
- support gen(x)_from_XXXX for unique fields in patterns
- check that the provided VC extends VC
- check that when adding an edge, the base name is not XXX_id
- generate a list of UUID keys to load in patterns
- limit the limit in queries
- make sure field names are unique (also check edge fields vs XXX_id fields)
- delete cascade?
- entquery in patterns

# Future improvements

Those are things we may tackle later... maybe! Let us know if you're interested!

- Adding a function to `EntXXXCountQuery` to compute the count in a privacy-aware way.
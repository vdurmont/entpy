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

# Using Ents

## Reading an Ent

You have 2 ways to load an Ent:
- Use `gen` to load an Ent and return `None` if it doesn't exist.
- Use `genx` to load an Ent and raise and error if it doesn't exist.

Both will check your privacy rules and only return the Ent if it can be accessed.

```python
optional_ent = await EntMyObject.gen(vc, ent_id)
ent = await EntMyObject.genx(vc, ent_id)
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

# 
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
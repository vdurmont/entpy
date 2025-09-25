# EntPy

Ent Framework for Python.

Run with:

```bash
uv run python ent_gencode.py
```

# Contributing

Before contributing to this repository, it is recommended to add the pre-commit hook:

```bash
cd .git/hooks
ln -s ../../hooks/pre-commit .
```

Always run `ruff` before committing:

```bash
uv run ruff format
uv run ruff check
```
# EntPy

Ent Framework for Python.

Run the examples with:

```bash
PYTHONPATH=. uv run python examples/run_gencode.py
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
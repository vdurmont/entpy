---
name: entpy
description: >-
  Use when reading, writing, or reviewing code in the EntPy data-access and
  privacy framework — schemas, generated Ents, viewer contexts, ordered privacy
  rules, patterns, triggers, mutators, and gencode. EntPy augments SQLAlchemy so
  the safe, privacy-checked path is the standard path; this skill distills the
  load-bearing rules that are easy to get wrong.
---

# EntPy

EntPy is a generated, privacy-aware data-access layer on top of SQLAlchemy. A
schema describes one concrete table; code generation turns it into the
application-facing Ent API; every operation carries a viewer context, and
ordered privacy rules decide whether it may proceed.

This skill is a condensed map. For depth, read the two authoritative docs and
prefer them over anything here:

- `README.md` — the API surface and the exact dev commands.
- `docs/primer.md` — the conceptual model (privacy ordering, patterns,
  triggers, viewer contexts, escape hatches, misconceptions).

## Mental model

You author a **schema** (developer input, one concrete table). Running the
gencode script generates, for a schema `EntX`:

- `EntX` — the privacy-checked entity instance you use in application code;
- `EntXModel` — the raw SQLAlchemy model (used in query filters, and as an
  escape hatch);
- `EntXQuery` — a query builder that returns privacy-checked Ents;
- `EntXMutator` — safe create/update/delete operations;
- `EntXPending` — the proposed post-trigger state that write privacy rules see;
- `EntXExample` — recursively populated test fixtures.

This split explains the syntax: reads go through `EntX.gen(vc, id)` while
filters use model columns such as `EntXModel.title == "..."`.

## Reads

- `EntX.gen(vc, id)` returns `None` if the row does not exist **or is not
  visible**.
- `EntX.genx(vc, id)` raises `EntNotFoundError` in either case.
- Both run `READ` privacy. `None`/not-found is *deliberately*
  indistinguishable from "not visible" — this avoids leaking the existence of
  private rows. Do not try to distinguish them.

Prefer `genx` when absence is exceptional, `gen` when it is an expected branch.
Pass loaded Ents (not naked UUIDs) across boundaries: loading *is* the privacy
check.

## Writes

Writes go through a mutator — **never assign to a loaded model**:

```python
ent = await EntXMutator.create(vc=vc, field1=val1).gen_savex()

mut = await EntXMutator.update(vc, ent)
mut.field1 = new_value
ent = await mut.gen_savex()

await EntXMutator.delete(vc, ent).gen_save()  # HARD delete only, for now
```

The write pipeline is:

```text
caller values → preprocessors → triggers → validation/privacy → flush
```

Privacy evaluates the *trigger-produced* state, so a trigger cannot rewrite a
value to evade a validator or a privacy rule. For `CREATE`/`UPDATE`, a rule
receives both `ent` (current state) and `pending_ent` (proposed state); rules
that restrict a new owner/status/visibility usually inspect `pending_ent`.

## Viewer context (VC)

Every normal read and mutation carries a `ViewerContext` describing **who is
viewing** — not which operation is running. VC classes are application-defined;
a VC is not itself permission, privacy rules interpret it. Two special VCs,
`omniscient` (see everything) and `all_powerful` (see and do everything), are
rare escape hatches — use them as little as possible, only when the real
identity is genuinely unavailable, and construct them at the narrowest call
site.

## Privacy — an ordered firewall (default-deny)

Privacy is evaluated separately per action: `READ`, `CREATE`, `UPDATE`,
`HARD_DELETE`, `SOFT_DELETE`. Each schema's `get_privacy_config(action)` returns
a **non-empty ordered list** of `PrivacyRule` and/or `EdgeDelegate` objects.

Each rule returns `ALLOW`, `DENY`, or `PASS`. **The first `ALLOW` or `DENY`
wins**; if everything returns `PASS`, EntPy **denies by default**. This is an
ordered firewall, not a set of predicates that are all combined.

Consequences that are easy to get wrong:

- **Order is security-sensitive.** Put unconditional guards (e.g. "deny publish
  without admin") *before* rules that can allow (e.g. "allow the owner"), or the
  allow short-circuits and the guard never runs.
- A rule that doesn't recognize the viewer should return `PASS`, not `DENY`, so
  a later rule can decide.
- `AllOf([...])` requires several rules to *all* return `ALLOW` — different from
  listing them sequentially, where an early `ALLOW` finishes evaluation.
- `EdgeDelegate("workspace")` inherits a required, non-nullable parent edge's
  policy for the same action. A decisive parent allow/deny short-circuits the
  child; if the parent all-passes, delegation passes. A child's `pending_ent`
  is **not** forwarded to the parent — write a local rule when authorization
  depends on the child's proposed values.

## Patterns

A `Pattern` is a generated interface/trait, **not** a parent table or FK
inheritance. Implementations stay separate concrete tables; pattern fields
become real columns in each. Schemas opt in via `get_patterns()`, gaining the
generated `I<Name>` interface.

Critical rule: **a privacy rule colocated with a pattern is NOT auto-applied.**
Each concrete schema must explicitly wire those rules into its own
`get_privacy_config()` (order and policy can differ per implementation).
Pattern *triggers*, by contrast, do apply to implementing schemas.

## Escape hatches / no-privacy paths

Ordinary loads, queries, edges, and mutators enforce privacy. These do **not**
— keep them small, named, and reviewed:

- `ent.model` — the raw SQLAlchemy model, no Ent abstraction.
- Raw SQLAlchemy sessions/models (e.g. `session.get(EntXModel, id)`).
- `query_count(vc)` / `gen_count()` — privacy is **not** run when counting; it
  loads and privacy-filters only at/below a threshold (50 by default) and above
  it returns a raw count. `gen_count_NO_PRIVACY()` is always raw.
- Raw SQLAlchemy joins and aggregates silently bypass Ent privacy — prefer an
  Ent query with SQLAlchemy expressions; if a raw query is necessary, reload the
  relevant Ents with the caller's VC before using the result.

## Field types & chaining (pointer)

Field types include `StringField`, `TextField`, `IntField`, `EnumField`,
`JsonField`, `DatetimeField`, `EdgeField`, and more. Chainable methods include
`.not_null()`, `.default()`, `.example()` / `.dynamic_example()`, `.unique()`
(adds `gen_from_<field>`), `.index()`, `.immutable()`, `.validators([...])`,
`.preprocessors([...])`. An `EdgeField("workspace", ...)` stores as
`workspace_id` and generates `gen_workspace()`. See `docs/primer.md` (fields and
chaining) and `README.md` (Schema API) for the full list.

## Dev commands

Lint, format, and type-check (from the README "Contributing" section):

```bash
uv run ruff format
uv run ruff check
uv run mypy .
```

Run the tests:

```bash
PYTHONPATH=. uv run pytest examples/__tests__
```

Regenerate the example Ents after changing schemas or gencode:

```bash
PYTHONPATH=. uv run python examples/run_gencode.py
```

CI (`.github/workflows/python.yaml`) runs ruff/format/mypy/pytest and enforces
that regenerated code is committed ("Check that generated code is up-to-date"):
if regenerating produces a diff, the build fails. Always regenerate and commit
the generated output alongside schema changes.

## Common misconceptions

- **"EntPy is another SQLAlchemy."** It wraps and generates around SQLAlchemy;
  it does not replace it.
- **"A pattern is a parent table."** It is a shared interface whose fields are
  materialized in each implementation; cross-table querying uses a generated
  union view.
- **"Putting a privacy rule beside a pattern applies it."** It does not — every
  concrete schema wires its ordered privacy list explicitly.
- **"All privacy rules run."** Evaluation stops at the first `ALLOW` or `DENY`.
- **"False means deny."** Rules return `ALLOW`, `DENY`, or `PASS`; deny vs.
  not-applicable is fundamental.
- **"A parent allow plus a child deny gives the stricter result."** Not if the
  parent is delegated first — its `ALLOW` stops evaluation. Order the policy to
  express the intended precedence.
- **"The pending Ent is the current row."** On updates it is the proposed
  post-trigger state; compare it with `ent` when transitions matter.
- **"Every Ent operation enforces privacy."** Ordinary loads, queries, edges,
  and mutators do. Large counts may return a raw count; raw models/sessions and
  explicitly named no-privacy helpers are escape hatches.

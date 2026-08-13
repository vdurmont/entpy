# EntPy: a conceptual primer

EntPy is a generated, privacy-aware data-access layer built on SQLAlchemy. It
puts the definition of an application entity, the safe ways to read and change
it, and the authorization policy for those operations in one system.

The shortest useful mental model is:

> A schema describes a concrete table. Code generation turns that description
> into the application-facing Ent API. Every operation carries a viewer context,
> and privacy rules decide whether it may proceed.

EntPy is not a replacement for SQLAlchemy's database engine, sessions, models,
or expression language. Generated Ent queries deliberately accept SQLAlchemy
expressions, and an Ent exposes its underlying SQLAlchemy model when an escape
hatch is necessary. EntPy adds the parts that a conventional ORM does not make
uniform:

- privacy checks on ordinary reads and writes;
- a required identity and authorization context for data access;
- generated, typed read, query, mutation, edge, and test-fixture APIs;
- reusable interfaces that can span multiple concrete tables; and
- one declarative source for fields, validation, preprocessing, indexes,
  triggers, events, and documentation.

The value is not “less SQL.” It is making the safe path the standard path.
Application code should normally use Ents; direct model and session access is
an explicit escape hatch whose caller owns the privacy implications.

## The pieces and how they fit

### Schema: the concrete storage definition

A `Schema` describes one concrete kind of entity and therefore one database
table. Its fields become columns. It also supplies the privacy configuration
for every action.

```python
class EntDocumentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("workspace", EntWorkspaceSchema).not_null(),
            StringField("title", 200).not_null().example("Design notes"),
        ]

    def get_privacy_config(
        self, action: Action
    ) -> list[PrivacyRule | EdgeDelegate]:
        return [EdgeDelegate("workspace")]
```

The schema is developer-authored input, not the class most application code
uses at runtime.

#### Fields

`get_fields()` returns the columns owned by the schema. Fields are nullable by
default and use chainable methods to add constraints and generation metadata:

```python
def get_fields(self) -> list[Field]:
    return [
        EdgeField("workspace", EntWorkspaceSchema)
        .not_null()
        .immutable()
        .documentation("The workspace that owns this document."),
        StringField("title", 200)
        .not_null()
        .not_empty()
        .index()
        .example("Design notes"),
        EnumField("status", DocumentStatus)
        .not_null()
        .default(DocumentStatus.DRAFT),
        JsonField("metadata", "dict[str, str]"),
    ]
```

The basic field types are:

- `StringField(name, length)` for length-bounded strings and
  `TextField(name)` for unbounded text;
- `EmailField(name)` for a validated email string;
- `IntField`, `BigIntField`, and `BoolField` for scalar values;
- `UuidField` and `BytesField`;
- `DateField`, `DatetimeField`, `TimeField`, and `IntervalField` (Python
  `timedelta`);
- `EnumField(name, EnumType)` for Python enums;
- `JsonField(name, "python type")` for JSON with a generated type annotation;
  and
- `EdgeField(name, TargetSchemaOrPattern)` for a reference to another Ent.

Prefer the type that preserves the most meaning. Use `EnumField` for a closed
set of states rather than storing an unchecked string, an edge rather than a
UUID when the value identifies another Ent, and `TextField` when content may
exceed a reasonable fixed bound. Types make invalid states harder to express
and let static analysis catch mistakes before runtime.

An `EdgeField("workspace", ...)` is stored as `workspace_id`; pass the logical
name without `_id`. Code generation also provides `gen_workspace()` to load the
edge through Ent privacy. An edge may target a concrete schema or a pattern.

Common chaining methods include:

- `.not_null()` makes the otherwise-nullable field required;
- `.default(value)` supplies a stored default on field types that support it;
- `.example(value)` or `.dynamic_example(factory)` tells the generated example
  builder how to populate the field; required scalar fields need an example,
  and unique examples should be dynamic;
- `.not_empty()` rejects empty or whitespace-only `StringField` and `TextField`
  values;
- `.index()` creates a single-column index;
- `.unique()` creates a unique single-column index and generated
  `gen_from_<field>()` lookup methods;
- `.immutable()` exposes the field during creation but not through generated
  update mutators;
- `.validators([...])` appends custom value checks;
- `.preprocessors([...])` appends input normalization steps;
- `.documentation(text)` feeds generated API documentation;
- `.internal()` omits the field from the generated API model; and
- `.deprecated()` removes a nullable field from the active generated Ent
  surface while allowing a staged database migration.

Preprocessors run in declaration order before triggers, validation, and
privacy. Validators reject the resulting value during mutation. These are good
for field-local behavior; use a trigger for asynchronous or cross-field work
and a privacy rule for authorization.

> [!NOTE]
> A default is not always helpful. Add one when the system has a genuine default,
> not merely to save the caller an argument. If choosing a value is an important
> product or security decision, require the caller to choose it explicitly.

#### Indexes and uniqueness

Use `.index()` or `.unique()` on a field for a single-column index. For an index
over several columns, implement `get_composite_indexes()`:

```python
def get_composite_indexes(self) -> list[CompositeIndex]:
    return [
        CompositeIndex(
            field_names=["workspace_id", "slug"],
            unique=True,
        ),
        CompositeIndex(field_names=["status", "created_at"]),
    ]
```

Index field names are generated model column names, so edges use names such as
`workspace_id`. `unique=False` is the default. Indexes are partial by default:
their `where` clause excludes soft-deleted rows, allowing a value to be reused
after soft deletion. Pass `where=None` for an index covering every row, or a
SQLAlchemy expression string such as `text("status = 'ACTIVE'")` for a custom
partial index. The expression is emitted for PostgreSQL and SQLite.

An index declared by a pattern is copied to each implementation. A unique
pattern field or composite index additionally enforces uniqueness across all
implementations through the pattern view. Because that requires the view,
non-queryable patterns cannot declare cross-implementation uniqueness. Use
`.unique(pattern=False)` when a field comes from a pattern but only needs to be
unique within each concrete table.

> [!WARNING]
> `.unique()` already creates an index; do not also call `.index()` on the same
> field. For composite indexes, column order matters: put columns used by the
> most common leading filters first. An index on `(account_id, day, category)`
> can support filters beginning with `account_id`, but generally not a filter on
> `day` alone. Avoid retaining redundant single-column and composite indexes
> without a query-driven reason.

#### Privacy configuration

Every concrete schema must implement `get_privacy_config(action)` and return a
non-empty ordered list of `PrivacyRule` and/or `EdgeDelegate` objects for every
action:

```python
def get_privacy_config(
    self, action: Action
) -> list[PrivacyRule | EdgeDelegate]:
    if action == Action.READ:
        return [AllowIfPublic(), EdgeDelegate("workspace")]
    return [EdgeDelegate("workspace")]
```

The action is one of `READ`, `CREATE`, `UPDATE`, `HARD_DELETE`, or
`SOFT_DELETE`. The first decisive rule or delegate wins, and an all-`PASS` list
denies by default. Rule order is therefore part of the security policy. The
later privacy section explains decisions, pending state, delegation, caching,
and safe ordering in detail.

#### Other schema-level behavior

A schema can also:

- implement shared contracts with `get_patterns()`;
- register transactional mutation hooks with `get_triggers()`;
- disable all generated updates with `is_immutable()`;
- describe the Ent with `get_description()`;
- customize its table name or database schema with `get_table_name()` and
  `get_table_schema()`; and
- declare event payload fields with `get_event_fields()`.

Patterns and triggers have dedicated sections below. These methods belong in
the descriptor because code generation needs them; application code should
continue to create and modify rows through the generated mutators.

> [!WARNING]
> Do not copy descriptor overrides from another Ent without understanding why
> they exist. Methods such as `get_uuid_type()`, `get_event_fields()`, table-name
> overrides, and a pattern's `get_example_subclass_name()` solve specific ID,
> event-delivery, migration, or circular-dependency problems. The defaults are
> correct for an ordinary new Ent.

### Generated API: the application-facing layer

Code generation produces several related types from a schema:

- `EntDocument`: a privacy-checked entity instance;
- `EntDocumentModel`: the SQLAlchemy model;
- `EntDocumentQuery`: a query builder returning privacy-checked Ents;
- `EntDocumentMutator`: create, update, and delete operations;
- `EntDocumentPending`: the proposed state visible to write privacy rules; and
- `EntDocumentExample`: recursively populated test data.

This split explains some otherwise surprising syntax. Reads happen through
`EntDocument.gen(vc, id)` while filters use model columns such as
`EntDocumentModel.title == "Design notes"`.

### Viewer context: who is asking

A `ViewerContext` carries the identity and capabilities of the actor performing
an operation. It is passed to every normal read and mutation:

```python
document = await EntDocument.genx(vc, document_id)

documents = await (
    EntDocument.query(vc)
    .where(EntDocumentModel.workspace_id == workspace_id)
    .gen()
)
```

Viewer-context classes are application-defined. They might represent a user,
an API key, a background task, an anonymous request, or a deliberately
privileged maintenance process. A viewer context is not itself permission;
privacy rules interpret it. Highly privileged contexts should remain explicit
and rare because they weaken the main guarantee EntPy provides.

> [!WARNING]
> A viewer context describes **who is viewing**, not which operation a function
> happens to be performing or miscellaneous values convenient to a rule. Put
> proposed entity state in fields and inspect `pending_ent`; pass ordinary
> operation inputs as ordinary arguments.

If a background job acts for a real user or service, carry enough identity in
the job payload to reconstruct that actor's viewer context. Do not silently
replace a missing viewer with a privileged context.

### Ent and model: two views of the same row

An Ent wraps a SQLAlchemy model together with the viewer context under which it
was loaded. Field access feels model-like, and generated edge methods keep the
same viewer context:

```python
workspace = await document.gen_workspace()
raw_model = document.model  # Escape hatch: no additional Ent abstraction.
```

Loading an Ent runs `READ` privacy. `gen()` returns `None` when the row does not
exist *or is not visible*; `genx()` raises `EntNotFoundError` in either case.
This deliberate indistinguishability avoids leaking the existence of private
rows.

> [!NOTE]
> Pass loaded Ents across application and service boundaries when the callee
> needs the entity. Loading is the privacy check; passing only a naked UUID
> makes every callee rely on an undocumented promise that somebody checked it.
> Accept an ID when the entity genuinely need not be loaded, or at an input
> boundary whose job is to resolve it.

Prefer `genx(vc, value)` when absence is exceptional and `gen(vc, value)` when
it is an expected branch. The load methods validate and parse string IDs, so
manual `UUID(value)` conversion and `gen()` followed only by a `None` check add
noise. In application helper signatures, consistently placing `vc` first also
makes the authorization context difficult to overlook.

At an HTTP boundary, `genx_or_404()` provides the corresponding not-found
translation, and mutation helpers ending in `_or_403` translate privacy denial
for the response layer. Keep those transport-specific variants at that
boundary; internal services generally benefit from the Ent exceptions.

### Mutators and pending state

Writes go through a generated mutator rather than by assigning to a loaded
model:

```python
document = await EntDocumentMutator.create(
    vc=vc,
    workspace_id=workspace_id,
    title="Design notes",
).gen_savex()

mutation = await EntDocumentMutator.update(vc, document)
mutation.title = "Architecture notes"
document = await mutation.gen_savex()
```

For `CREATE` and `UPDATE`, a privacy rule receives both `ent` and
`pending_ent`. The former is the current state (or the new wrapper during
creation); the latter is the proposed post-trigger state. A rule restricting a
new owner, visibility, role, or status usually needs to inspect `pending_ent`.
Edge delegation does not forward a child's pending state to its parent because
that state has the child's type and meaning.

The write pipeline is broadly: preprocess supplied values, run triggers,
evaluate validation and privacy against the resulting state, then flush. Do
not rely on a trigger to evade a validator or privacy rule.

### Triggers: transactional mutation hooks

An `EntTrigger` is application code that runs inside an Ent mutation before the
row is flushed. Despite the name, it is not a database trigger: it runs only
when a write goes through an Ent mutator.

Triggers are useful for work that belongs to the mutation itself:

- computing a stored field, such as a slug derived from a name;
- keeping related Ents in sync;
- creating a related Ent as part of a larger atomic operation;
- implementing transactional cascade behavior; or
- aborting the mutation by raising an exception.

A schema or pattern registers triggers with `get_triggers()`:

```python
class EntDocumentSchema(Schema):
    def get_triggers(self) -> list[EntTrigger]:
        return [DocumentTrigger()]


class DocumentTrigger(EntTrigger[ViewerContext, EntDocumentModel]):
    async def gen_on_create(
        self, vc: ViewerContext, model: EntDocumentModel
    ) -> EntDocumentModel:
        model.slug = slugify(model.title)
        return model

    async def gen_on_update(
        self,
        vc: ViewerContext,
        old_model: EntDocumentModel,
        new_model: EntDocumentModel,
    ) -> EntDocumentModel:
        if old_model.title != new_model.title:
            new_model.slug = slugify(new_model.title)
        return new_model

    async def gen_on_delete(
        self,
        vc: ViewerContext,
        model: EntDocumentModel,
        is_soft_delete: bool,
    ) -> None:
        pass
```

On create, the trigger receives and returns the model being built. On update,
`old_model` is a snapshot of the current row and `new_model` is a working copy
containing the caller's proposed changes; the returned model becomes the
pending state examined by privacy. On delete, the trigger receives the current
model as context and whether the operation is a soft delete.

The important ordering is:

```text
caller values → preprocessors → triggers → validation/privacy → flush
```

Triggers therefore cannot rewrite a value after authorization: privacy rules
evaluate the trigger-produced state. Trigger code can call other Ent mutators,
and those writes participate in the caller's transaction and run their own
privacy checks. A trigger that intentionally needs different authority must
construct an explicit viewer context for that nested operation rather than
assuming the caller has it.

Pattern triggers apply to implementing schemas, which is useful when shared
mutation behavior is part of the pattern's contract. This differs from pattern
privacy rules: reusable rule classes colocated with a pattern still have to be
wired explicitly into each concrete schema's privacy configuration.

Because triggers run before authorization and commit, they must not perform
irreversible external side effects such as sending email, publishing a message,
or calling a third-party API. A later validation failure, privacy denial, or
transaction rollback would undo database changes but not the external action.
Use triggers only for rollback-safe model shaping, transactional Ent work, and
aborting invalid operations.

## Patterns: shared contract and polymorphism

An EntPy `Pattern` is closer to a generated interface or trait than to an ORM
base table. A pattern can define fields, indexes, triggers, events, and other
patterns. Concrete schemas opt into it with `get_patterns()`:

```python
class EntOwnablePattern(Pattern):
    def get_fields(self) -> list[Field]:
        return [EdgeField("owner", EntAccountPattern).not_null()]


class EntProjectSchema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntOwnablePattern()]
```

The generated `IEntOwnable` interface can represent any implementing Ent.
Pattern fields become real columns in each implementing table, and their
mutator surface is available through both the concrete and pattern APIs.

Use a pattern when callers need a shared, typed capability (“has an owner,”
“can be archived,” “is an actor”), or need to load/query heterogeneous entities
through one interface. Do not use one merely to avoid repeating a couple of
fields when no common semantic contract exists.

> [!NOTE]
> When one field may reference several kinds of Ent, model the target kinds with
> a pattern and use one `EdgeField` to that pattern. Avoid loose
> `target_type`/`target_id` pairs or one nullable edge per possible target. The
> pattern preserves referential integrity, generated loading, privacy, and
> static typing while remaining open to new implementations.

Patterns also replace field-name-based duck typing. If a reusable rule or
service requires an `owner_id`, define a “has owner” pattern with that edge and
type the code against its generated interface. Do not probe arbitrary Ents with
`getattr()` or teach a supposedly generic rule a growing list of concrete Ent
special cases. If there is no honest shared contract, use concrete rules.

### Patterns are not tables or foreign-key inheritance

Implementations remain separate concrete tables. EntPy entity IDs encode the
concrete entity type, allowing a pattern's `gen()`/`gen_by_ids()` to dispatch to
the correct implementation. A queryable pattern additionally generates a
database view that unions its implementations so `IEntOwnable.query(vc)` can
query across them.

If polymorphic queries are unnecessary, override `is_queryable()` to return
`False`. Loading by ID, inherited fields, mutators, and interfaces still work;
only the union view and `query()` disappear. A non-queryable pattern cannot
enforce uniqueness across implementations, so it cannot declare a unique field
or unique composite index.

### Pattern composition is explicit

Patterns can include other patterns, but `get_patterns()` is not inferred from
Python inheritance or from fields that happen to look alike. List every
contract the descriptor implements. Fields with the same name in multiple
included descriptors are an error, not an override mechanism.

Most importantly, **patterns do not supply a schema's privacy configuration**.
A pattern may colocate reusable `PrivacyRule` classes with its contract, but
each concrete schema must explicitly put those rules in
`get_privacy_config()`. This is intentional: the correct policy and rule order
can differ between implementations and actions.

## Privacy rules: an ordered decision list

Privacy is evaluated separately for `READ`, `CREATE`, `UPDATE`, `HARD_DELETE`,
and `SOFT_DELETE`. `get_privacy_config(action)` must return a non-empty ordered
list containing rules and/or edge delegates.

Every rule returns one of three decisions:

- `ALLOW`: permit the operation immediately;
- `DENY`: reject the operation immediately; or
- `PASS`: this rule does not decide; continue to the next item.

The first `ALLOW` or `DENY` wins. If everything returns `PASS`, EntPy denies by
default. This is an ordered firewall, not a set of predicates that are all
combined.

```text
prepended rules → schema rules/delegates, in order
                         │
                 PASS ───┤ try next
                ALLOW ───┤ stop: allow
                 DENY ───┘ stop: deny
all PASS → deny
```

This makes ordering security-sensitive. Put unconditional guards before rules
that can allow. For example, “deny publishing without admin permission” must
run before a general “allow the owner” rule, or the owner rule will
short-circuit and the guard will never execute. A rule should return `PASS`,
not `DENY`, when it simply does not recognize the viewer or situation and a
later rule should get a chance to decide.

> [!NOTE]
> Prefer small rules with one job: an allow rule should allow or pass, and a deny
> rule should deny or pass. A combined “allow this viewer, deny everybody else”
> rule is terminal in both branches and is difficult to compose. Default-closed
> evaluation usually makes the explicit `DENY` branch unnecessary.

`AllOf([...])` is available when several rules truly must all return `ALLOW`.
It is different from placing those rules sequentially, where any early
`ALLOW` would finish evaluation.

### Edge delegation: inherit policy from a parent

`EdgeDelegate("workspace")` evaluates the same action against the entity at a
required edge. This is useful when a dependent row has exactly the same access
boundary as its owner or container:

```python
def get_privacy_config(
    self, action: Action
) -> list[PrivacyRule | EdgeDelegate]:
    return [EdgeDelegate("workspace")]
```

The edge must exist and be non-nullable. Delegation is itself one item in the
ordered list. If the parent's rules all pass, delegation passes and the child
continues to its next rule; a decisive parent allow or deny short-circuits the
child. Delegation loads the parent without first applying ordinary read
privacy, then evaluates the requested action, avoiding the circular requirement
that one must already read the parent to ask it for authorization.

Delegate when the child's boundary really is the parent's boundary. Write a
child rule when authorization depends on the child's proposed values, since a
child's `pending_ent` is not passed to the delegate.

### Global prepended rules

Applications can provide a privacy mixin whose `_get_prepended_rules(action)`
adds rules before every schema's configuration. This is the right place for
truly global behavior such as a narrowly controlled test bypass or denying
reads of soft-deleted rows. Because prepended rules run first, an `ALLOW` there
bypasses all schema rules; treat additions to this list as framework-level
security changes.

> [!WARNING]
> Never add a schema rule for a privileged viewer that the application's
> prepended rules already handle. More generally, do not reach for a privileged
> viewer context because a legitimate operation was denied: fix the policy or
> use the caller's context. If a maintenance operation genuinely must bypass
> privacy, construct the privileged context at the narrowest call site, use it
> for only that operation, and do not pass it through a service where unrelated
> reads and writes could inherit it. If privileged traversal discovers an ID to
> return to a caller, reload the final Ent with the caller's viewer context.

### Rule caching

A rule can implement `cache_key(ent)` to reuse its decision within the current
database session for the same rule type, viewer-context object, and key. Only
use this when every input that can change the decision is represented by that
key. In particular, the built-in cache key does not include `pending_ent` or
the action. Mutation rules whose decision depends on proposed values should
usually remain uncached unless their key safely captures that state.

Keep authorization as close to Ent access as possible. A route or other caller
may enforce broader workflow requirements, but entity access policy belongs in
privacy rules. Hand-written checks at one entry point neither protect other
callers nor compose with generated edge and mutator access; repeating an
existing rule in a route creates two policies that can drift apart. Likewise,
delete behavior is policy: deliberately decide which viewers, if any, may hard
delete, soft delete, or neither.

## Queries and the privacy boundary

Ent queries use SQLAlchemy expressions but convert rows to Ents and apply read
privacy. This can mean that a database `limit(10)` yields fewer than ten Ents:
the limit selects candidate rows before application-level privacy removes
invisible ones.

Count queries are a notable exception. `gen_count()` first obtains a raw count;
when that count is at or below its privacy threshold (50 by default), it loads
the rows and returns the privacy-filtered count. Above the threshold it returns
the raw count without per-row privacy, trading precision for bounded work.
`gen_count_NO_PRIVACY()` is always raw. Use either only when the SQL filters
establish an acceptable visibility boundary, the count is intentionally
privileged, or the threshold behavior is acceptable. Direct SQLAlchemy access
has the same general responsibility and should be visibly treated as a
no-privacy path.

> [!WARNING]
> Raw SQLAlchemy joins and aggregates silently bypass Ent privacy. Prefer an Ent
> query with SQLAlchemy expressions. When a specialized raw query is genuinely
> necessary, make the no-privacy boundary obvious and separately load the
> relevant Ents with the caller's viewer context before using or returning the
> result. “The route already checked something similar” is not a substitute for
> authorizing the rows that were read.

## Modeling choices that prevent later mistakes

The framework cannot decide whether a schema represents the right domain
model. Before adding columns or rules, sketch the existing edge graph and ask
what each new fact means.

### Follow edges before denormalizing

Do not add a direct `root_id` merely because a frequently used parent can reach
the root, or copy both `parent_id` and `container_id` when the parent already
identifies its container. Generated edge methods make traversal ordinary, and
privacy can delegate through the same chain. A child that delegates to its
parent can inherit the parent's delegation without copying a distant ownership
edge and reproducing its policy.

Redundant edges create consistency questions: which value is authoritative,
what prevents disagreement, and which one should privacy trust? Denormalize
only for a measured query or reliability requirement, and then document and
enforce how the copies stay consistent. Choose the edge matching the actual
concept—for example, an association entity representing “this member in this
group” can be a better target than two independent edges to member and group.

When behavior or data genuinely belongs to every implementation of a pattern,
put it on that pattern rather than repeating it in each concrete schema.

### Preserve useful information

Small field choices determine how many migrations and ambiguous states appear
later:

- Prefer a nullable timestamp such as `disabled_at` over `is_disabled` when
  the time of the change matters; add an actor edge when who changed it
  matters.
- Prefer an edge to the event or Ent that caused a state over a Boolean saying
  that something happened.
- Name mutable references to communicate that they change, such as
  `latest_revision`, rather than giving them timeless names.
- Record provenance, source, and actor fields when the domain will plausibly
  need them. Adding them before data exists is much cheaper than reconstructing
  them in a backfill.
- Avoid representing the same lifecycle twice. A soft-deleted row often does
  not also need a `REVOKED` or `DELETED` status unless those states have a
  distinct domain meaning.

Patterns are queryable by default. Keep that default unless avoiding the union
view is an intentional tradeoff and callers truly do not need polymorphic
queries. Similarly, choose deletion policy from retention and lifecycle needs:
some data should be archived, some may be soft-deleted, and some ephemeral data
may only support hard deletion. Do not copy another schema's choice by habit.

## A practical design recipe

When adding an entity, work through these questions in order:

1. What concrete row is stored? Put only its own fields in a `Schema`.
2. Which real shared capabilities does it implement? Add the relevant
   `Pattern` instances explicitly.
3. Who is acting? Make sure the operation receives the least-privileged useful
   viewer context.
4. For each action, what must always be forbidden, who may allow it, and when
   should a rule merely pass? Write the ordered list down in that order.
5. Does the entity exactly inherit an owner's boundary? If so, delegate over a
   required edge; otherwise write a local rule.
6. Does write authorization depend on the new state? Inspect `pending_ent` and
   be cautious with caching.
7. Will callers query across implementations? Keep the pattern queryable only
   when the union view is useful.
8. Could this code bypass Ent privacy through models, counts, or no-privacy
   helpers? Keep that access small, named, and reviewed.

Tests should cover each action and viewer kind, both decisive and `PASS` paths,
rule ordering, proposed-state changes, and delegation. A successful authorized
case alone is not enough; the dangerous regressions are usually an earlier
allow that makes a later deny unreachable, or a rule that returns `DENY` where
it meant “not applicable.”

## Common misconceptions

- **“EntPy is another SQLAlchemy.”** It wraps and generates around SQLAlchemy;
  it does not replace it.
- **“A pattern is a parent table.”** It is a shared interface/contract whose
  fields are materialized in each implementation; cross-table querying uses a
  generated union view.
- **“Putting a privacy rule beside a pattern applies it.”** It does not. Every
  concrete schema wires its ordered privacy list explicitly.
- **“All privacy rules run.”** Evaluation stops at the first `ALLOW` or `DENY`.
- **“False means deny.”** Rules return `ALLOW`, `DENY`, or `PASS`; the
  distinction between deny and not-applicable is fundamental.
- **“A parent allow plus a child deny gives the stricter result.”** Not if the
  parent is delegated first: its `ALLOW` stops evaluation. Order the policy to
  express the intended precedence.
- **“The pending Ent is the current row.”** On updates it represents the
  proposed post-trigger state; compare it with `ent` when transitions matter.
- **“Every Ent operation enforces privacy.”** Ordinary loads, queries, edges,
  and mutators do. Large counts may return a raw count; raw models/sessions and
  explicitly named no-privacy helpers are escape hatches.

from collections.abc import Callable
from typing import Any

from alembic.operations import MigrateOperation, Operations
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement


def gen_postgresql_function(
    pattern: str, _table: str, columns: list[str], quote: Callable[[str], str]
) -> str:
    where_clause = " AND ".join(f"{c} = NEW.{c}" for c in columns)
    return f"""
        CREATE OR REPLACE FUNCTION unique_{pattern}_{"_".join(columns)}() RETURNS TRIGGER AS $$
        BEGIN
            PERFORM 1 FROM {quote(pattern)} WHERE {where_clause} AND id != NEW.id AND soft_deleted_at IS NULL;
            IF FOUND THEN
                RAISE EXCEPTION 'duplicate key value violates unique constraint "unique_{pattern}_{"_".join(columns)}"';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
    """


def gen_postgresql_trigger(
    pattern: str, table: str, columns: list[str], quote: Callable[[str], str]
) -> str:
    return f"""
        CREATE OR REPLACE TRIGGER unique_{table}_{"_".join(columns)}
        AFTER INSERT OR UPDATE OF {", ".join(columns)} ON {quote(table)}
        FOR EACH ROW EXECUTE FUNCTION unique_{pattern}_{"_".join(columns)}()
    """


def gen_sqlite_trigger(
    event: str,
    pattern: str,
    table: str,
    columns: list[str],
    quote: Callable[[str], str],
) -> str:
    where_clause = " AND ".join(f"{c} = NEW.{c}" for c in columns)
    event_clause = event.upper()
    if event == "update":
        event_clause = "UPDATE OF " + ", ".join(columns)
    return f"""
        CREATE TRIGGER IF NOT EXISTS unique_{table}_{"_".join(columns)}_{event}
        BEFORE {event_clause} ON {quote(table)}
        FOR EACH ROW
        WHEN EXISTS (
            SELECT 1 FROM {quote(pattern)} WHERE {where_clause} AND id != NEW.id AND soft_deleted_at IS NULL
        )
        BEGIN
            SELECT RAISE(ABORT, 'UNIQUE constraint failed: unique_{pattern}_{"_".join(columns)}');
        END;
    """


class CreatePatternUniqueFunctionPostgres(DDLElement):
    def __init__(self, pattern: str, table: str, columns: list[str]):
        self.pattern = pattern
        self.table = table
        self.columns = columns


@compiler.compiles(CreatePatternUniqueFunctionPostgres)
def compile_create_pattern_unique_function_postgres(
    element: CreatePatternUniqueFunctionPostgres, compiler: Any, **kwargs: Any
) -> str:
    return gen_postgresql_function(
        element.pattern,
        element.table,
        element.columns,
        compiler.dialect.identifier_preparer.quote,
    )


class CreatePatternUniqueTriggerPostgres(DDLElement):
    def __init__(self, pattern: str, table: str, columns: list[str]):
        self.pattern = pattern
        self.table = table
        self.columns = columns


@compiler.compiles(CreatePatternUniqueTriggerPostgres)
def compile_create_pattern_unique_trigger_postgres(
    element: CreatePatternUniqueTriggerPostgres, compiler: Any, **kwargs: Any
) -> str:
    return gen_postgresql_trigger(
        element.pattern,
        element.table,
        element.columns,
        compiler.dialect.identifier_preparer.quote,
    )


class CreatePatternUniqueTriggerSqlite(DDLElement):
    def __init__(self, event: str, pattern: str, table: str, columns: list[str]):
        self.pattern = pattern
        self.table = table
        self.columns = columns
        self.event = event


@compiler.compiles(CreatePatternUniqueTriggerSqlite)
def compile_create_pattern_unique_trigger_sqlite(
    element: CreatePatternUniqueTriggerSqlite, compiler: Any, **kwargs: Any
) -> str:
    return gen_sqlite_trigger(
        element.event,
        element.pattern,
        element.table,
        element.columns,
        compiler.dialect.identifier_preparer.quote,
    )


@Operations.register_operation("create_pattern_unique_constraint")
class CreatePatternUniqueOp(MigrateOperation):
    def __init__(self, pattern: str, table: str, columns: list[str]):
        self.pattern = pattern
        self.table = table
        self.columns = columns

    @classmethod
    def create_pattern_unique_constraint(
        cls, operations: Operations, pattern: str, table: str, columns: list[str]
    ) -> Any:
        op = CreatePatternUniqueOp(pattern, table, columns)
        return operations.invoke(op)

    def reverse(self) -> "DropPatternUniqueOp":
        return DropPatternUniqueOp(self.pattern, self.table, self.columns)

    def to_diff_tuple(self) -> tuple[str, str, str, list[str]]:
        return (
            "create_pattern_unique_constraint",
            self.pattern,
            self.table,
            self.columns,
        )


@Operations.implementation_for(CreatePatternUniqueOp)
def create_pattern_unique_constraint(
    operations: Operations, operation: CreatePatternUniqueOp
) -> None:
    quote = operations.get_context().dialect.identifier_preparer.quote
    if operations.get_context().dialect.name == "postgresql":
        operations.execute(
            gen_postgresql_function(
                operation.pattern, operation.table, operation.columns, quote
            )
        )
        operations.execute(
            gen_postgresql_trigger(
                operation.pattern, operation.table, operation.columns, quote
            )
        )
    elif operations.get_context().dialect.name == "sqlite":
        operations.execute(
            gen_sqlite_trigger(
                "insert", operation.pattern, operation.table, operation.columns, quote
            )
        )
        operations.execute(
            gen_sqlite_trigger(
                "update", operation.pattern, operation.table, operation.columns, quote
            )
        )
    else:
        raise NotImplementedError(
            f"Unsupported dialect: {operations.get_context().dialect.name}"
        )


@Operations.register_operation("drop_pattern_unique_constraint")
class DropPatternUniqueOp(MigrateOperation):
    def __init__(self, pattern: str, table: str, columns: list[str]):
        self.pattern = pattern
        self.table = table
        self.columns = columns

    @classmethod
    def drop_pattern_unique_constraint(
        cls, operations: Operations, pattern: str, table: str, columns: list[str]
    ) -> Any:
        op = DropPatternUniqueOp(pattern, table, columns)
        return operations.invoke(op)

    def reverse(self) -> "CreatePatternUniqueOp":
        return CreatePatternUniqueOp(self.pattern, self.table, self.columns)

    def to_diff_tuple(self) -> tuple[str, str, str, list[str]]:
        return (
            "drop_pattern_unique_constraint",
            self.pattern,
            self.table,
            self.columns,
        )


@Operations.implementation_for(DropPatternUniqueOp)
def drop_pattern_unique_constraint(
    operations: Operations, operation: DropPatternUniqueOp
) -> None:
    quote = operations.get_context().dialect.identifier_preparer.quote
    if operations.get_context().dialect.name == "postgresql":
        operations.execute(
            f"DROP TRIGGER IF EXISTS unique_{operation.table}_{"_".join(operation.columns)} ON {quote(operation.table)}"
        )
    elif operations.get_context().dialect.name == "sqlite":
        operations.execute(
            f"DROP TRIGGER IF EXISTS unique_{operation.table}_{"_".join(operation.columns)}_insert"
        )
        operations.execute(
            f"DROP TRIGGER IF EXISTS unique_{operation.table}_{"_".join(operation.columns)}_update"
        )
    else:
        raise NotImplementedError(
            f"Unsupported dialect: {operations.get_context().dialect.name}"
        )

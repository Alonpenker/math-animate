import argparse
import sys
from dataclasses import dataclass, field

from app.repositories import (
    Repository,
    ArtifactsRepository,
    JobRequestsRepository,
    KnowledgeRepository,
    PlansRepository,
    TokenLedgerRepository,
)
from app.utils.logging import APILog, Logger


logger = Logger.get_logger("api")
ALL_REPOSITORIES: tuple[type[Repository], ...] = (
    PlansRepository,
    ArtifactsRepository,
    KnowledgeRepository,
    TokenLedgerRepository,
    JobRequestsRepository,
)
REPOSITORIES_BY_TABLE = {repo.TABLE_NAME: repo for repo in ALL_REPOSITORIES}


@dataclass
class MigrationResult:
    table_name: str
    operations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def migrate_repository_schemas(
    cursor,
    repositories: tuple[type[Repository], ...] = ALL_REPOSITORIES,
    *,
    dry_run: bool = False,
    allow_destructive: bool = False,
) -> list[MigrationResult]:
    logger.info(APILog(
        operation="migrate_schema",
        event="Schema migration started",
        context={
            "tables": [repository.TABLE_NAME for repository in repositories],
            "dry_run": dry_run,
            "allow_destructive": allow_destructive,
        },
    ))
    results: list[MigrationResult] = []
    try:
        for repository in repositories:
            results.append(migrate_repository_schema(
                cursor,
                repository,
                dry_run=dry_run,
                allow_destructive=allow_destructive,
            ))
    except Exception as exc:
        logger.error(APILog(
            operation="migrate_schema",
            event="Schema migration failed",
            error=Logger.serialize_error(exc),
            context={
                "tables": [repository.TABLE_NAME for repository in repositories],
                "dry_run": dry_run,
                "allow_destructive": allow_destructive,
            },
        ), exc_info=exc)
        raise

    logger.info(APILog(
        operation="migrate_schema",
        event="Schema migration completed",
        context={
            "tables": [result.table_name for result in results],
            "operation_count": sum(len(result.operations) for result in results),
            "warning_count": sum(len(result.warnings) for result in results),
            "dry_run": dry_run,
        },
    ))
    return results


def migrate_repository_schema(
    cursor,
    repository: type[Repository],
    *,
    dry_run: bool = False,
    allow_destructive: bool = False,
) -> MigrationResult:
    result = MigrationResult(repository.TABLE_NAME)
    table_exists = _table_exists(cursor, repository.TABLE_NAME)

    if not table_exists:
        _run(cursor, repository._create(), result, dry_run=dry_run)

    # Adds any missing columns
    expected_columns = {column.name for column in repository.SCHEMA.columns()}
    existing_columns = _existing_columns(cursor, repository.TABLE_NAME) if table_exists else expected_columns
    for column in repository.SCHEMA.columns():
        if column.name not in existing_columns:
            _run(
                cursor,
                (
                    f"ALTER TABLE {repository.TABLE_NAME} "
                    f"ADD COLUMN {column.name} {column.sql_type}"
                ),
                result,
                dry_run=dry_run,
            )
    
    # Remove any column missing from code schema (given --allow-destructive flag)
    extra_columns = _existing_columns(cursor, repository.TABLE_NAME) - expected_columns
    for column_name in sorted(extra_columns):
        if allow_destructive:
            _run(
                cursor,
                f"ALTER TABLE {repository.TABLE_NAME} DROP COLUMN {column_name}",
                result,
                dry_run=dry_run,
            )
        else:
            warning = (
                f"{repository.TABLE_NAME}.{column_name} exists in DB but not in code; "
                "pass --allow-destructive to drop it."
            )
            result.warnings.append(warning)
            logger.warning(APILog(
                operation="migrate_schema",
                event="Schema migration warning",
                context={"table": repository.TABLE_NAME, "warning": warning},
            ))

    # Create indexes
    existing_indexes = _existing_indexes(cursor, repository.TABLE_NAME) if table_exists else set()
    for field_name in repository.INDEX_FIELDS:
        index_name = f"idx_{repository.TABLE_NAME}_{field_name}"
        if index_name not in existing_indexes:
            _run(cursor, repository._create_index(field_name), result, dry_run=dry_run)

    if result.operations or result.warnings:
        logger.info(APILog(
            operation="migrate_schema",
            event="Table migration completed",
            context={
                "table": repository.TABLE_NAME,
                "operation_count": len(result.operations),
                "warning_count": len(result.warnings),
                "dry_run": dry_run,
            },
        ))
    return result


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        ) AS exists
        """,
        (table_name,),
    )
    row = cursor.fetchone()
    return bool(row["exists"] if isinstance(row, dict) else row[0])


def _existing_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        """,
        (table_name,),
    )
    rows = cursor.fetchall()
    return {row["column_name"] if isinstance(row, dict) else row[0] for row in rows}


def _existing_indexes(cursor, table_name: str) -> set[str]:
    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s
        """,
        (table_name,),
    )
    rows = cursor.fetchall()
    return {row["indexname"] if isinstance(row, dict) else row[0] for row in rows}


def _run(cursor, sql: str, result: MigrationResult, *, dry_run: bool) -> None:
    result.operations.append(sql)
    logger.debug(APILog(
        operation="migrate_schema",
        event="Schema migration operation prepared",
        context={
            "table": result.table_name,
            "dry_run": dry_run,
            "sql": sql,
        },
    ))
    if not dry_run:
        cursor.execute(sql)


def _select_repositories(table_name: str | None, migrate_all: bool) -> tuple[type[Repository], ...]:
    if migrate_all:
        return ALL_REPOSITORIES
    if table_name is None:
        raise ValueError("Pass --all or --table <name>.")
    repository = REPOSITORIES_BY_TABLE.get(table_name)
    if repository is None:
        allowed = ", ".join(sorted(REPOSITORIES_BY_TABLE))
        raise ValueError(f"Unsupported table '{table_name}'. Allowed tables: {allowed}")
    return (repository,)


def _print_results(results: list[MigrationResult]) -> None:
    printed = False
    for result in results:
        if not result.operations and not result.warnings:
            continue
        printed = True
        print(f"{result.table_name}:")
        for operation in result.operations:
            print(f"OPERATION: {operation}")
        for warning in result.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    if not printed:
        print("No schema changes required.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate application table schemas.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--all", action="store_true", help="migrate every repository table")
    target.add_argument("--table", choices=sorted(REPOSITORIES_BY_TABLE), help="table to migrate")
    parser.add_argument("--dry-run", action="store_true", help="print changes without applying them")
    parser.add_argument(
        "--allow-destructive",
        action="store_true",
        help="drop DB columns that no longer exist in code",
    )
    args = parser.parse_args()

    from app.dependencies import db

    db.init_db_pool()
    try:
        with db.get_db_cursor() as cursor:
            if not args.dry_run:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            results = migrate_repository_schemas(
                cursor,
                _select_repositories(args.table, args.all),
                dry_run=args.dry_run,
                allow_destructive=args.allow_destructive,
            )
        _print_results(results)
    finally:
        db.close_db_pool()


if __name__ == "__main__":
    main()

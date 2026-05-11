"""Storage adapter for workflow persistence and checkpointing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


def initialize_storage_layer(
    storage_type: str = "memory", connection_string: str | None = None
) -> BaseCheckpointSaver | None:
    """Configures the persistence mechanism for the graph execution.

    Supports in-memory storage for testing and SQLite/Postgres for persistent 
    state management across sessions.
    """
    if storage_type == "none":
        return None
        
    if storage_type == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
        
    if storage_type == "sqlite":
        import sqlite3
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore[import-not-found]
        except ImportError as err:
            raise RuntimeError(
                "SQLite persistence requires 'langgraph-checkpoint-sqlite' package."
            ) from err
        
        db_path = connection_string or "checkpoints.db"
        connection = sqlite3.connect(db_path, check_same_thread=False)
        # Optimize performance with Write-Ahead Logging
        connection.execute("PRAGMA journal_mode=WAL")
        return SqliteSaver(connection)
        
    if storage_type == "postgres":
        try:
            from langgraph.checkpoint.postgres import (  # type: ignore[import-not-found]
                PostgresSaver,
            )
        except ImportError as err:
            raise RuntimeError(
                "Postgres persistence requires 'langgraph-checkpoint-postgres' package."
            ) from err
        return PostgresSaver.from_conn_string(connection_string or "")
        
    raise ValueError(f"Unsupported storage provider: {storage_type}")

"""Dialect-agnostic column types for the persistence models.

The deployment target is PostgreSQL 15 or later, where JSON payloads use the
native ``jsonb`` type and identifiers use the native ``uuid`` type. The test
suite and the offline demo run on SQLite, which has neither. Declaring the
PostgreSQL types directly on the models would therefore make the schema
unusable anywhere except PostgreSQL, and Alembic would emit migration code
that references names it never imported.

Each type below is declared once here as a generic SQLAlchemy type with a
PostgreSQL variant, so the same model definitions serve both dialects.
"""

from __future__ import annotations

from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID

__all__ = ["JSONType", "UUIDType"]

# Generic JSON, upgraded to native jsonb on PostgreSQL.
JSONType = JSON().with_variant(JSONB, "postgresql")

# Generic UUID, upgraded to native uuid on PostgreSQL.
UUIDType = Uuid(as_uuid=True).with_variant(UUID, "postgresql")

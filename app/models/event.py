"""
For the 10-hour MVP we don't use a database/ORM.
This module just re-exports the Pydantic schema so the rest of the
codebase can `from app.models.event import Event` as if it were a
real model. Swapping in SQLAlchemy/PostGIS later only means changing
this file, not every file that imports it.
"""

from app.schemas.event import EventOut as Event

__all__ = ["Event"]

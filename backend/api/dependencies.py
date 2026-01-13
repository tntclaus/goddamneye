"""FastAPI dependencies for injection."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]

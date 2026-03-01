"""Common API dependencies."""

from llm_deploy.database import async_session_factory


async def get_db():
    """Yield a database session for request scope."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

"""
Database connection and session management.

This module provides:
- SQLAlchemy engine creation
- Database session management
- Connection pooling
- Transaction handling
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from .config import settings


# Configure logging
logger = logging.getLogger(__name__)


# ============================================
# DATABASE ENGINE
# ============================================

def create_db_engine():
    """
    Create SQLAlchemy engine with connection pooling.

    Returns:
        SQLAlchemy engine instance
    """
    engine_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 10,  # Number of connections to maintain
        "max_overflow": 20,  # Additional connections beyond pool_size
        "pool_timeout": 30,  # Timeout for getting connection from pool
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using
        "echo": settings.DB_ECHO,  # Log SQL statements (development only)
    }

    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )

    # Add event listeners
    _add_engine_listeners(engine)

    logger.info(
        f"Database engine created: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}"
    )

    return engine


def _add_engine_listeners(engine):
    """
    Add event listeners to the engine for monitoring and optimization.

    Args:
        engine: SQLAlchemy engine instance
    """

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Handle new connections."""
        logger.debug("New database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Handle connection checkout from pool."""
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Handle connection return to pool."""
        logger.debug("Connection returned to pool")


# Create global engine instance
engine = create_db_engine()


# ============================================
# SESSION FACTORY
# ============================================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Allow access to objects after commit
)


# ============================================
# SESSION MANAGEMENT
# ============================================

def get_db() -> Generator[Session, None, None]:
    """
    Get database session dependency for FastAPI.

    Yields:
        Database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get database session as context manager.

    Yields:
        Database session

    Example:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# ============================================
# TRANSACTION MANAGEMENT
# ============================================

class DatabaseTransaction:
    """
    Context manager for database transactions with automatic rollback on error.

    Example:
        with DatabaseTransaction() as db:
            campaign = Campaign(name="Test")
            db.add(campaign)
            # Automatically committed if no exception
    """

    def __init__(self, session: Session = None):
        """
        Initialize transaction.

        Args:
            session: Optional existing session, otherwise creates new one
        """
        self.session = session
        self.owns_session = session is None

    def __enter__(self) -> Session:
        """Enter transaction context."""
        if self.owns_session:
            self.session = SessionLocal()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        try:
            if exc_type is None:
                self.session.commit()
                logger.debug("Transaction committed successfully")
            else:
                self.session.rollback()
                logger.warning(f"Transaction rolled back due to: {exc_val}")
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}", exc_info=True)
            self.session.rollback()
            raise
        finally:
            if self.owns_session:
                self.session.close()


# ============================================
# HEALTH CHECK
# ============================================

def check_database_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        with get_db_context() as db:
            # Execute simple query
            db.execute("SELECT 1")
        logger.info("Database connection healthy")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False


def get_database_info() -> dict:
    """
    Get database connection information.

    Returns:
        Dictionary with database info
    """
    try:
        with get_db_context() as db:
            result = db.execute("SELECT version()").scalar()
            return {
                "connected": True,
                "version": result,
                "pool_size": engine.pool.size(),
                "checked_out_connections": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}", exc_info=True)
        return {
            "connected": False,
            "error": str(e)
        }


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_database():
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    """
    from .models import Base

    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def drop_database():
    """
    Drop all database tables.

    WARNING: This will delete all data!
    """
    from .models import Base

    if settings.is_production:
        raise RuntimeError("Cannot drop database in production environment!")

    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database: {e}", exc_info=True)
        raise


def reset_database():
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data!
    """
    if settings.is_production:
        raise RuntimeError("Cannot reset database in production environment!")

    logger.warning("Resetting database...")
    drop_database()
    init_database()
    logger.info("Database reset complete")


# ============================================
# QUERY HELPERS
# ============================================

def get_or_create(session: Session, model, defaults=None, **kwargs):
    """
    Get an existing record or create a new one.

    Args:
        session: Database session
        model: SQLAlchemy model class
        defaults: Default values for creation
        **kwargs: Filter criteria

    Returns:
        Tuple of (instance, created)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = kwargs.copy()
        if defaults:
            params.update(defaults)
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def bulk_insert(session: Session, model, data: list[dict], batch_size: int = 1000):
    """
    Bulk insert records efficiently.

    Args:
        session: Database session
        model: SQLAlchemy model class
        data: List of dictionaries with record data
        batch_size: Number of records per batch

    Returns:
        Number of records inserted
    """
    total_inserted = 0

    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            session.bulk_insert_mappings(model, batch)
            total_inserted += len(batch)
            logger.debug(f"Inserted batch of {len(batch)} records")

        session.flush()
        logger.info(f"Bulk insert complete: {total_inserted} records")
        return total_inserted

    except Exception as e:
        logger.error(f"Bulk insert failed: {e}", exc_info=True)
        raise


def bulk_update(session: Session, model, data: list[dict], batch_size: int = 1000):
    """
    Bulk update records efficiently.

    Args:
        session: Database session
        model: SQLAlchemy model class
        data: List of dictionaries with record data (must include primary key)
        batch_size: Number of records per batch

    Returns:
        Number of records updated
    """
    total_updated = 0

    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            session.bulk_update_mappings(model, batch)
            total_updated += len(batch)
            logger.debug(f"Updated batch of {len(batch)} records")

        session.flush()
        logger.info(f"Bulk update complete: {total_updated} records")
        return total_updated

    except Exception as e:
        logger.error(f"Bulk update failed: {e}", exc_info=True)
        raise


# ============================================
# CLEANUP
# ============================================

def close_database_connections():
    """
    Close all database connections.

    Should be called on application shutdown.
    """
    try:
        logger.info("Closing database connections...")
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}", exc_info=True)


# ============================================
# EXPORTS
# ============================================

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_context",
    "DatabaseTransaction",
    "check_database_connection",
    "get_database_info",
    "init_database",
    "drop_database",
    "reset_database",
    "get_or_create",
    "bulk_insert",
    "bulk_update",
    "close_database_connections",
]

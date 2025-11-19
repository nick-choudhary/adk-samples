"""
Backend package for Outbound Automation System.

This package provides the FastAPI backend for managing outbound campaigns,
lead extraction, multi-channel outreach, and analytics.

Modules:
    - config: Application configuration and settings
    - models: SQLAlchemy database models
    - schemas: Pydantic validation schemas
    - database: Database connection and session management
    - auth: Authentication and authorization
    - jobs: Cloud Tasks job management
    - main: FastAPI application and API endpoints
"""

from .config import settings, validate_configuration
from . import models, schemas, database, auth, jobs


# Package version
__version__ = "1.0.0"


# Package metadata
__title__ = "Outbound Automation System Backend"
__description__ = "Complete automated outbound system with Email, SMS, and Voice calls using Google ADK"
__author__ = "Your Name"
__license__ = "Apache-2.0"


# Export commonly used items
__all__ = [
    # Config
    "settings",
    "validate_configuration",
    # Modules
    "models",
    "schemas",
    "database",
    "auth",
    "jobs",
    # Metadata
    "__version__",
]


# ============================================
# INITIALIZATION
# ============================================

def init_backend():
    """
    Initialize backend components.

    This function should be called on application startup to:
    - Validate configuration
    - Initialize database
    - Initialize Firebase (if configured)
    - Set up logging
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_configuration()
        logger.info(f"Configuration validated for environment: {settings.ENVIRONMENT}")

        # Initialize Firebase if configured
        if settings.FIREBASE_PROJECT_ID:
            logger.info("Initializing Firebase...")
            auth.init_firebase()

        # Log service availability
        services = settings.validate_required_services()
        logger.info(f"Service availability: {services}")

        logger.info("Backend initialization complete")

    except Exception as e:
        logger.error(f"Backend initialization failed: {e}", exc_info=True)
        raise


def cleanup_backend():
    """
    Cleanup backend components.

    This function should be called on application shutdown to:
    - Close database connections
    - Clean up resources
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Cleaning up backend...")

        # Close database connections
        database.close_database_connections()

        logger.info("Backend cleanup complete")

    except Exception as e:
        logger.error(f"Backend cleanup error: {e}", exc_info=True)

#!/usr/bin/env python3
"""
Database initialization script for Outbound Automation System.

This script:
1. Creates database tables
2. Sets up indexes
3. Inserts sample data
4. Validates the schema

Usage:
    python scripts/init_database.py [--drop-existing] [--sample-data]

Options:
    --drop-existing  Drop all existing tables before creating new ones (DANGER!)
    --sample-data    Insert sample campaigns and leads for testing
    --validate-only  Only validate the database connection without making changes
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        # Construct from individual components
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'outbound_db')
        db_user = os.getenv('DB_USER', 'outbound_user')
        db_password = os.getenv('DB_PASSWORD', 'outbound_pass')

        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return database_url


def create_database_if_not_exists(database_url: str) -> None:
    """Create the database if it doesn't exist."""
    from urllib.parse import urlparse

    # Parse the database URL
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip('/')

    # Connect to postgres database to create our database
    postgres_url = database_url.replace(f'/{db_name}', '/postgres')

    try:
        # Connect to postgres database
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            logger.info(f"Creating database: {db_name}")
            cursor.execute(f'CREATE DATABASE {db_name}')
            logger.info(f"Database '{db_name}' created successfully")
        else:
            logger.info(f"Database '{db_name}' already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


def validate_connection(database_url: str) -> bool:
    """Validate database connection."""
    try:
        logger.info("Validating database connection...")
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version.split(',')[0]}")
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def drop_all_tables(database_url: str) -> None:
    """Drop all existing tables (USE WITH CAUTION!)."""
    logger.warning("Dropping all existing tables...")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables:
        logger.info("No tables to drop")
        return

    with engine.connect() as conn:
        # Drop all tables
        for table in tables:
            logger.info(f"Dropping table: {table}")
            conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
            conn.commit()

        # Drop all views
        conn.execute(text("DROP VIEW IF EXISTS campaign_performance CASCADE"))
        conn.commit()

    logger.info(f"Dropped {len(tables)} tables")
    engine.dispose()


def run_sql_file(database_url: str, sql_file: Path) -> None:
    """Execute SQL file."""
    logger.info(f"Running SQL file: {sql_file}")

    if not sql_file.exists():
        logger.error(f"SQL file not found: {sql_file}")
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    with open(sql_file, 'r') as f:
        sql_content = f.read()

    engine = create_engine(database_url)
    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            try:
                conn.execute(text(statement))
                conn.commit()
            except Exception as e:
                logger.error(f"Error executing statement {i}: {e}")
                logger.debug(f"Statement: {statement[:100]}...")
                raise

    logger.info(f"SQL file executed successfully: {sql_file}")
    engine.dispose()


def verify_tables(database_url: str) -> bool:
    """Verify that all required tables exist."""
    logger.info("Verifying database tables...")

    required_tables = [
        'campaigns',
        'leads',
        'interactions',
        'jobs',
        'do_not_contact',
        'email_templates',
        'sms_templates',
        'users',
        'audit_logs'
    ]

    engine = create_engine(database_url)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    missing_tables = [t for t in required_tables if t not in existing_tables]

    if missing_tables:
        logger.error(f"Missing tables: {', '.join(missing_tables)}")
        return False

    logger.info(f"All {len(required_tables)} required tables exist")

    # Verify views
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT viewname FROM pg_views WHERE schemaname = 'public'"
        ))
        views = [row[0] for row in result]

    if 'campaign_performance' in views:
        logger.info("View 'campaign_performance' exists")
    else:
        logger.warning("View 'campaign_performance' not found")

    engine.dispose()
    return True


def insert_sample_data(database_url: str) -> None:
    """Insert sample campaigns and leads for testing."""
    logger.info("Inserting sample data...")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Sample campaign
        sample_campaign = text("""
            INSERT INTO campaigns (name, status, config, stats)
            VALUES (
                'Sample Q1 2025 Campaign',
                'draft',
                '{"target_industries": ["Technology", "SaaS"], "target_titles": ["CEO", "CTO"], "company_size": "50-200", "geography": "United States", "sources": ["apollo"], "min_score": 70}'::jsonb,
                '{"total_leads": 0, "contacted": 0, "responded": 0, "converted": 0}'::jsonb
            )
            RETURNING id
        """)

        result = session.execute(sample_campaign)
        campaign_id = result.fetchone()[0]
        session.commit()

        logger.info(f"Sample campaign created with ID: {campaign_id}")

        # Sample leads
        sample_leads = text(f"""
            INSERT INTO leads (campaign_id, name, email, phone, title, company, company_size, industry, score, status, source)
            VALUES
                ('{campaign_id}', 'John Smith', 'john.smith@techcorp.com', '+1-555-0101', 'CEO', 'TechCorp Inc', '50-200', 'Technology', 85, 'new', 'apollo'),
                ('{campaign_id}', 'Sarah Johnson', 'sarah.j@innovatesoft.com', '+1-555-0102', 'CTO', 'InnovateSoft', '100-500', 'SaaS', 92, 'new', 'apollo'),
                ('{campaign_id}', 'Michael Chen', 'mchen@cloudservices.io', '+1-555-0103', 'VP Engineering', 'CloudServices.io', '200-1000', 'Cloud Computing', 78, 'new', 'linkedin'),
                ('{campaign_id}', 'Emily Davis', 'emily@dataanalytics.com', '+1-555-0104', 'CEO', 'DataAnalytics Pro', '20-50', 'Analytics', 88, 'new', 'apollo'),
                ('{campaign_id}', 'David Wilson', 'dwilson@aiventures.ai', '+1-555-0105', 'Founder', 'AI Ventures', '10-50', 'Artificial Intelligence', 95, 'new', 'linkedin')
        """)

        session.execute(sample_leads)
        session.commit()

        logger.info("Sample leads inserted (5 leads)")

        # Sample user
        sample_user = text("""
            INSERT INTO users (email, name, role)
            VALUES ('admin@example.com', 'Admin User', 'admin')
            ON CONFLICT (email) DO NOTHING
        """)

        session.execute(sample_user)
        session.commit()

        logger.info("Sample user created")

    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Initialize Outbound Automation System database"
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop all existing tables before creating new ones (DANGER!)'
    )
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Insert sample campaigns and leads for testing'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate the database connection without making changes'
    )

    args = parser.parse_args()

    try:
        # Get database URL
        database_url = get_database_url()
        logger.info(f"Database URL: {database_url.split('@')[1]}")  # Hide credentials

        # Validate connection
        if not validate_connection(database_url):
            logger.error("Database connection validation failed")
            sys.exit(1)

        if args.validate_only:
            logger.info("Validation complete. Exiting.")
            sys.exit(0)

        # Create database if it doesn't exist
        create_database_if_not_exists(database_url)

        # Drop existing tables if requested
        if args.drop_existing:
            confirm = input("⚠️  Are you sure you want to drop all existing tables? (yes/no): ")
            if confirm.lower() == 'yes':
                drop_all_tables(database_url)
            else:
                logger.info("Skipping table drop")

        # Run SQL initialization file
        sql_file = Path(__file__).parent.parent / 'database' / 'init.sql'
        run_sql_file(database_url, sql_file)

        # Verify tables were created
        if not verify_tables(database_url):
            logger.error("Table verification failed")
            sys.exit(1)

        # Insert sample data if requested
        if args.sample_data:
            insert_sample_data(database_url)

        logger.info("=" * 60)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 60)

        # Print summary
        logger.info("\nDatabase Summary:")
        logger.info("  - All tables created")
        logger.info("  - Indexes created")
        logger.info("  - Triggers configured")
        logger.info("  - Views created")
        logger.info("  - Sample templates inserted")

        if args.sample_data:
            logger.info("  - Sample data inserted")

        logger.info("\nNext steps:")
        logger.info("  1. Start the backend: docker-compose up")
        logger.info("  2. Access API docs: http://localhost:8080/docs")
        logger.info("  3. Access frontend: http://localhost:3000")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

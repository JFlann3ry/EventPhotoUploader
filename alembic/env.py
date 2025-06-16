# Import necessary modules for Alembic migrations
from logging.config import fileConfig  # Configure logging from a file
from sqlalchemy import engine_from_config  # Create a SQLAlchemy engine from config
from sqlalchemy import pool  # Manage database connection pooling
from alembic import context  # Alembic context for migrations

# Import your models here (adjust the import path to your project structure)
from sqlmodel import SQLModel  # SQLModel for defining database models

# ─── Alembic Configuration ──────────────────────────────────────────────────

# This is the Alembic Config object, which provides access to the values
# within the `alembic.ini` file in use.
config = context.config

# Interpret the config file for Python logging.
# This sets up loggers based on the configuration in `alembic.ini`.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set `target_metadata` to the metadata of your models.
# This is used by Alembic to detect changes in your database schema.
target_metadata = SQLModel.metadata

# ─── Additional Configuration (Optional) ────────────────────────────────────
# You can retrieve additional options from the Alembic config file if needed.
# Example:
# my_important_option = config.get_main_option("my_important_option")

# ─── Offline Migrations ─────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    In this mode, Alembic generates SQL scripts without connecting to the database.
    """
    # Retrieve the database URL from the Alembic configuration
    url = config.get_main_option("sqlalchemy.url")

    # Configure the Alembic context for offline mode
    context.configure(
        url=url,  # Database URL
        target_metadata=target_metadata,  # Metadata of your models
        literal_binds=True,  # Use literal values in the generated SQL
        dialect_opts={"paramstyle": "named"},  # Use named parameters in SQL
    )

    # Begin a new transaction and run migrations
    with context.begin_transaction():
        context.run_migrations()

# ─── Online Migrations ──────────────────────────────────────────────────────

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    In this mode, Alembic connects to the database and applies migrations directly.
    """
    # Create a database engine using the configuration from `alembic.ini`
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),  # Retrieve config section
        prefix="sqlalchemy.",  # Prefix for SQLAlchemy-related settings
        poolclass=pool.NullPool,  # Use a NullPool (no connection pooling)
    )

    # Connect to the database and configure the Alembic context
    with connectable.connect() as connection:
        context.configure(
            connection=connection,  # Database connection
            target_metadata=target_metadata,  # Metadata of your models
        )

        # Begin a new transaction and run migrations
        with context.begin_transaction():
            context.run_migrations()

# ─── Entry Point ────────────────────────────────────────────────────────────

# Determine whether to run migrations in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

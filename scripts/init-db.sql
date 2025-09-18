-- Database initialization script for FastAPI Clean Project
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create test database for running tests
CREATE DATABASE fastapi_db_test OWNER fastapi_user;

-- Connect to test database and set it up
\c fastapi_db_test;

-- Create extensions in test database too
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Grant all privileges to user on test database
GRANT ALL PRIVILEGES ON DATABASE fastapi_db_test TO fastapi_user;
GRANT ALL ON SCHEMA public TO fastapi_user;

-- Switch back to main database
\c fastapi_db;

-- Set timezone for main database
SET timezone = 'UTC';

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed at %', now();
    RAISE NOTICE 'Created main database: fastapi_db';
    RAISE NOTICE 'Created test database: fastapi_db_test';
END $$;

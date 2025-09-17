-- Database initialization script for FastAPI Clean Project
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user if not exists (optional, already handled by Docker)
-- The main database and user are created by the POSTGRES_* environment variables

-- You can add additional database setup here, such as:
-- Additional schemas
-- Custom functions
-- Initial data
-- Indexes

-- Example: Create a custom schema for application data
-- CREATE SCHEMA IF NOT EXISTS app_data;

-- Set timezone
SET timezone = 'UTC';

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed at %', now();
END $$;

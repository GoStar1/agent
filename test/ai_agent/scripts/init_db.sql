-- Database initialization script
-- This runs automatically when PostgreSQL container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for full-text search (optional, for better keyword search performance)
-- These will be created after tables are created by SQLAlchemy

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;

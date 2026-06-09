
-- Initialize database with required roles and permissions
-- Use IF NOT EXISTS pattern to avoid errors on re-initialization

-- Create or update ujops role
DO $$
BEGIN
  CREATE ROLE ujops WITH LOGIN CREATEDB;
  ALTER ROLE ujops WITH PASSWORD '<your_secure_password>';
EXCEPTION WHEN duplicate_object THEN
  -- Role already exists, just update password
  ALTER ROLE ujops WITH PASSWORD '<your_secure_password>';
END
$$;

-- Grant permissions to jobanalyzer_user
GRANT ALL PRIVILEGES ON DATABASE jobanalyzer TO ujops;

-- Create schemas (IF NOT EXISTS already handles duplicates)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Grant schema permissions
GRANT USAGE, CREATE ON SCHEMA raw TO ujops;
GRANT USAGE, CREATE ON SCHEMA staging TO ujops;
GRANT USAGE, CREATE ON SCHEMA warehouse TO ujops;
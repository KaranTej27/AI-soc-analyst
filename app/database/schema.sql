-- Protocol: PostgreSQL
-- Database: "AI SOC Analyst Credentials"

-- 1. Create the credentials table
CREATE TABLE IF NOT EXISTS ai_soc_analyst_credentials (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create the function to update the 'updated_at' column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 3. Create the trigger to execute the function before any update
DROP TRIGGER IF EXISTS update_ai_soc_user_modtime ON ai_soc_analyst_credentials;
CREATE TRIGGER update_ai_soc_user_modtime
BEFORE UPDATE ON ai_soc_analyst_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

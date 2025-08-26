-- Optional: Telegram Users Table Schema
-- This table provides dedicated storage for Telegram user information
-- You can use this instead of storing everything in the leads table

CREATE TABLE IF NOT EXISTS telegram_users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    is_bot BOOLEAN DEFAULT FALSE,
    last_activity TIMESTAMP WITH TIME ZONE,
    total_messages INTEGER DEFAULT 0,
    session_id VARCHAR(255),
    lead_id UUID REFERENCES leads(id),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_telegram_users_telegram_id ON telegram_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_username ON telegram_users(username);
CREATE INDEX IF NOT EXISTS idx_telegram_users_lead_id ON telegram_users(lead_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_session_id ON telegram_users(session_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_telegram_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_telegram_users_updated_at
    BEFORE UPDATE ON telegram_users
    FOR EACH ROW
    EXECUTE FUNCTION update_telegram_users_updated_at();

-- Add preferences column to leads table if it doesn't exist
-- This allows storing user preferences in the leads table
ALTER TABLE leads ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';

-- Index for preferences in leads table
CREATE INDEX IF NOT EXISTS idx_leads_preferences ON leads USING GIN (preferences);

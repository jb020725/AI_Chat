-- Sessions Table Schema for Supabase
-- This table stores ONLY Telegram user session data for persistence across server restarts
-- Website sessions are temporary and not stored in database

CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL DEFAULT 'telegram',  -- 'telegram' or 'website' (though only telegram should be stored)
    email TEXT,
    phone TEXT,
    name TEXT,
    country TEXT,
    intake TEXT,
    program_level TEXT,
    field_of_study TEXT,
    conversation_summary TEXT,
    progress_state TEXT DEFAULT 'conversation_active',
    exchange_count INTEGER DEFAULT 0,
    completed_steps JSONB DEFAULT '[]',
    next_actions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on session_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);

-- Create index on platform for filtering
CREATE INDEX IF NOT EXISTS idx_sessions_platform ON sessions(platform);

-- Create index on email for user tracking
CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(email);

-- Create index on last_updated for cleanup operations
CREATE INDEX IF NOT EXISTS idx_sessions_last_updated ON sessions(last_updated);

-- Enable Row Level Security (RLS)
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Create policy for service role access (for backend operations)
CREATE POLICY "Service role can access all sessions" ON sessions
    FOR ALL USING (auth.role() = 'service_role');

-- Create policy for authenticated users to see their own sessions
CREATE POLICY "Users can view their own sessions" ON sessions
    FOR SELECT USING (auth.email() = email);

-- Create function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_sessions_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update last_updated
CREATE TRIGGER trigger_update_sessions_last_updated
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_sessions_last_updated();

-- Insert sample Telegram session data for testing (optional)
-- INSERT INTO sessions (session_id, platform, email, name, country, intake) 
-- VALUES ('telegram_123456789', 'telegram', 'test@example.com', 'Test User', 'USA', 'Fall 2025');

-- Grant permissions to service role
GRANT ALL ON sessions TO service_role;
GRANT USAGE ON SEQUENCE sessions_id_seq TO service_role;

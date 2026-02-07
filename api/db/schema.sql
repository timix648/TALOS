
-- Run this in your Supabase SQL Editor to set up the database.
-- https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_installation_id BIGINT UNIQUE NOT NULL,
    account_login TEXT NOT NULL,
    account_type TEXT DEFAULT 'User' CHECK (account_type IN ('User', 'Organization')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_installations_github_id 
    ON installations(github_installation_id);



CREATE TABLE IF NOT EXISTS watched_repos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID REFERENCES installations(id) ON DELETE CASCADE,
    repo_full_name TEXT NOT NULL,
    auto_heal_enabled BOOLEAN DEFAULT TRUE,
    safe_mode BOOLEAN DEFAULT TRUE,  
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    
    UNIQUE(installation_id, repo_full_name)
);

CREATE INDEX IF NOT EXISTS idx_watched_repos_installation 
    ON watched_repos(installation_id);
CREATE INDEX IF NOT EXISTS idx_watched_repos_enabled 
    ON watched_repos(auto_heal_enabled) WHERE auto_heal_enabled = TRUE;



CREATE TABLE IF NOT EXISTS healing_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT UNIQUE NOT NULL,  -- Short ID like "a1b2c3d4"
    installation_id UUID REFERENCES installations(id) ON DELETE SET NULL,
    repo_full_name TEXT NOT NULL,
    
    
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'success', 'failure', 'cancelled')),
    
   
    error_type TEXT,  
    error_message TEXT,
    patient_zero TEXT,  
    crash_site TEXT,   
    
   
    pr_url TEXT,
    pr_number INTEGER,
    branch_name TEXT,
    
  
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
  
    metadata JSONB DEFAULT '{}'::jsonb
);


CREATE INDEX IF NOT EXISTS idx_runs_status ON healing_runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_repo ON healing_runs(repo_full_name);
CREATE INDEX IF NOT EXISTS idx_runs_started ON healing_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_run_id ON healing_runs(run_id);


CREATE TABLE IF NOT EXISTS healing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT REFERENCES healing_runs(run_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_run_id ON healing_events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON healing_events(event_type);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';


DROP TRIGGER IF EXISTS update_installations_updated_at ON installations;
CREATE TRIGGER update_installations_updated_at
    BEFORE UPDATE ON installations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


DROP TRIGGER IF EXISTS update_watched_repos_updated_at ON watched_repos;
CREATE TRIGGER update_watched_repos_updated_at
    BEFORE UPDATE ON watched_repos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Enable if you want to use Supabase auth on the frontend

-- ALTER TABLE installations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE watched_repos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE healing_runs ENABLE ROW LEVEL SECURITY;

-- Uncomment to insert test data

-- INSERT INTO installations (github_installation_id, account_login, account_type)
-- VALUES (12345678, 'test-user', 'User');


-- Run this to verify all tables were created:

SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('installations', 'watched_repos', 'healing_runs', 'healing_events')
ORDER BY table_name;

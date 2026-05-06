-- Migration 007-009: Phase 5 Foundations

-- 1. Public Shared Reports
CREATE TABLE IF NOT EXISTS shared_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    company_name TEXT,
    config JSONB DEFAULT '{}',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE shared_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their shared reports" ON shared_reports FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Anyone with token can view shared report" ON shared_reports FOR SELECT USING (true);

-- 2. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    resource_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can see their own audit logs" ON audit_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role full access on audit_logs" ON audit_logs FOR ALL TO service_role USING (true);

-- 3. Vector Support (Optional Extension)
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS embedding vector(1536);

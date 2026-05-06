-- Migration 004: Aspects Table

CREATE TABLE IF NOT EXISTS aspects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid(),
    company_name TEXT,
    aspect TEXT NOT NULL,
    score FLOAT NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE aspects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only see their own aspects" ON aspects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own aspects" ON aspects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service role full access on aspects" ON aspects FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_aspects_company ON aspects (company_name);
CREATE INDEX IF NOT EXISTS idx_aspects_user ON aspects (user_id);

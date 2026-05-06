-- Migration 001: Initial Schema

-- 1. Enable pgcrypto for UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    original_text TEXT NOT NULL,
    clean_text TEXT,
    sentiment TEXT,
    rating FLOAT,
    date TIMESTAMPTZ,
    source TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    keyword TEXT NOT NULL,
    pressure_score FLOAT NOT NULL,
    status TEXT DEFAULT 'EMERGING',
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Watchlist Table
CREATE TABLE IF NOT EXISTS watchlist (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    company_name TEXT,
    last_scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Enable RLS
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;

-- Initial open policies (Phase 1)
CREATE POLICY "Allow anonymous read access on reviews" ON reviews FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anonymous read access on alerts" ON alerts FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anonymous read access on watchlist" ON watchlist FOR SELECT TO anon USING (true);

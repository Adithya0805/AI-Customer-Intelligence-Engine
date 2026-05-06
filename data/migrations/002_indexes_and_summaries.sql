-- Migration 002: Indexes, Summaries, and Deduplication

-- 1. Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews (date DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews (sentiment);
CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews (source);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC);

-- 2. Create Summaries Table
CREATE TABLE IF NOT EXISTS summaries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content TEXT NOT NULL,
    source_context TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Add Deduplication Constraint to reviews
-- We wrap in DO block to avoid failure if constraint exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_review_per_source') THEN
        ALTER TABLE reviews ADD CONSTRAINT unique_review_per_source UNIQUE (clean_text, source);
    END IF;
END $$;

-- 4. Tighten RLS
-- Drop old Phase 1 policies before creating new ones
DROP POLICY IF EXISTS "Allow anonymous read access on reviews" ON reviews;
CREATE POLICY "Allow anonymous read access on reviews" ON reviews FOR SELECT TO anon USING (true);
CREATE POLICY "Service role full access on reviews" ON reviews FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anonymous read access on alerts" ON alerts;
CREATE POLICY "Allow anonymous read access on alerts" ON alerts FOR SELECT TO anon USING (true);
CREATE POLICY "Service role full access on alerts" ON alerts FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anonymous read access on watchlist" ON watchlist;
CREATE POLICY "Allow anonymous read access on watchlist" ON watchlist FOR SELECT TO anon USING (true);
CREATE POLICY "Service role full access on watchlist" ON watchlist FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Summaries RLS
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read access on summaries" ON summaries FOR SELECT TO anon USING (true);
CREATE POLICY "Service role full access on summaries" ON summaries FOR ALL TO service_role USING (true) WITH CHECK (true);

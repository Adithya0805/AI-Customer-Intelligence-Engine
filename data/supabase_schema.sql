-- Create the reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    original_text TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    rating FLOAT,
    normalized_rating FLOAT,
    date TIMESTAMPTZ,
    source TEXT,
    url TEXT,
    sentiment TEXT,
    sentiment_score FLOAT,
    topic_cluster TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    keyword TEXT NOT NULL,
    status TEXT NOT NULL,
    pressure_score FLOAT,
    recent_importance FLOAT,
    baseline_importance FLOAT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Turn on Row Level Security (RLS) but allow anonymous access for this local app to read/write for now
-- Since this is an internal tool, we will just allow all operations
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous all access on reviews"
ON reviews FOR ALL TO anon
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow anonymous all access on alerts"
ON alerts FOR ALL TO anon
USING (true)
WITH CHECK (true);

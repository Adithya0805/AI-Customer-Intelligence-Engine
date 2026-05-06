-- Migration 003: Multi-Tenancy and User Scoping

-- 1. Add user_id column to existing tables
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE summaries ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();

-- 2. Update RLS policies to scope data by user_id
-- We drop old policies first

-- Reviews
DROP POLICY IF EXISTS "Allow anonymous read access on reviews" ON reviews;
DROP POLICY IF EXISTS "Service role full access on reviews" ON reviews;
CREATE POLICY "Users can only see their own reviews" ON reviews FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own reviews" ON reviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service role full access on reviews" ON reviews FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Alerts
DROP POLICY IF EXISTS "Allow anonymous read access on alerts" ON alerts;
DROP POLICY IF EXISTS "Service role full access on alerts" ON alerts;
CREATE POLICY "Users can only see their own alerts" ON alerts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own alerts" ON alerts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service role full access on alerts" ON alerts FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Summaries
DROP POLICY IF EXISTS "Allow anonymous read access on summaries" ON summaries;
DROP POLICY IF EXISTS "Service role full access on summaries" ON summaries;
CREATE POLICY "Users can only see their own summaries" ON summaries FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own summaries" ON summaries FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service role full access on summaries" ON summaries FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Watchlist
DROP POLICY IF EXISTS "Allow anonymous read access on watchlist" ON watchlist;
DROP POLICY IF EXISTS "Service role full access on watchlist" ON watchlist;
CREATE POLICY "Users can only see their own watchlist" ON watchlist FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own watchlist" ON watchlist FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own watchlist" ON watchlist FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own watchlist" ON watchlist FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Service role full access on watchlist" ON watchlist FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 3. Create Profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT,
    display_name TEXT,
    org_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can see their own profile" ON profiles;
CREATE POLICY "Users can see their own profile" ON profiles FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (new.id, new.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists to avoid errors on rerun
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

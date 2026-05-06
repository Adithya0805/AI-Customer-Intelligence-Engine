-- Migration 005: API Keys and Webhooks

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own API keys" ON api_keys FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Service role full access on api_keys" ON api_keys FOR ALL TO service_role USING (true);

CREATE TABLE IF NOT EXISTS webhooks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    url TEXT NOT NULL,
    events TEXT[] DEFAULT '{alert,new_review}',
    secret TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own webhooks" ON webhooks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Service role full access on webhooks" ON webhooks FOR ALL TO service_role USING (true);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    webhook_id UUID REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    response_code INTEGER,
    delivered_at TIMESTAMPTZ DEFAULT NOW(),
    attempts INTEGER DEFAULT 1
);

ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can see deliveries for their webhooks" ON webhook_deliveries 
    FOR SELECT USING (EXISTS (SELECT 1 FROM webhooks WHERE webhooks.id = webhook_id AND webhooks.user_id = auth.uid()));
CREATE POLICY "Service role full access on webhook_deliveries" ON webhook_deliveries FOR ALL TO service_role USING (true);

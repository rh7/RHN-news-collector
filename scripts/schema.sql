-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sources configuration table
CREATE TABLE IF NOT EXISTS sources (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  type VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  enabled BOOLEAN DEFAULT true,
  config JSONB DEFAULT '{}',
  last_sync TIMESTAMP,
  last_sync_status VARCHAR(50),
  sync_metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Main content storage
CREATE TABLE IF NOT EXISTS contents (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  external_id VARCHAR(255) NOT NULL,
  title TEXT,
  url TEXT,
  content TEXT,
  author TEXT,
  published_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  UNIQUE(source_id, external_id)
);

-- Track delivered content (used by intelligence service)
CREATE TABLE IF NOT EXISTS delivered_content (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  content_id UUID REFERENCES contents(id) ON DELETE CASCADE,
  delivered_at TIMESTAMP DEFAULT NOW(),
  delivery_channel VARCHAR(50),
  digest_type VARCHAR(50),
  user_feedback INT,
  metadata JSONB DEFAULT '{}'
);

-- User preferences (used by intelligence service)
CREATE TABLE IF NOT EXISTS preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  preference_type VARCHAR(50),
  value JSONB NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contents_collected_at ON contents(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_published_at ON contents(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_source_id ON contents(source_id);
CREATE INDEX IF NOT EXISTS idx_delivered_content_delivered_at ON delivered_content(delivered_at DESC);

-- updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_sources_updated_at ON sources;
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



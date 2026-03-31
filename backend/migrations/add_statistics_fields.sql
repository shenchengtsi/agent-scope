-- Migration: Add statistics fields to traces table
-- Run this if your database was created before v0.5.1

ALTER TABLE traces ADD COLUMN total_tokens INTEGER DEFAULT 0;
ALTER TABLE traces ADD COLUMN total_latency_ms REAL DEFAULT 0.0;
ALTER TABLE traces ADD COLUMN cost_estimate REAL DEFAULT 0.0;
ALTER TABLE traces ADD COLUMN llm_call_count INTEGER DEFAULT 0;
ALTER TABLE traces ADD COLUMN tool_call_count INTEGER DEFAULT 0;

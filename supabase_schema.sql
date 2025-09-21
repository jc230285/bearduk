-- Supabase PostgreSQL Schema for BEARDUK Website
-- Run this script in your Supabase SQL editor to create the tables

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    location TEXT,
    facebook_url TEXT,
    is_upcoming BOOLEAN DEFAULT true,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    going_count INTEGER DEFAULT 0,
    interested_count INTEGER DEFAULT 0,
    friends_going TEXT DEFAULT ''
);

-- Create social_media_followers table  
CREATE TABLE IF NOT EXISTS social_media_followers (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    username TEXT NOT NULL,
    follower_count INTEGER NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_upcoming ON events(is_upcoming, date);
CREATE INDEX IF NOT EXISTS idx_events_scraped_at ON events(scraped_at);
CREATE INDEX IF NOT EXISTS idx_social_followers_platform ON social_media_followers(platform, username);
CREATE INDEX IF NOT EXISTS idx_social_followers_scraped_at ON social_media_followers(scraped_at);

-- Add unique constraint for social media followers (per platform/username/time)
ALTER TABLE social_media_followers 
ADD CONSTRAINT unique_platform_username_time 
UNIQUE (platform, username, date_trunc('day', scraped_at));
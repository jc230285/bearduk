#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to database
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
c = conn.cursor()

# First check what tables exist
print("=== Available Tables ===")
c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = c.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\n=== Looking for events-related tables ===")
c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%event%'")
event_tables = c.fetchall()
for table in event_tables:
    print(f"- {table[0]}")

print("\n=== Looking for beard-related tables ===")
c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%beard%'")
beard_tables = c.fetchall()
for table in beard_tables:
    print(f"- {table[0]}")

# Check if the 'events' table exists and show its structure
print("\n=== Checking 'events' table structure ===")
try:
    c.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'events'
        ORDER BY ordinal_position
    """)
    columns = c.fetchall()
    if columns:
        print("Events table columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
    else:
        print("No 'events' table found")
except Exception as e:
    print(f"Error checking events table: {e}")

# Check if the 'beard_events' table exists and show its structure
print("\n=== Checking 'beard_events' table structure ===")
try:
    c.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'beard_events'
        ORDER BY ordinal_position
    """)
    columns = c.fetchall()
    if columns:
        print("beard_events table columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        # Also get a sample of data
        print("\n=== Sample data from beard_events ===")
        c.execute("SELECT * FROM beard_events LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f"  {row}")
    else:
        print("No 'beard_events' table found")
except Exception as e:
    print(f"Error checking beard_events table: {e}")

conn.close()
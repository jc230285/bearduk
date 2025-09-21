#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Connect to database
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
c = conn.cursor()

print("=== BEARD_EVENTS TABLE STRUCTURE ===")
print()

# Get detailed column information
c.execute("""
    SELECT 
        column_name, 
        data_type, 
        character_maximum_length,
        is_nullable, 
        column_default 
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'beard_events'
    ORDER BY ordinal_position
""")

columns = c.fetchall()

print("Column Details:")
print("-" * 80)
for col in columns:
    name, data_type, max_length, nullable, default = col
    length_info = f" ({max_length})" if max_length else ""
    print(f"{name:15} | {data_type}{length_info:15} | Nullable: {nullable:3} | Default: {default}")

print()
print("=== SAMPLE DATA FROM BEARD_EVENTS ===")
print()

# Get all data with formatted output
c.execute("SELECT * FROM beard_events ORDER BY timestamp DESC")
rows = c.fetchall()

if rows:
    print(f"Found {len(rows)} events in beard_events table:")
    print()
    
    for i, row in enumerate(rows, 1):
        print(f"Event {i}:")
        print(f"  ID: {row[0]}")
        print(f"  Created: {row[1]}")
        print(f"  URL: {row[2]}")
        print(f"  Timestamp: {row[3]}")
        print(f"  Name: {row[4]}")
        print(f"  Responded: {row[5]}")
        print(f"  Location: {row[6]}")
        print(f"  Venue URL: {row[7]}")
        print(f"  Duration: {row[8]}")
        print(f"  Image URL: {row[9]}")
        print(f"  Updated: {row[10]}")
        print("-" * 60)
else:
    print("No data found in beard_events table")

print()
print("=== COMPARISON WITH EVENTS TABLE ===")
print()

# Also check what's in the events table
c.execute("SELECT COUNT(*) FROM events")
events_count = c.fetchone()[0]
print(f"Events table has {events_count} records")

c.execute("SELECT COUNT(*) FROM beard_events")
beard_events_count = c.fetchone()[0]
print(f"beard_events table has {beard_events_count} records")

conn.close()
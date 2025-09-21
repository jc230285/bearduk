-- Data migration for BEARDUK Website - Run this after creating the schema

-- Insert events data
INSERT INTO events (title, date, location, facebook_url, is_upcoming, scraped_at, going_count, interested_count, friends_going) VALUES
('BEARD @ The Vaults', 'Fri, 28 Nov at 21:00', 'The Vaults, Southsea', 'https://www.facebook.com/events/1365306694514142/', true, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins'),
('BEARD @ Steamtown', 'Fri, 19 Dec at 20:00', 'Steam Town Brew Co, Eastleigh', 'https://www.facebook.com/events/1276300143600709/', true, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins'),
('BEARD @ The Anglers', 'Sun, 21 Dec at 16:00', 'Event by BEARD', 'https://www.facebook.com/events/955296663193145/', true, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins'),
('Private Party', 'Tomorrow at 19:00', 'Event by BEARD', 'https://www.facebook.com/bearduk/events', true, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins'),
('BEARD @ Local Pub', 'September 10, 2025', 'Southampton', 'https://www.facebook.com/bearduk/events', false, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins'),
('BEARD @ Brewery Event', 'August 25, 2025', 'Portsmouth', 'https://www.facebook.com/bearduk/events', false, '2025-09-19 19:41:21', 1, 6, 'Heather Ingleby, Jane Collins-Glass, Karl Collins');

-- Insert social media followers data
INSERT INTO social_media_followers (platform, username, follower_count, scraped_at) VALUES
('facebook', 'bearduk', 478, '2025-09-21 04:49:26'),
('instagram', 'beardbanduk', 351, '2025-09-21 04:41:35');
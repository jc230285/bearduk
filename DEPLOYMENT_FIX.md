# Coolify Deployment Fix

## Issue Identified
Port 5000 is already allocated by a previous container that wasn't properly stopped.

## Quick Fix Steps

### 1. Stop All Running Containers
In your Coolify dashboard, go to:
- **bearduk** project
- **Terminal** tab
- Run these commands to stop any running containers:

```bash
docker ps | grep bearduk
docker stop $(docker ps -q --filter name=jc4osc8w4sg0okww0c840wok)
docker rm $(docker ps -aq --filter name=jc4osc8w4sg0okww0c840wok)
```

### 2. Fix Port Configuration
In Coolify **General** settings:

**Current (Wrong):**
- Ports Exposes: `5005`
- Ports Mappings: `5005:5000`

**Should be:**
- Ports Exposes: `5000`
- Ports Mappings: `5000:5000`

**OR use different external port:**
- Ports Exposes: `5000`  
- Ports Mappings: `5005:5000`

### 3. Remove Unnecessary Docker Options
The custom Docker options seem excessive. Try removing this:
```
--cap-add SYS_ADMIN --device=/dev/fuse --security-opt apparmor:unconfined --ulimit nofile=1024:1024 --tmpfs /run:rw,noexec,nosuid,size=65536k --hostname=myapp
```

Replace with just what we need for Chrome:
```
--no-sandbox --disable-setuid-sandbox
```

### 4. Remove Pre/Post Deployment Commands
These PHP commands aren't needed for your Flask app:
- Remove: `php artisan migrate`

## Test Endpoints After Successful Deployment

Once deployed successfully, test these URLs:

1. **Main site**: https://bearduk.com
2. **Live scraping test**: https://bearduk.com/test_scraping
3. **System status**: https://bearduk.com/debug_status
4. **Events API**: https://bearduk.com/events_json

## Alternative: Use Different Port Mapping

If port 5000 conflicts persist, you can:
1. Set Ports Mappings to: `8080:5000`
2. Access via: https://bearduk.com:8080

But the main issue is cleaning up the old containers first.
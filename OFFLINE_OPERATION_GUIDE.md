# 1BIP System - Offline Operation Guide

This guide confirms that the 1BIP Face Recognition & Attendance System operates **completely offline** without requiring internet connectivity.

---

## ✅ Offline Operation Confirmed

The 1BIP system is designed to run on **your own server** without any internet connection. All components communicate via internal Docker network.

---

## System Architecture (Offline)

```
┌─────────────────────────────────────────────────────────────┐
│  1BIP SERVER (No Internet Required)                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CompreFace   │  │   Camera     │  │  Dashboard   │      │
│  │   Services   │←→│   Service    │←→│   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↕                  ↕                  ↕              │
│  ┌──────────────────────────────────────────────────┐      │
│  │          PostgreSQL Database                      │      │
│  └──────────────────────────────────────────────────┘      │
│                         ↑                                     │
└─────────────────────────┼─────────────────────────────────┘
                          │
                   Local Network Only
                          │
                ┌─────────┴─────────┐
                │                   │
         Hikvision Cameras    Admin/User PCs
              (RTSP)          (Web Browser)
```

---

## Components Analysis

### 1. CompreFace Services ✅ Offline

**Location:** Internal Docker Network

**Communication:**
- `compreface-admin` → `compreface-postgres-db` (Internal)
- `compreface-api` → `compreface-postgres-db` (Internal)
- `compreface-api` → `compreface-core` (Internal)
- `compreface-core` → ML Models (Local files)

**External Dependencies:** NONE

**Verification:**
```bash
# Check that no external URLs are called
docker-compose logs compreface-api | grep -i "http://" | grep -v "localhost\|compreface"
# Should return: No matches
```

---

### 2. Camera Service ✅ Offline

**Location:** Internal Docker Network

**Communication:**
- Camera RTSP Stream (Local Network: `rtsp://192.168.x.x`)
- CompreFace API (`http://compreface-api:8080`) - Internal
- PostgreSQL (`compreface-postgres-db:5432`) - Internal

**Optional Features (Can be Disabled):**
- Email Alerts: Disabled by default (`ENABLE_ALERTS=false`)
- Webhook Alerts: Disabled by default (URL empty)

**External Dependencies:** NONE (when alerts disabled)

**Configuration for Offline:**
```bash
# In camera-service/config/camera_config.env
ENABLE_ALERTS=false              # No external alerts
ALERT_WEBHOOK_URL=               # Empty (no webhook)
ALERT_EMAIL=                     # Empty (no email)
```

---

### 3. Dashboard Service ✅ Offline

**Location:** Internal Docker Network

**Communication:**
- PostgreSQL (`compreface-postgres-db:5432`) - Internal only

**Frontend Assets:**
- ✅ All CSS: Self-hosted (`/static/css/dashboard.css`)
- ✅ All JavaScript: Pure vanilla JS (`/static/js/dashboard.js`)
- ✅ No External CDNs
- ✅ No jQuery/React/Vue
- ✅ No Google Fonts
- ✅ No Analytics/Tracking

**External Dependencies:** NONE

**Verification:**
```bash
# Check HTML for external resources
grep -r "https://" dashboard-service/src/templates/
# Should return: No matches

grep -r "http://" dashboard-service/src/templates/ | grep -v "localhost"
# Should return: No matches
```

---

### 4. PostgreSQL Database ✅ Offline

**Location:** Internal Docker Network

**Communication:** Local only (port 5432, not exposed externally)

**External Dependencies:** NONE

---

### 5. Hikvision Cameras ✅ Offline

**Connection:** RTSP stream via local network

**Format:** `rtsp://admin:password@192.168.1.100:554/...`

**External Dependencies:** NONE (local network only)

---

## No Internet Required - Complete Checklist

### ✅ No External API Calls
- CompreFace uses local ML models
- No cloud services
- No external face recognition APIs

### ✅ No External Dependencies (CDN)
- No Bootstrap CDN
- No jQuery CDN
- No Google Fonts
- No Font Awesome CDN
- All resources self-hosted

### ✅ No Analytics or Tracking
- No Google Analytics
- No Facebook Pixel
- No third-party tracking

### ✅ No Email/SMS Services (Optional)
- Email alerts: DISABLED by default
- SMS alerts: Not implemented
- Can be enabled later if needed

### ✅ Docker Images
- All images: Pre-built or built locally
- No need to pull from internet after initial setup
- Can be saved and transferred offline

---

## Deployment in Air-Gapped Environment

### Step 1: Prepare Docker Images (On Internet-Connected Machine)

```bash
# Pull all required images
docker-compose pull

# Save images to tar files
docker save exadel/compreface-admin:1.2.0 | gzip > compreface-admin.tar.gz
docker save exadel/compreface-api:1.2.0 | gzip > compreface-api.tar.gz
docker save exadel/compreface-core:1.2.0 | gzip > compreface-core.tar.gz
docker save exadel/compreface-fe:1.2.0 | gzip > compreface-fe.tar.gz
docker save exadel/compreface-postgres-db:1.2.0 | gzip > compreface-postgres-db.tar.gz

# Build custom services
docker-compose build camera-service dashboard-service

# Save custom images
docker save 1bip-camera-service:latest | gzip > camera-service.tar.gz
docker save 1bip-dashboard:latest | gzip > dashboard-service.tar.gz
```

### Step 2: Transfer to Offline Server

```bash
# Copy all tar.gz files to offline server
# Also copy the entire project directory
```

### Step 3: Load Images on Offline Server

```bash
# Load all images
docker load < compreface-admin.tar.gz
docker load < compreface-api.tar.gz
docker load < compreface-core.tar.gz
docker load < compreface-fe.tar.gz
docker load < compreface-postgres-db.tar.gz
docker load < camera-service.tar.gz
docker load < dashboard-service.tar.gz
```

### Step 4: Start System Offline

```bash
# Start all services (no internet needed)
docker-compose up -d

# Verify all services are running
docker-compose ps
```

---

## Verifying Offline Operation

### Test 1: Disconnect Internet

```bash
# Disable network interface (optional, for testing)
sudo ifconfig eth0 down  # Linux
# or
sudo networksetup -setnetworkserviceenabled "Wi-Fi" off  # macOS
```

### Test 2: Access Dashboard

```
http://localhost:5000
```

**Expected:** Dashboard loads completely, no broken images/styles

### Test 3: Check Browser Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh dashboard page
4. **Expected:** All requests to `localhost` or `[server-ip]` only
5. **No requests to:** googleapis.com, cdnjs.com, unpkg.com, etc.

### Test 4: Test Face Recognition

1. Person walks in front of camera
2. **Expected:** Detection works
3. **Expected:** Logged to database
4. **Expected:** Appears in dashboard

### Test 5: Check Docker Logs

```bash
# Check for any internet connection attempts
docker-compose logs | grep -i "connection refused\|timeout\|unreachable"
# If offline, should show: No errors

# Check normal operations
docker-compose logs camera-service | tail -20
docker-compose logs dashboard-service | tail -20
```

---

## Network Requirements (Local Only)

### Required Network Configuration

```
1. Server IP: 192.168.1.10 (example)
2. Camera IPs: 192.168.1.100-110
3. Client PCs: 192.168.1.20-50

All on same subnet: 192.168.1.0/24
```

### Firewall Rules

```bash
# Allow internal network access only
sudo ufw default deny incoming
sudo ufw allow from 192.168.1.0/24 to any port 8000  # CompreFace UI
sudo ufw allow from 192.168.1.0/24 to any port 5000  # Dashboard
sudo ufw allow from 192.168.1.0/24 to any port 554   # RTSP (if needed)
sudo ufw enable

# Block all outgoing internet (optional, for strict air-gap)
sudo ufw default deny outgoing
sudo ufw allow out to 192.168.1.0/24
```

---

## Optional Features Requiring Internet

These features are **DISABLED by default** and **NOT required** for operation:

### 1. Email Alerts (Optional)

```bash
# To enable, edit camera-service/config/camera_config.env
ENABLE_ALERTS=true
email_host=smtp.yourinternalserver.com  # Use internal email server
```

**Recommendation:** Use internal SMTP server on local network

### 2. Software Updates (Optional)

```bash
# Updates can be done manually:
# 1. Download new images on internet-connected machine
# 2. Transfer to offline server
# 3. Load images
```

### 3. Webhook Alerts (Optional)

```bash
# Can use internal webhook service
ALERT_WEBHOOK_URL=http://192.168.1.50:8080/alerts  # Internal server
```

---

## Advantages of Offline Operation

### ✅ Security
- No data leaves your network
- No cloud storage of face images
- No third-party access
- Complete data sovereignty

### ✅ Privacy
- GDPR/Data protection compliant
- No external data processors
- All data stays on-premises

### ✅ Reliability
- No dependency on internet uptime
- Works during internet outages
- Faster response times (no network latency)

### ✅ Performance
- All processing local
- No bandwidth limitations
- Sub-second face recognition

### ✅ Cost
- No cloud subscription fees
- No API usage charges
- One-time hardware investment

---

## Offline Maintenance

### Regular Tasks (No Internet Needed)

1. **Database Backups**
   ```bash
   # Automated backup script (runs offline)
   docker-compose exec -T compreface-postgres-db pg_dump -U postgres frs_1bip > backup.sql
   ```

2. **Log Rotation**
   ```bash
   # Clean old logs
   find camera-service/logs/ -name "*.log" -mtime +30 -delete
   ```

3. **Monitor Disk Space**
   ```bash
   df -h
   docker system df
   ```

4. **Check Service Health**
   ```bash
   docker-compose ps
   curl http://localhost:5000/health
   ```

### Updates (Requires Manual Internet Access)

```bash
# On internet-connected machine:
docker pull exadel/compreface-api:1.3.0
docker save exadel/compreface-api:1.3.0 | gzip > api-update.tar.gz

# Transfer to offline server and load
docker load < api-update.tar.gz
docker-compose up -d
```

---

## FAQ

### Q: Can the system work without ANY network?

**A:** The system requires **local network** for:
- Cameras to communicate with server (RTSP)
- Users to access dashboard (HTTP)
- Docker containers to communicate

But **NO INTERNET** is required.

### Q: Do I need internet for initial setup?

**A:** Only for downloading Docker images initially. After that, system is fully offline.

**Alternative:** Download images on another computer and transfer via USB.

### Q: Can I use email alerts offline?

**A:** Yes, if you have an **internal email server** on your local network. Just point to it instead of Gmail/Yahoo.

### Q: How to update face recognition models?

**A:** Models are included in Docker images. Updates require:
1. Download new image (on internet PC)
2. Transfer to offline server
3. Load and restart

---

## Conclusion

The 1BIP Face Recognition & Attendance System is **100% offline** capable:

✅ No internet required for operation
✅ All communication via local network
✅ All processing on local server
✅ All data stored locally
✅ All resources self-hosted
✅ Complete privacy and security

**Perfect for:**
- Government facilities
- Secure corporate environments
- Air-gapped networks
- Privacy-sensitive applications
- Locations with unreliable internet

---

**Document Version:** 1.0
**Last Updated:** 2025-10-21
**For:** 1BIP Organization
**Status:** ✅ Fully Offline Compatible

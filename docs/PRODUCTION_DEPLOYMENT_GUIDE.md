# Legacy2Lake UTM - Production Deployment Guide

**Fecha:** Marzo 3, 2026  
**Versión:** v4.0 GA (Post-Launch Stabilization)  
**Target:** Dev → Production  
**Deployment Type:** Full Database + Code Deployment

---

## 🎯 Deployment Overview

### Strategy
**"Big Bang" Migration**: Full database clone + code deploy + validation

### Phases
1. **Pre-Deployment** (2 hours) - Prep, backup, validation
2. **Database Migration** (30 min) - Clone dev → prod, run migrations
3. **Code Deployment** (30 min) - Backend + Frontend deploy
4. **Post-Deployment** (1 hour) - Validation, monitoring, fixes
5. **Monitoring** (24 hours) - Watch for issues

**Total Estimated Time:** 4 hours active + 24 hours monitoring

---

## 📋 Pre-Deployment Checklist

### Code Validation ✅
- [x] v4.0 GA: All 6 pipeline stages validated end-to-end
- [x] Post-launch stabilization: 9 bugs fixed (BUG-001 → BUG-009 + 3 E2E bugs)
- [x] All critical features validated (Zero-Hardcode, RBAC, Ghost Mode, Agent Matrix)
- [x] No P0 bugs in backlog
- [ ] Git repo clean (no uncommitted changes)
- [ ] All PRs merged to main branch

### Documentation Ready ✅
- [ ] DATABASE_SCHEMA.md complete
- [ ] API endpoints documented
- [ ] Environment variables listed
- [ ] Rollback procedure documented
- [ ] Known issues documented

### Infrastructure Ready ✅
- [ ] Production Supabase project created
- [ ] Cloudflare R2 bucket configured
- [ ] Railway/Vercel accounts ready
- [ ] Environment secrets configured
- [ ] DNS records configured (if needed)
- [ ] SSL certificates valid

### Team Ready ✅
- [ ] Deployment window scheduled
- [ ] Team notified (no competing deploys)
- [ ] Rollback decision-maker identified
- [ ] Communication channels ready (Slack/Teams)
- [ ] Post-deployment monitoring assignments

---

## 🗄️ Database Migration (Dev → Prod)

### Step 1: Backup Development Database
```bash
# Set connection string
export DEV_DB_URL="postgresql://postgres:<password>@db.qdsdfityyxmalyipqbfm.supabase.co:5432/postgres"

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump "$DEV_DB_URL" \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  > "backups/utm_dev_backup_${TIMESTAMP}.sql"

# Verify backup size
ls -lh "backups/utm_dev_backup_${TIMESTAMP}.sql"

# Expected size: 5-20 MB (depends on data volume)
```

### Step 2: Sanitize Data (Optional)
```sql
-- Remove test/demo data if needed
BEGIN;

-- Option A: Delete specific test tenants
DELETE FROM utm_tenants WHERE name IN ('test_tenant', 'demo_test');

-- Option B: Keep only production tenants
DELETE FROM utm_tenants WHERE name NOT IN ('production_tenant_1', 'production_tenant_2');

-- Option C: Keep all data (no sanitization)
-- ROLLBACK;

COMMIT;
```

### Step 3: Clone to Production Database
```bash
# Set production connection
export PROD_DB_URL="postgresql://postgres:<prod_password>@db.<prod_project>.supabase.co:5432/postgres"

# Restore to production
psql "$PROD_DB_URL" < "backups/utm_dev_backup_${TIMESTAMP}.sql"

# Expected output: CREATE TABLE, INSERT statements, indexes creation
```

### Step 4: Verify Database Migration
```sql
-- Connect to production database
psql "$PROD_DB_URL"

-- Check table counts
SELECT 
    'utm_tenants' as table_name, COUNT(*) as rows FROM utm_tenants
UNION ALL
SELECT 'utm_users', COUNT(*) FROM utm_users
UNION ALL
SELECT 'utm_projects', COUNT(*) FROM utm_projects
UNION ALL
SELECT 'utm_prompts', COUNT(*) FROM utm_prompts
UNION ALL
SELECT 'utm_agents', COUNT(*) FROM utm_agents
UNION ALL
SELECT 'utm_design_registry', COUNT(*) FROM utm_design_registry;

-- Expected: Similar counts to dev (or less if sanitized)

-- Verify Sprint 1 cartridge prompts
SELECT COUNT(*) FROM utm_prompts WHERE prompt_id LIKE 'agent_c_%';
-- Expected: 24 cartridges

-- Check RLS policies enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE 'utm_%';
-- Expected: rowsecurity = true for all tables
```

### Step 5: Post-Migration SQL Updates
```sql
-- Update production-specific configs
BEGIN;

-- Update tenant settings for production
UPDATE utm_tenants 
SET settings = jsonb_set(
    settings, 
    '{environment}', 
    '"production"'
);

-- Deactivate test agents if any
UPDATE utm_agents 
SET is_active = FALSE 
WHERE display_name LIKE '%test%' OR display_name LIKE '%dev%';

-- Reset any locked processes
UPDATE utm_process_locks 
SET is_active = FALSE 
WHERE expires_at < NOW();

-- Verify changes
SELECT tenant_id, name, settings->'environment' FROM utm_tenants;

COMMIT;
```

---

## 🔐 Environment Variables

### Backend (.env for Railway/Docker)
```bash
# Supabase Configuration
SUPABASE_URL=https://<prod_project>.supabase.co
SUPABASE_ANON_KEY=<prod_anon_key>
SUPABASE_SERVICE_ROLE_KEY=<prod_service_role_key>

# Azure OpenAI (Agent LLMs)
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<api_key>
AZURE_OPENAI_DEPLOYMENT_GPT4O=<deployment_name>
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Cloudflare R2 Storage
R2_ACCOUNT_ID=<account_id>
R2_ACCESS_KEY_ID=<access_key>
R2_SECRET_ACCESS_KEY=<secret_key>
R2_BUCKET_NAME=utm-prod-storage
R2_PUBLIC_URL=https://storage.legacy2lake.com

# Application Settings
ENVIRONMENT=production
API_PORT=8085
FRONTEND_URL=https://utm.legacy2lake.com
ALLOWED_ORIGINS=https://utm.legacy2lake.com

# Security
JWT_SECRET=<generate_strong_secret>
SESSION_SECRET=<generate_strong_secret>
ENCRYPTION_KEY=<generate_strong_key>

# Monitoring (Optional)
SENTRY_DSN=<sentry_dsn>
LOGTAIL_TOKEN=<logtail_token>

# Email (if using invitations)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid_api_key>
FROM_EMAIL=noreply@legacy2lake.com
```

### Frontend (.env for Vercel/Next.js)
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.legacy2lake.com
NEXT_PUBLIC_SUPABASE_URL=https://<prod_project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<prod_anon_key>

# Application
NEXT_PUBLIC_APP_URL=https://utm.legacy2lake.com
NEXT_PUBLIC_ENVIRONMENT=production

# Analytics (Optional)
NEXT_PUBLIC_GA_TRACKING_ID=<google_analytics_id>
NEXT_PUBLIC_HOTJAR_ID=<hotjar_id>
```

### Generate Secrets
```bash
# Generate JWT secret (32 bytes)
openssl rand -base64 32

# Generate session secret (64 bytes)
openssl rand -base64 64

# Generate encryption key (32 bytes)
openssl rand -hex 32
```

---

## 🚀 Backend Deployment (Railway)

### Step 1: Prepare Repository
```bash
# Ensure on main branch
git checkout main
git pull origin main

# Tag release
git tag -a v1.0.0-sprint1 -m "Production release: Sprint 0 + Sprint 1"
git push origin v1.0.0-sprint1

# Verify clean state
git status
```

### Step 2: Deploy to Railway
```bash
# Via Railway CLI
railway login
railway link <production_project_id>

# Set environment variables
railway variables set SUPABASE_URL=<value>
railway variables set SUPABASE_SERVICE_ROLE_KEY=<value>
# ... (repeat for all env vars)

# Deploy
railway up

# Monitor logs
railway logs --follow
```

### Alternative: Railway Dashboard
1. Go to Railway dashboard
2. Create new project "UTM Production"
3. Connect GitHub repo (main branch)
4. Add environment variables (see section above)
5. Configure build settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
   - Port: 8085
6. Click "Deploy"
7. Wait for deployment (~3-5 min)
8. Verify health endpoint: `https://<railway_url>/health`

---

## 🎨 Frontend Deployment (Vercel)

### Step 1: Prepare Frontend
```bash
cd apps/web

# Update API URL in config
# Verify .env.production file exists with correct values

# Test build locally
npm run build

# Expected: Build succeeds with no errors
```

### Step 2: Deploy to Vercel
```bash
# Via Vercel CLI
vercel login
vercel --prod

# Or link first time
vercel link
vercel --prod

# Monitor deployment
vercel logs <deployment_url>
```

### Alternative: Vercel Dashboard
1. Go to Vercel dashboard
2. Import GitHub repository
3. Configure project:
   - Framework: Next.js
   - Root Directory: `apps/web`
   - Build Command: `npm run build`
   - Output Directory: `.next`
4. Add environment variables (see Frontend .env section)
5. Click "Deploy"
6. Wait for deployment (~2-4 min)
7. Configure custom domain (optional): `utm.legacy2lake.com`

---

## ✅ Post-Deployment Validation

### 1. Health Checks
```bash
# Backend health
curl https://api.legacy2lake.com/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Frontend health
curl https://utm.legacy2lake.com
# Expected: 200 OK, HTML response

# Database connection (via backend)
curl https://api.legacy2lake.com/api/health/db
# Expected: {"database": "connected", "tables": 15}
```

### 2. Authentication Test
```bash
# Login endpoint
curl -X POST https://api.legacy2lake.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@tenant.com", "password": "test123"}'

# Expected: {"access_token": "...", "user": {...}}
```

### 3. Agent C Code Generation Test
```bash
# Create test request payload
cat > test_agent_c.json <<EOF
{
  "node_data": {
    "name": "test_bronze",
    "layer": "bronze",
    "tech_id": "pyspark",
    "source_table": "dbo.Test",
    "target_table": "bronze.test",
    "primary_keys": ["id"]
  },
  "context": {
    "project_id": "<prod_project_id>",
    "source_tech": "mssql",
    "target_tech": "pyspark"
  }
}
EOF

# Test Agent C
curl -X POST https://api.legacy2lake.com/transpile/task \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <tenant_id>" \
  -H "X-User-ID: <user_id>" \
  -d @test_agent_c.json

# Expected: {"final_code": "...", "status": "success"}
```

### 4. Database Prompt Loading Test
```sql
-- Via Supabase SQL editor
SELECT 
    prompt_id,
    version_number,
    length(content) as size,
    is_active
FROM utm_prompts
WHERE prompt_id = 'agent_c_bronze_pyspark'
  AND tenant_id IS NULL;

-- Expected: 1 row, is_active = true, size ~9600 chars
```

### 5. End-to-End User Flow Test
```
1. Open https://utm.legacy2lake.com
2. Login with test user
3. Create new project
4. Upload source DDL
5. Generate design registry (Agent A)
6. Generate code for one node (Agent C)
7. Download generated code
8. Verify code quality

Expected: All steps complete without errors
```

---

## 📊 Monitoring & Alerting

### Key Metrics to Watch (First 24 Hours)

#### Application Metrics
- **Response Times**: API endpoints < 500ms p95
- **Error Rate**: < 1% of requests
- **Agent C Success Rate**: > 85%
- **Database Query Time**: < 100ms average

#### Infrastructure Metrics
- **CPU Usage**: < 70% sustained
- **Memory Usage**: < 80% sustained
- **Database Connections**: < 50% of pool
- **Storage (R2)**: Bandwidth and request count

#### Business Metrics
- **User Sign-ups**: Track new registrations
- **Code Generations**: Count per hour
- **Project Creations**: Track new projects
- **Active Users**: Concurrent users

### Monitoring Tools

#### Railway (Backend)
```
Dashboard → Metrics tab
- CPU usage graph
- Memory usage graph
- Network I/O
- Deployment logs (real-time)
```

#### Vercel (Frontend)
```
Dashboard → Analytics tab
- Page views
- Load times
- Error tracking
- Build activity
```

#### Supabase (Database)
```
Dashboard → Database tab
- Query performance
- Connection pool status
- Table statistics
- RLS policy hits
```

### Alert Thresholds
```
CRITICAL (Page immediately):
- Error rate > 5%
- API response time > 2 seconds
- Database down
- Storage quota exceeded

WARNING (Slack notification):
- Error rate > 2%
- API response time > 1 second
- CPU > 80%
- Memory > 85%
- Agent C success rate < 80%

INFO (Log only):
- Slow queries > 500ms
- High traffic periods
- Unused resources
```

---

## 🔄 Rollback Procedure

### When to Rollback
- Critical bugs affecting > 25% of users
- Data corruption detected
- Security vulnerability discovered
- Core features completely broken
- Decision by deployment lead

### Rollback Steps

#### 1. Rollback Code (10 minutes)
```bash
# Backend (Railway)
railway rollback <previous_deployment_id>

# Or via dashboard:
# Deployments → Select previous → "Redeploy"

# Frontend (Vercel)
vercel rollback <previous_deployment_url>

# Or via dashboard:
# Deployments → Previous → "Promote to Production"

# Verify rollback
curl https://api.legacy2lake.com/health
curl https://utm.legacy2lake.com
```

#### 2. Rollback Database (30 minutes)
```bash
# Restore from pre-deployment backup
psql "$PROD_DB_URL" << EOF
-- Drop all tables (careful!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Grant permissions
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
EOF

# Restore backup
psql "$PROD_DB_URL" < "backups/utm_pre_deployment_${DATE}.sql"

# Verify restoration
psql "$PROD_DB_URL" -c "SELECT COUNT(*) FROM utm_tenants;"
```

#### 3. Communicate Rollback
```
1. Post in Slack/Teams: "Production rolled back to previous version due to [reason]"
2. Email active users: "Brief service interruption resolved"
3. Update status page: "All systems operational"
4. Schedule postmortem: Review what went wrong
```

---

## 🐛 Common Deployment Issues

### Issue 1: Environment Variables Missing
**Symptoms:** Backend crashes on startup, 500 errors

**Solution:**
```bash
# Verify all env vars set
railway variables

# Add missing variables
railway variables set MISSING_VAR=value

# Redeploy
railway up --detach
```

### Issue 2: Database Connection Failed
**Symptoms:** "Could not connect to database" errors

**Solution:**
```bash
# Check Supabase project status
curl https://<project>.supabase.co

# Verify connection string
psql "$PROD_DB_URL" -c "SELECT 1;"

# Check RLS policies (may block service role)
# Temporarily disable RLS for debugging:
# ALTER TABLE utm_tenants DISABLE ROW LEVEL SECURITY;
```

### Issue 3: Slow Agent C Responses
**Symptoms:** Timeouts, 30+ second responses

**Solution:**
```python
# Check prompt loading from DB
# May need to add caching layer

# Temporary fix: Increase timeout
# apps/api/services/agent_c_service.py
timeout = 180  # from 120
```

### Issue 4: CORS Errors
**Symptoms:** Frontend can't call backend API

**Solution:**
```python
# apps/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://utm.legacy2lake.com"],  # Update production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 5: File Upload Failures
**Symptoms:** R2 storage errors, "Access Denied"

**Solution:**
```bash
# Verify R2 credentials in production
railway variables get R2_ACCESS_KEY_ID
railway variables get R2_SECRET_ACCESS_KEY

# Test R2 access
python << EOF
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='https://<account_id>.r2.cloudflarestorage.com',
    aws_access_key_id='<key>',
    aws_secret_access_key='<secret>'
)
s3.list_buckets()
EOF
```

---

## 📈 Post-Deployment Success Criteria

### Day 1 (First 24 Hours)
- [ ] Zero critical bugs reported
- [ ] All health checks passing
- [ ] Agent C success rate > 80%
- [ ] No performance degradation
- [ ] User feedback positive/neutral

### Week 1
- [ ] < 5 minor bugs reported
- [ ] Response times stable
- [ ] Database performance good
- [ ] Storage costs within budget
- [ ] User adoption growing

### Month 1
- [ ] Feature usage analytics collected
- [ ] Performance baselines established
- [ ] Monitoring alerts tuned
- [ ] Team comfortable with production ops
- [ ] Planning next sprint features

---

## 📞 Deployment Support

### Deployment Team Roles
```
Deployment Lead:      [Name] - Final rollback decision
Backend Engineer:     [Name] - API deployment, DB migration
Frontend Engineer:    [Name] - UI deployment, DNS
DevOps:               [Name] - Infrastructure, monitoring
QA:                   [Name] - Smoke tests, validation
Product:              [Name] - User communication
```

### Communication Channels
```
Real-time:  Slack #utm-deployment
Escalation: Phone tree documented
Users:      Status page + email
Incidents:  PagerDuty/OpsGenie
```

### Deployment Windows
```
Preferred:   Tuesday-Thursday, 10AM-2PM (avoid Mondays & Fridays)
Avoid:       Evenings, weekends, holidays, major customer events
Duration:    4 hours active work + 24 hours monitoring
Rollback:    Must be possible within 1 hour
```

---

## ✅ Pre-Deployment Final Checklist

**24 Hours Before:**
- [ ] Schedule deployment window
- [ ] Notify team and stakeholders
- [ ] Backup dev database
- [ ] Test backup restoration
- [ ] Review all deployment steps
- [ ] Verify environment variables documented
- [ ] Confirm rollback procedure ready

**1 Hour Before:**
- [ ] Team assembled and ready
- [ ] Communication channels open
- [ ] Backup procedure tested
- [ ] Monitoring dashboards open
- [ ] Coffee/food prepared (long session!)

**Go/No-Go Decision:**
- [ ] All team members present?
- [ ] All tests passing?
- [ ] No major bugs in backlog?
- [ ] Infrastructure ready?
- [ ] Rollback plan clear?

**If all checked:** ✅ GO FOR DEPLOYMENT

**If any unchecked:** ⚠️ POSTPONE & FIX

---

**Document Version:** 2.0  
**Last Updated:** Marzo 3, 2026  
**Owner:** DevOps Team  
**Status:** ✅ v4.0 GA — Ready for Production Deployment  
**Next Review:** Post-deployment (within 48 hours)

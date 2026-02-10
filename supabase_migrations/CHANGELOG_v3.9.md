# v3.9 Migration Scripts - Change Log

**Date Created:** 2026-02-09
**Version:** v3.9 - Multi-User Support
**Status:** Ready for Testing

---

## Scripts Created (7 total)

### ✅ 010_v3.9_create_users_table.sql
- **Purpose:** Creates `utm_users` table for separate user identity
- **Changes:**
  - New table: `utm_users` with fields: user_id, tenant_id, email, username, password_hash_bcrypt, role (ADMIN/COLLABORATOR/VIEWER), is_active
  - Unique constraint on email (global)
  - Unique constraint on (tenant_id, email)
  - Indexes on tenant_id, email, role, is_active
- **Dependencies:** None (run first)
- **Rollback:** Safe to drop table before data migration

---

### ✅ 011_v3.9_create_invitations_table.sql
- **Purpose:** Email-based invitation workflow
- **Changes:**
  - New table: `utm_user_invitations` with token-based acceptance
  - Fields: invitation_id, tenant_id, email, role, token, expires_at, status (PENDING/ACCEPTED/EXPIRED/REVOKED)
  - Auto-expire function for old invitations
  - Default expiry: 7 days
- **Dependencies:** Requires `utm_users` table (run after 010)
- **Rollback:** Safe to drop table

---

### ✅ 012_v3.9_refactor_tenants.sql
- **Purpose:** Convert tenants → organizations
- **Changes:**
  - Backs up `utm_tenants` → `utm_tenants_old`
  - Recreates `utm_tenants` with new schema:
    - Removes user-specific fields (username, password, role)
    - Adds organization fields (org_name, org_logo_url, tier)
    - tier: STANDARD/PREMIUM/ENTERPRISE (for future pricing)
  - Keeps tenant_id, client_id, is_active, timestamps
- **Dependencies:** None, but must run BEFORE 015 (data migration)
- **Rollback:** Restore from `utm_tenants_old`
- **⚠️ CRITICAL:** Keep `utm_tenants_old` for 1 week minimum

---

### ✅ 013_v3.9_add_user_ref_projects.sql
- **Purpose:** Add user ownership to projects
- **Changes:**
  - Adds column `created_by_user_id UUID` to `utm_projects`
  - Foreign key to `utm_users(user_id)` with ON DELETE SET NULL
  - Index on created_by_user_id
- **Dependencies:** Requires `utm_users` table (run after 010)
- **Rollback:** Safe to drop column

---

### ✅ 014_v3.9_add_user_ref_locks.sql
- **Purpose:** Track which user owns process locks
- **Changes:**
  - Adds column `locked_by_user_email VARCHAR(255)` to `utm_process_locks`
  - Index on locked_by_user_email
- **Dependencies:** None
- **Rollback:** Safe to drop column

---

### ✅ 015_v3.9_data_migration.sql ⚠️ MOST CRITICAL
- **Purpose:** Migrate all existing data to new structure
- **Changes:**
  1. **Migrate Tenants:** `utm_tenants_old` → `utm_tenants` (as organizations)
  2. **Create Users:** One ADMIN user per tenant (user_id = tenant_id for backward compat)
  3. **Update Projects:** Set `created_by_user_id` to first user of each tenant
  4. **Validation:** Verifies counts match, no data loss
- **Dependencies:** Run AFTER 010-014 (last schema script)
- **Rollback:** Use ROLLBACK_v3.9.sql
- **⚠️ TESTING REQUIRED:**
  - Test on staging with real production data snapshot
  - Verify ZERO data loss
  - Verify user_id = tenant_id for first user (backward compat)
  - Verify all projects have owner

---

### ✅ 016_v3.9_update_rls_policies.sql
- **Purpose:** Implement role-based access control
- **Changes:**
  - **utm_projects:** All users can read, ADMIN/COLLABORATOR can write, only ADMIN can delete
  - **utm_assets:** Same as projects
  - **utm_users:** Users see same tenant, ADMIN can manage all
  - **utm_user_invitations:** ADMIN-only access
  - Helper function: `get_user_role(user_uuid, tenant_uuid)`
- **Dependencies:** Run AFTER 015 (data migration)
- **Rollback:** Restore old policies

---

### ✅ ROLLBACK_v3.9.sql (Emergency Recovery)
- **Purpose:** Complete rollback to v3.8 state
- **Use Case:** Critical migration failure
- **Changes:**
  1. Drops utm_users, utm_user_invitations
  2. Drops new utm_tenants
  3. Restores utm_tenants_old → utm_tenants
  4. Removes new columns from projects, locks
- **⚠️ WARNING:** DESTROYS all v3.9 multi-user data
- **When to use:** Only if production is broken and cannot wait for fix

---

## Execution Order

```bash
# 1. Schema changes (safe, reversible)
psql -f 010_v3.9_create_users_table.sql
psql -f 011_v3.9_create_invitations_table.sql
psql -f 012_v3.9_refactor_tenants.sql
psql -f 013_v3.9_add_user_ref_projects.sql
psql -f 014_v3.9_add_user_ref_locks.sql

# 2. Data migration (CRITICAL - test first!)
psql -f 015_v3.9_data_migration.sql

# 3. Security policies
psql -f 016_v3.9_update_rls_policies.sql
```

---

## Verification Queries

### After Each Script
```sql
-- Check script ran successfully
SELECT * FROM information_schema.tables 
WHERE table_name LIKE 'utm_%' 
ORDER BY table_name;
```

### After Data Migration (015)
```sql
-- Verify tenant count
SELECT 
    (SELECT count(*) FROM utm_tenants_old) AS old_count,
    (SELECT count(*) FROM utm_tenants) AS new_count,
    (SELECT count(*) FROM utm_users) AS user_count;
-- All three should match!

-- Verify first user = tenant_id (backward compat)
SELECT 
    t.tenant_id,
    t.org_name,
    u.user_id,
    u.email,
    u.role,
    (t.tenant_id = u.user_id) AS backward_compatible
FROM utm_tenants t
LEFT JOIN utm_users u ON u.tenant_id = t.tenant_id
ORDER BY t.created_at;
-- backward_compatible should be TRUE for all legacy tenants

-- Verify all projects have owner
SELECT 
    count(*) AS total_projects,
    count(created_by_user_id) AS projects_with_owner,
    count(*) - count(created_by_user_id) AS orphans
FROM utm_projects;
-- orphans should be 0
```

### After RLS Policies (016)
```sql
-- Check policies created
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE tablename IN ('utm_projects', 'utm_assets', 'utm_users', 'utm_user_invitations')
ORDER BY tablename, cmd;
```

---

## Safety Checklist

- [ ] All scripts tested on staging environment
- [ ] Production data snapshot taken
- [ ] Backup of utm_tenants_old verified
- [ ] Rollback script tested
- [ ] Team trained on verification queries
- [ ] Maintenance window scheduled (low traffic time)
- [ ] Communication plan for users (downtime notice)
- [ ] Post-migration verification plan
- [ ] Keep utm_tenants_old for minimum 1 week

---

## Estimated Downtime

- **Small database (<1000 tenants):** 5-10 minutes
- **Medium database (1000-10000 tenants):** 15-30 minutes
- **Large database (>10000 tenants):** 30-60 minutes

Most downtime is from RLS policy updates and index creation.

---

## Post-Migration Monitoring

### First 24 Hours
- Monitor error rates (should be 0)
- Check login success rate
- Verify project access works
- Test invitation flow with 2-3 beta users

### First Week
- Monitor user_id = tenant_id queries (backward compat)
- Check for orphaned projects
- Verify RLS policies enforce correctly
- Test all 3 roles (ADMIN, COLLABORATOR, VIEWER)

### After 1 Week
- If stable, can drop utm_tenants_old
- Remove rollback script from production
- Mark migration as complete

---

## Known Issues & Workarounds

### Issue 1: Password Hash Migration
- **Problem:** Old tenants may have SHA256 hashes instead of bcrypt
- **Workaround:** Set dummy hash, force password reset on first login
- **Script:** Migration 015 sets `$2b$12$DUMMY_HASH_NEEDS_RESET` for missing hashes

### Issue 2: Email Format
- **Problem:** Legacy tenants don't have email
- **Workaround:** Generate email from username: `{username}@legacy.local`
- **Script:** Migration 015 creates synthetic emails

### Issue 3: Multiple Tenants Same Email
- **Problem:** If user wants same email across multiple organizations
- **Workaround:** Not supported in v3.9 - user must use different email per tenant
- **Future:** v4.0 will support organization switching

---

## Contact

- **Lead Developer:** [Your Name]
- **Database Admin:** [DBA Name]
- **Emergency:** [On-call number]

---

**Last Updated:** 2026-02-09
**Next Review:** After staging deployment (Feb 14)

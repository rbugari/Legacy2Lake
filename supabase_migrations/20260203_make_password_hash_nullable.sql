-- Migration: Make password_hash nullable to support bcrypt-only users (invitations)
ALTER TABLE utm_tenants ALTER COLUMN password_hash DROP NOT NULL;

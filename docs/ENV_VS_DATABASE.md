# Environment Vs Database

> Last Updated: 2026-03-21
> Status: current

Legacy2Lake separates infrastructure configuration from tenant runtime configuration.

## `.env`

Use `.env` for deployment- or environment-level values such as:

- Supabase connection
- storage settings
- runtime host values

## Database

Use the database-backed runtime model for tenant-specific operational behavior such as:

- provider configuration
- model assignment
- agent routing
- runtime prompt records
- project settings and optional custom instructions

## Rule Of Thumb

- infrastructure belongs in `.env`
- tenant runtime behavior belongs in the database

This keeps deployment concerns separate from customer-specific operation and governance.

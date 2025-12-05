# Supabase Migrations Guide

This project uses Supabase CLI for database migrations. All migrations are stored in `supabase/migrations/`.

## Creating a New Migration

**Always use Supabase CLI to generate migrations:**

```bash
cd backend
supabase migration new <migration_name>
```

This creates a new migration file with a timestamp prefix (e.g., `20241204210000_migration_name.sql`).

## Editing Migrations

1. **Open the generated migration file** in `supabase/migrations/`
2. **Add your SQL statements** (CREATE TABLE, ALTER TABLE, etc.)
3. **Test locally** (if using local Supabase):
   ```bash
   supabase db reset
   ```

## Applying Migrations to Remote Database

```bash
cd backend
supabase db push
```

This will:
- Show you which migrations will be applied
- Ask for confirmation
- Apply migrations to your linked Supabase project

## Best Practices

1. **Always use `supabase migration new`** - Never create migration files manually
2. **Use `gen_random_uuid()`** instead of `uuid_generate_v4()` (built-in, no extension needed)
3. **Test migrations locally first** if possible
4. **One logical change per migration** - Keep migrations focused
5. **Never edit existing migrations** - Create a new migration to fix issues

## Current Migrations

- `001_initial_schema.sql` - Initial database schema (tables, RLS policies, indexes)
- `002_system_templates.sql` - System product templates

## Troubleshooting

If you get errors about missing functions or extensions:
- Use `gen_random_uuid()` instead of `uuid_generate_v4()`
- Check Supabase documentation for available extensions
- Ensure you're connected to the correct project: `supabase link --project-ref <your-project-ref>`


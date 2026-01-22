-- Fix permissions for newly created tables
GRANT ALL ON TABLE public.utm_asset_context TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.utm_transformations TO anon, authenticated, service_role;

-- Add permissive RLS policies (adjust as needed later)
-- Note: We already enabled RLS in the previous migration, but didn't add policies.

CREATE POLICY "Enable all for all users" ON public.utm_asset_context
    FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for all users" ON public.utm_transformations
    FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);

-- Grant permissions for utm_execution_logs
GRANT ALL ON TABLE utm_execution_logs TO postgres, anon, authenticated, service_role;
GRANT ALL ON SEQUENCE utm_execution_logs_id_seq TO postgres, anon, authenticated, service_role;

-- Enable RLS for utm_execution_logs
ALTER TABLE utm_execution_logs ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for utm_execution_logs
CREATE POLICY "Enable read access for all users" ON utm_execution_logs FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON utm_execution_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON utm_execution_logs FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON utm_execution_logs FOR DELETE USING (true);

-- Grant permissions for utm_file_inventory
GRANT ALL ON TABLE utm_file_inventory TO postgres, anon, authenticated, service_role;
-- Assuming utm_file_inventory might have a sequence if it fulfills a similar role, though usually it uses uuid or path as key. 
-- If it has a serial ID, we'd grant on that too, but usually explicit keys are used. 
-- Just in case it has an id sequence:
-- GRANT ALL ON SEQUENCE utm_file_inventory_id_seq TO postgres, anon, authenticated, service_role;

-- Enable RLS for utm_file_inventory
ALTER TABLE utm_file_inventory ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for utm_file_inventory
CREATE POLICY "Enable read access for all users" ON utm_file_inventory FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON utm_file_inventory FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON utm_file_inventory FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON utm_file_inventory FOR DELETE USING (true);

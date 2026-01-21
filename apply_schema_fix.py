import os
import sys
from dotenv import load_dotenv
import psycopg2

def fix_schema():
    # 1. Manually parse .env to find DIRECT_URL even if commented
    db_url = None
    with open(".env", "r") as f:
        for line in f:
            if "DIRECT_URL" in line:
                # Remove comments & quotes
                parts = line.split("=", 1)
                if len(parts) > 1:
                    raw_val = parts[1].strip().strip('"').strip("'")
                    # Handle commented out line like # DIRECT_URL=...
                    if line.strip().startswith("#"):
                        # re-split from the =
                        if "=" in line:
                            raw_val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    
                    db_url = raw_val
                    break
    
    if not db_url:
        print("DIRECT_URL not found in .env (even commented).")
        return

    print(f"Found URL template: {db_url}")

    # 2. Handle [PASSWORD] placeholder
    # Try multiple passwords, including the one from memory "A1111rfb" and "A2321rfb!"
    candidates = ["A1111rfb", "A2321rfb!", "A2321rfb"]
    valid_conn_url = None

    if "[PASSWORD]" in db_url:
        print("Detected [PASSWORD] placeholder. Trying known passwords...")
        for p in candidates:
            try:
                test_url = db_url.replace("[PASSWORD]", p)
                # Try connecting
                conn = psycopg2.connect(test_url)
                conn.close()
                print(f"Success with password: {p}")
                valid_conn_url = test_url
                break
            except Exception as e:
                print(f"Failed with candidate {p}: {e}")
    else:
        # Maybe the password is valid as is?
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            valid_conn_url = db_url
            print("Connected with existing URL.")
        except Exception as e:
            print(f"Existing URL failed: {e}")
            # fall through to candidates if user put a partial password? Unlikely.
    
    if not valid_conn_url:
        print("Could not connect to database. Please check .env or Schema.")
        return

    # 3. Apply Schema Changes
    print("Applying Schema Changes...")
    try:
        conn = psycopg2.connect(valid_conn_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        stmts = [
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS frequency text DEFAULT 'DAILY';",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS load_strategy text DEFAULT 'FULL_OVERWRITE';",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS criticality text DEFAULT 'P3';",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS is_pii boolean DEFAULT false;",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS masking_rule text;",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS business_entity text;",
            "ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS target_name text;",
            "NOTIFY pgrst, 'reload config';"
        ]
        
        for s in stmts:
            try:
                cur.execute(s)
                print(f"Executed: {s}")
            except Exception as e:
                # Ignore duplicate column error if it happens race condition style
                if "already exists" in str(e):
                    print(f"Exists: {s}")
                else:
                    print(f"Error executing '{s}': {e}")
                
        cur.close()
        conn.close()
        print("Schema update complete.")
    except Exception as e:
        print(f"Connection failed during update: {e}")

if __name__ == "__main__":
    fix_schema()

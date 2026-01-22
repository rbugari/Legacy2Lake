import subprocess
import os
import sys
import time
import copy

def main():
    print("✨ Legacy2Lake Platform Launcher ✨")
    print("--------------------------------")
    print("🚀 Launching Backend & Frontend in separate windows...")

    # Paths
    root_dir = os.getcwd()
    frontend_dir = os.path.join(root_dir, "apps", "web")
    api_path = os.path.join(root_dir, "apps", "api")

    # Load .env manually to be robust
    env_vars = os.environ.copy()
    env_file = os.path.join(root_dir, ".env")
    if os.path.exists(env_file):
        print("Loading .env file...")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    env_vars[key] = value

    # Prepare environment for Backend (Inject PYTHONPATH)
    env_vars["PYTHONPATH"] = f"{api_path};{env_vars.get('PYTHONPATH', '')}"

    # Check for Windows
    if os.name == 'nt':
        supabase_url = env_vars.get("SUPABASE_URL", "")
        supabase_key = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")
        
        # Backend Command
        # Using default port 8085
        backend_cmd = f'start "Legacy2Lake API (Port 8085)" cmd /k "set PYTHONPATH={api_path};%PYTHONPATH% && set SUPABASE_URL={supabase_url} && set SUPABASE_SERVICE_ROLE_KEY={supabase_key} && {sys.executable} -m uvicorn apps.api.main:app --port 8085 --reload --reload-dir apps"'
        
        subprocess.Popen(
            backend_cmd,
            cwd=root_dir,
            shell=True
        )
        
        # Frontend
        subprocess.Popen(
            'start "Legacy2Lake Web (Port 3005)" cmd /k "npm.cmd run dev -- -p 3005"',
            cwd=frontend_dir,
            shell=True
        )
        
        print("\n✅ Services launched!")
        print("   - API: http://localhost:8085")
        print("   - Web: http://localhost:3005")
        
    else:
        # Fallback for Linux/Mac
        print("[WARN] Non-Windows OS detected. Running sequentially (blocking).")
        try:
             subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--port", "8086", "--reload"], cwd=root_dir, env=env_vars)
             subprocess.Popen(["npm", "run", "dev", "--", "-p", "3005"], cwd=frontend_dir)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()

import subprocess
import os
import sys
import time
from pathlib import Path

def kill_process_on_port(port):
    """Kill any process running on the specified port (Windows)"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids.add(pid)
            
            for pid in pids:
                try:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    print(f"   ✅ Killed process {pid} on port {port}")
                except:
                    pass
            
            if pids:
                time.sleep(1)
                return True
        return False
    except:
        return False

def main():
    print("\n" + "="*40)
    print("✨ Legacy2Lake Platform Launcher ✨")
    print("="*40)
    
    # Root directory setup
    root_dir = Path(__file__).parent.absolute()
    os.chdir(root_dir)
    print(f"📁 Working Directory: {root_dir}")

    # Kill existing processes
    print("\n🧹 Cleaning ports...")
    kill_process_on_port(8085)
    kill_process_on_port(3005)
    
    # Paths
    frontend_dir = root_dir / "apps" / "web"
    api_path = root_dir / "apps" / "api"

    # Load .env manually to be robust
    env_vars = os.environ.copy()
    env_file = root_dir / ".env"
    if env_file.exists():
        print("📝 Loading .env file...")
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    try:
                        key, value = line.split("=", 1)
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        env_vars[key] = value
                    except ValueError:
                        continue

    # Force Debug Mode for visibility
    env_vars["DEBUG_MODE"] = "true"
    env_vars["LOG_LEVEL"] = "DEBUG"
    
    # Prepare environment for Backend (Inject PYTHONPATH)
    # Important: root_dir must be in PYTHONPATH for `apps.api` imports to work
    python_path = str(root_dir)
    env_vars["PYTHONPATH"] = f"{python_path};{env_vars.get('PYTHONPATH', '')}"

    print("🚀 Launching Backend & Frontend in separate windows...")

    # Check for Windows
    if os.name == 'nt':
        supabase_url = env_vars.get("SUPABASE_URL", "")
        supabase_key = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")
        
        # Create a temporary .bat file to ensure env vars are inherited and python path is correct
        bat_content = f'''@echo off
set PYTHONPATH={python_path}
set SUPABASE_URL={supabase_url}
set SUPABASE_SERVICE_ROLE_KEY={supabase_key}
set DEBUG_MODE=true
set LOG_LEVEL=DEBUG
echo ============================================================
echo 🚀 Starting Backend with DEBUG_MODE=true
echo ============================================================
"{sys.executable}" -m uvicorn apps.api.main:app --port 8085 --reload --reload-dir apps
'''
        
        bat_file = root_dir / "_start_backend.bat"
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        # Backend Command - execute the batch file
        backend_cmd = f'start "Legacy2Lake API (Port 8085)" cmd /k "{bat_file}"'
        
        subprocess.Popen(
            backend_cmd,
            cwd=str(root_dir),
            shell=True
        )
        
        # Frontend
        if frontend_dir.exists():
            subprocess.Popen(
                'start "Legacy2Lake Web (Port 3005)" cmd /k "npm.cmd run dev -- -p 3005"',
                cwd=str(frontend_dir),
                shell=True
            )
        else:
            print(f"⚠️  Frontend directory not found at {frontend_dir}")
        
        print("\n✅ Services launched!")
        print(f"   - API: http://localhost:8085")
        print(f"   - Web: http://localhost:3005")
        print("\nLogs will appear in the new windows. Check for '🤖 LLM START' messages.\n")
        
    else:
        # Fallback for Linux/Mac
        print("[WARN] Non-Windows OS detected. Running sequentially (blocking).")
        try:
             subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--port", "8085", "--reload"], cwd=str(root_dir), env=env_vars)
             if frontend_dir.exists():
                subprocess.Popen(["npm", "run", "dev", "--", "-p", "3005"], cwd=str(frontend_dir))
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

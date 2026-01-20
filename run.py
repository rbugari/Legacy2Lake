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

    # Prepare environment for Backend (Inject PYTHONPATH)
    backend_env = os.environ.copy()
    current_pythonpath = backend_env.get("PYTHONPATH", "")
    backend_env["PYTHONPATH"] = f"{api_path};{current_pythonpath}"

    # Check for Windows
    if os.name == 'nt':
        # Backend
        # We explicitly activate the current python environment using sys.executable
        # Note: 'start' command in Windows doesn't easily accept env vars directly for the new window
        # unless we set them in the command string itself.
        # My previous attempt failed because of syntax. Trying a cleaner approach:
        # We launch a python script that sets the env and runs uvicorn.
        
        # Command Construction:
        # set PYTHONPATH=... && python -m uvicorn ...
        
        backend_cmd = f'start "Legacy2Lake API (Port 8085)" cmd /k "set PYTHONPATH={api_path};%PYTHONPATH% && {sys.executable} -m uvicorn apps.api.main:app --port 8085 --reload --reload-exclude solutions"'
        
        subprocess.Popen(
            backend_cmd,
            cwd=root_dir,
            shell=True
        )
        
        # Frontend
        # Launching npm in a new window
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
             subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--port", "8085", "--reload"], cwd=root_dir, env=backend_env)
             subprocess.Popen(["npm", "run", "dev", "--", "-p", "3005"], cwd=frontend_dir)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()

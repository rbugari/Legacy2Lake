import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Add apps/api to pythonpath
root_dir = os.getcwd()
api_path = os.path.join(root_dir, "apps", "api")
env = os.environ.copy()
env["PYTHONPATH"] = f"{api_path};{env.get('PYTHONPATH', '')}"

print("Starting Ephemeral Backend on 8087...")
subprocess.run([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--port", "8087"], env=env)

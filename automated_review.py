import subprocess
import requests
import time
import os
import sys

# Configuration
API_PORT = 8085
API_URL = f"http://localhost:{API_PORT}"
ROOT_DIR = os.getcwd()
FIXTURE_PATH = os.path.join(ROOT_DIR, "tests", "fixtures", "ssis_test_repo", "Building Sales Data Mart Using ETL", "ETL_Dim_Customer.dtsx")
OUTPUT_PY_PATH = os.path.join(ROOT_DIR, "output", "test_automation", "ETL_Dim_Customer.py")
BACKEND_LOG_FILE = os.path.join(ROOT_DIR, "backend_debug.log")

def print_pass(msg):
    print(f"✅ [PASS] {msg}")

def print_fail(msg):
    print(f"❌ [FAIL] {msg}")

def print_info(msg):
    print(f"ℹ️  [INFO] {msg}")

def check_backend_health():
    print_info("Checking Backend Health...")
    retries = 20
    for i in range(retries):
        try:
            resp = requests.get(f"{API_URL}/ping", timeout=5)
            if resp.status_code == 200:
                print_pass("Backend is up and responsive!")
                return True
        except requests.exceptions.RequestException as e:
            # Catch ConnectionError, ReadTimeout, etc.
            pass
        
        if i % 2 == 0:
            print(f"   Waiting for backend... ({i}/{retries})")
        time.sleep(2)
    
    print_fail("Backend failed to start.")
    return False

def verify_prompts():
    print_info("Verifying Agent Prompts (Fix Validation)...")
    agents = ["agent-a", "agent-c", "agent-f", "agent-g"]
    all_passed = True
    
    for agent in agents:
        url = f"{API_URL}/prompts/{agent}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "prompt" in data and len(data["prompt"]) > 0:
                    print_pass(f"Prompt for {agent} loaded successfully.")
                else:
                    print_fail(f"Prompt for {agent} is empty.")
                    all_passed = False
            else:
                print_fail(f"Prompt for {agent} returned status {resp.status_code}: {resp.text}")
                all_passed = False
        except Exception as e:
            print_fail(f"Exception checking {agent}: {e}")
            all_passed = False
            
    return all_passed

def run_pipeline_test():
    print_info("Running UTM Pipeline Test...")
    
    if not os.path.exists(FIXTURE_PATH):
        print_fail(f"Fixture not found at {FIXTURE_PATH}")
        return False

    cmd = [
        sys.executable,
        os.path.join(ROOT_DIR, "run_utm_pipeline.py"),
        "--file", FIXTURE_PATH,
        "--output", OUTPUT_PY_PATH,
        "--target", "databricks"
    ]
    
    print(f"   Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_pass("Pipeline script executed successfully.")
            if os.path.exists(OUTPUT_PY_PATH):
                print_pass(f"Output file generated at {OUTPUT_PY_PATH}")
                if os.path.getsize(OUTPUT_PY_PATH) > 0:
                     print_pass("Output file is not empty.")
                     return True
                else:
                     print_fail("Output file is empty.")
            else:
                print_fail("Output file was NOT generated.")
        else:
            print_fail(f"Pipeline script failed with return code {result.returncode}")
            # print("   --- STDERR ---")
            # print(result.stderr) # Keep concise
    except Exception as e:
        print_fail(f"Exception running pipeline: {e}")
        
    return False

def main():
    print("🚀 AUTOMATED REVIEW & TESTING SCRIPT (v2) 🚀")
    print("------------------------------------------")
    
    # 1. Start Backend in Background
    print_info(f"Starting Backend API on port {API_PORT}...")
    
    # Setup Environment
    env = os.environ.copy()
    api_path = os.path.join(ROOT_DIR, "apps", "api")
    current_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{api_path};{current_pp}"
    
    # Capture output to file for debugging
    with open(BACKEND_LOG_FILE, "w") as log_file:
         backend_cmd = [sys.executable, "-m", "uvicorn", "apps.api.main:app", "--port", str(API_PORT)]
         backend_proc = subprocess.Popen(backend_cmd, cwd=ROOT_DIR, env=env, stdout=log_file, stderr=subprocess.STDOUT)
    
    results = {}
    
    try:
        # 2. Check Health
        if check_backend_health():
            results["Backend Start"] = True
            results["Prompt Loading Fix"] = verify_prompts()
            results["Legacy2Lake Pipeline"] = run_pipeline_test()
            # results["Agent A Logic"] = run_agent_a_test() # Skipped for speed/focus
        else:
            results["Backend Start"] = False
            
            # Print last lines of backend log
            print_fail("Backend Log Snippet:")
            try:
                with open(BACKEND_LOG_FILE, "r") as f:
                    lines = f.readlines()
                    print("".join(lines[-20:]))
            except:
                print("(Could not read backend log)")
            
            # Still run pipeline check
            results["Legacy2Lake Pipeline"] = run_pipeline_test()

    finally:
        print_info("Stopping Backend Server...")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
            
    print("\n---------------------------------------")
    print("📊 TEST SUMMARY 📊")
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")
        if not passed: all_passed = False
        
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
    else:
        print("⚠️ SOME CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()


import requests
import hashlib
import json

def test_login():
    url = "http://localhost:8085/login"
    payload = {
        "username": "DEMO",
        "password": "DEMO123!"
    }
    
    print(f"Testing Login against {url} with {payload}")
    
    try:
        res = requests.post(url, json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        
        if res.status_code == 200:
            print("[PASS] Login Successful")
        else:
            print("[FAIL] Login Failed")
            
    except Exception as e:
        print(f"[Error] {e}")

if __name__ == "__main__":
    test_login()

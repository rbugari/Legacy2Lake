
import asyncio
import os
import sys
import bcrypt
import hashlib

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def debug_user():
    username = "user_saas_5786"
    password = "DEMO123!"
    
    print(f"--- Debugging User: {username} ---")
    
    db = SupabasePersistence(tenant_id=None)
    res = db.client.table("utm_tenants").select("*").eq("username", username).execute()
    
    if not res.data:
        print("USER NOT FOUND!")
        return
        
    user = res.data[0]
    print(f"Tenant ID: {user.get('tenant_id')}")
    print(f"Role: {user.get('role')}")
    print(f"Has SHA256: {'Yes' if user.get('password_hash') else 'No'}")
    print(f"Has Bcrypt: {'Yes' if user.get('password_hash_bcrypt') else 'No'}")
    
    # Check SHA256 manually
    if user.get("password_hash"):
        calc_sha = hashlib.sha256(password.encode()).hexdigest()
        match = (calc_sha == user["password_hash"])
        print(f"SHA256 Check ('{password}'): {match}")
        if not match:
             print(f"  Expected: {calc_sha}")
             print(f"  Stored:   {user['password_hash']}")

    # Check Bcrypt manually
    if user.get("password_hash_bcrypt"):
        stored_bcrypt = user["password_hash_bcrypt"]
        try:
            match = bcrypt.checkpw(password.encode(), stored_bcrypt.encode())
            print(f"Bcrypt Check ('{password}'): {match}")
        except Exception as e:
            print(f"Bcrypt Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_user())

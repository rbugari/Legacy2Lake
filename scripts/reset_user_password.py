
import asyncio
import os
import sys
import bcrypt
import hashlib

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def reset_password():
    username = "user_saas_5786"
    password = "DEMO123!"
    
    print(f"--- Resetting Password for {username} to '{password}' ---")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Generate new hashes
    salt = bcrypt.gensalt(rounds=12)
    bcrypt_hash = bcrypt.hashpw(password.encode(), salt).decode()
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Update DB
    res = db.client.table("utm_tenants").update({
        "password_hash": sha256_hash,
        "password_hash_bcrypt": bcrypt_hash
    }).eq("username", username).execute()
    
    if res.data:
        print("SUCCESS: Password updated.")
        # Verify immediately
        updated = res.data[0]
        print(f"New SHA256: {updated.get('password_hash')}")
        print(f"New Bcrypt: Present")
    else:
        print("FAILED: User not found or update failed.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(reset_password())

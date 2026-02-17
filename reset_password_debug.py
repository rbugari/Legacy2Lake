import sys
import os
import asyncio
import bcrypt

# Add project root to path
sys.path.append("c:\\proyectos_dev\\UTM")

from apps.api.services.persistence_service import SupabasePersistence

def hash_password_bcrypt(password: str) -> str:
    """Generate secure bcrypt hash."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

async def reset_password():
    try:
        print("Connecting to DB...")
        db = SupabasePersistence(tenant_id=None) 
        
        target_user = "DEMO34"
        new_password = "password123"
        print(f"Reseting password for {target_user} to '{new_password}'...")
        
        # 1. Get User ID
        res = db.client.table("utm_users").select("user_id").eq("username", target_user).execute()
        if not res.data:
            print(f"User {target_user} not found!")
            return
        
        user_id = res.data[0]["user_id"]
        
        # 2. Hash Password
        hashed = hash_password_bcrypt(new_password)
        
        # 3. Update DB
        update_res = db.client.table("utm_users").update({
            "password_hash_bcrypt": hashed
        }).eq("user_id", user_id).execute()
        
        print("Password reset successful!")
        print(f"Login with: {target_user} / {new_password}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(reset_password())

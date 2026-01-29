
import asyncio
import os
import hashlib
import bcrypt
from dotenv import load_dotenv

# Ensure we can import from apps
import sys
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

def hash_password_bcrypt(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

async def setup_demo_client():
    print("--- Setting up DEMO2 Client ---")
    
    # Init DB as Admin
    db = SupabasePersistence(tenant_id=None)
    
    # 1. Create Client
    client_name = "CLIENTE_DEMO_2"
    client_id = None
    
    res = db.client.table("utm_clients").select("client_id").eq("name", client_name).execute()
    if res.data:
        client_id = res.data[0]["client_id"]
        print(f"[Info] Found existing Client {client_name}: {client_id}")
    else:
        res = db.client.table("utm_clients").insert({"name": client_name}).execute()
        client_id = res.data[0]["client_id"]
        print(f"[Success] Created Client {client_name}: {client_id}")

    # 2. Create User DEMO2
    username = "DEMO2"
    password_plain = "DEMO123!"
    tenant_id = None
    
    res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if res.data:
        tenant_id = res.data[0]["tenant_id"]
        print(f"[Info] Found existing User {username}: {tenant_id}")
    else:
        new_tenant = {
            "client_id": client_id,
            "username": username,
            "password_hash": hashlib.sha256(password_plain.encode()).hexdigest(),
            "password_hash_bcrypt": hash_password_bcrypt(password_plain),
            "role": "USER" # Explicitly NOT Admin
        }
        res = db.client.table("utm_tenants").insert(new_tenant).execute()
        tenant_id = res.data[0]["tenant_id"]
        print(f"[Success] Created User {username}: {tenant_id}")

    # 3. Transfer Ownership of ALL Projects
    print(f"[Action] Transferring all projects to {username} ({tenant_id})...")
    
    # Update Projects
    db.client.table("utm_projects").update({
        "tenant_id": tenant_id,
        "client_id": client_id
    }).neq("project_id", "00000000-0000-0000-0000-000000000000").execute() 
    # neq is just a trick to select all if no better where clause
    
    # Update Objects (Assets)
    db.client.table("utm_objects").update({
        "tenant_id": tenant_id,
        "client_id": client_id
    }).neq("object_id", "00000000-0000-0000-0000-000000000000").execute()
    
    # Update Vault (if any)
    # CRITICAL FIX: Do NOT transfer all vault items. Only specific ones if needed.
    # For a clean demo, we do NOT want this user to inherit admin/system keys.
    # db.client.table("utm_provider_vault").update({
    #     "tenant_id": tenant_id
    # }).neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print("[Info] Skipped Vault transfer to ensure clean state.")

    print("[Success] Ownership setup complete.")
    print(f"User: {username}")
    print(f"Pass: {password_plain}")
    print(f"Client: {client_name}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(setup_demo_client())

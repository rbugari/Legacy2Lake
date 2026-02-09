
import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def test_endpoints():
    load_dotenv()
    db = SupabasePersistence()
    
    print("Testing Origins Logic:")
    res = db.client.table("utm_system_catalog").select("*").eq("type", "origin").eq("is_active", True).execute()
    origins = []
    for item in res.data:
        origins.append({
            "id": str(item.get("id") or item.get("tech_id")),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "enabled": True
        })
    print(json.dumps({"origins": origins}, indent=2))

    print("\nTesting Destinations Logic:")
    res = db.client.table("utm_system_catalog").select("*").eq("type", "destination").eq("is_active", True).execute()
    destinations = []
    for item in res.data:
        destinations.append({
            "id": str(item.get("id") or item.get("tech_id")),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "enabled": True
        })
    print(json.dumps({"destinations": destinations}, indent=2))

if __name__ == "__main__":
    asyncio.run(test_endpoints())

#!/usr/bin/env python3
"""Regenerate demo1 documentation export with latest code."""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE = os.getenv("API_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))

from services.persistence_service import SupabasePersistence


async def regenerate_demo1():
    """Regenerate documentation export for demo1."""
    
    # Step 1: Get project ID for demo1
    print("📌 Finding demo1 project...")
    db = SupabasePersistence()
    
    projects = db.client.table("utm_projects").select("project_id, name").eq("name", "demo1").execute()
    
    if not projects.data:
        print("❌ demo1 project not found.")
        print("Available projects:")
        all_projects = db.client.table("utm_projects").select("project_id, name").limit(10).execute()
        for p in all_projects.data:
            print(f"  - {p['name']}: {p['project_id']}")
        return
    
    project_id = projects.data[0]["project_id"]
    print(f"✅ Found demo1: {project_id}")
    
    # Step 2: Run triage to regenerate understanding
    print("\n📌 Running triage to regenerate understanding...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            triage_response = await client.post(
                f"{API_BASE}/api/projects/{project_id}/triage",
                headers={"Content-Type": "application/json"}
            )
            if triage_response.status_code != 200:
                print(f"⚠️  Triage response: {triage_response.status_code}")
                print(f"Response: {triage_response.text[:500]}")
            else:
                print("✅ Triage completed")
                
            # Step 3: Generate documentation export
            print("\n📌 Generating documentation export...")
            export_response = await client.get(
                f"{API_BASE}/api/projects/{project_id}/export/documentation",
                params={"format": "markdown"}
            )
            
            if export_response.status_code != 200:
                print(f"❌ Export failed: {export_response.status_code}")
                print(f"Response: {export_response.text[:500]}")
                return
            
            # Save markdown
            output_path = os.path.expanduser("~/Downloads/demo1_Export_Final.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(export_response.text)
            
            print(f"✅ Export saved to: {output_path}")
            
            # Print summary
            lines = export_response.text.split("\n")
            for line in lines[:15]:
                print(f"   {line}")
            
            print("\n📊 Export Summary:")
            print(f"   Total lines: {len(lines)}")
            
            # Check for problematic sections
            content = export_response.text.lower()
            if "source_db" in content or "destination_db" in content or ("unknown" in content and "extraction" in content):
                print("   ⚠️  WARNING: Found placeholder rules in output")
            else:
                print("   ✅ No placeholder rules detected")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(regenerate_demo1())

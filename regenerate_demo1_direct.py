#!/usr/bin/env python3
"""Regenerate demo1 documentation export directly using services."""

import os
import sys
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.understanding_service import UnderstandingService
from apps.api.services.documentation_export_service import DocumentationExportService


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
    
    # Step 2: Generate understanding
    print("\n📌 Generating understanding...")
    try:
        understanding_service = UnderstandingService(project_id=project_id)
        
        # Persist understanding so export reads the latest snapshot
        understanding = await understanding_service.rebuild()
        if not understanding:
            print("❌ Understanding generation failed")
            return
        
        print("✅ Understanding generated")
        
        # Step 3: Export to markdown
        print("\n📌 Generating documentation export...")
        export_service = DocumentationExportService()
        export_result = await export_service.export_full_documentation(
            project_id=project_id,
            format="markdown"
        )
        
        if not export_result or "content" not in export_result:
            print("❌ Export generation failed")
            return
        
        markdown = export_result["content"]
        
        # Save markdown
        output_path = Path.home() / "Downloads" / "demo1_Export_Final.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print(f"✅ Export saved to: {output_path}")
        
        # Print summary
        lines = markdown.split("\n")
        print("\n📊 Export Preview (first 25 lines):")
        for line in lines[:25]:
            print(f"   {line}")
        
        print(f"\n📊 Export Summary:")
        print(f"   Total lines: {len(lines)}")
        
        # Check for problematic sections
        content = markdown.lower()
        if "source_db" in content or "destination_db" in content:
            print("   ⚠️  WARNING: Found placeholder rules in output")
            # Find and print the lines
            for i, line in enumerate(lines):
                if "source_db" in line.lower() or "destination_db" in line.lower():
                    print(f"   Line {i}: {line[:80]}")
        else:
            print("   ✅ No placeholder rules (SOURCE_DB/DESTINATION_DB) detected")
            
        # Check extraction rules section
        print("\n📋 Extraction Rules Section:")
        in_extraction = False
        extraction_lines = []
        for line in lines:
            if "## Extraction Rules" in line:
                in_extraction = True
                continue
            if in_extraction:
                if line.startswith("##"):
                    break
                extraction_lines.append(line)
        
        if extraction_lines and any(l.strip() for l in extraction_lines):
            meaningful_lines = [l for l in extraction_lines if l.strip()]
            print(f"   Found {len(meaningful_lines)} meaningful lines")
            for line in meaningful_lines[:15]:
                print(f"   {line}")
        else:
            print("   (empty or minimal content - this is fine if no extraction rules)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(regenerate_demo1())

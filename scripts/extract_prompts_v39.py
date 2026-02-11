"""
Extract Prompts: Extract hardcoded templates from v3.9 cartridges to .md format

This script analyzes existing cartridges and extracts their hardcoded
generation logic into structured markdown prompts for v4.0.

Usage:
    python scripts/extract_prompts_v39.py              # Extract all cartridges
    python scripts/extract_prompts_v39.py pyspark      # Extract specific cartridge

Author: Development Team
Date: 2026-02-10
Version: 1.0.0
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re


def extract_template_from_function(func_node: ast.FunctionDef) -> str:
    """
    Extract template string from a function's return statement
    
    Looks for patterns like:
        return f"template..."
        return "template..."
        return template_var
    """
    template_parts = []
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.Return):
            if node.value:
                # Try to extract string from return
                if isinstance(node.value, ast.Constant):
                    return node.value.value
                elif isinstance(node.value, ast.JoinedStr):
                    # f-string
                    for value in node.value.values:
                        if isinstance(value, ast.Constant):
                            template_parts.append(str(value.value))
                        else:
                            template_parts.append("{...}")
    
    if template_parts:
        return ''.join(template_parts)
    
    return "[Template extraction failed - manual review needed]"


def create_prompt_markdown(tech_id: str, layer: str, docstring: str, template: str) -> str:
    """
    Create structured markdown prompt from extracted data
    
    Format:
        ---
        tech_id: pyspark
        layer: bronze
        version: 1.0.0
        ---
        
        # PySpark - Bronze Layer
        
        ## Purpose
        [docstring]
        
        ## Code Pattern
        [template]
    """
    version = "1.0.0"
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Clean docstring
    if not docstring or docstring.strip() == "":
        docstring = f"Generate {layer} layer code for {tech_id}"
    
    # Clean template
    template = template.strip() if template else "[No template found]"
    
    # Format markdown
    md = f"""---
tech_id: {tech_id}
layer: {layer}
version: {version}
created: {today}
status: extracted_from_v39
---

# {tech_id.title()} - {layer.title()} Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** {today}  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

{docstring}

---

## 📐 Code Pattern (Extracted from v3.9)

```python
{template}
```

---

## ⚠️ Migration Notes

**This prompt was auto-extracted from v3.9 hardcoded template.**

### TODO for v4.0:
- [ ] Review and enhance description
- [ ] Add examples and best practices
- [ ] Define mandatory requirements
- [ ] Add error handling guidelines
- [ ] Document performance considerations
- [ ] Add validation rules
- [ ] Test with Agent C

### Changes from v3.9:
- Converted from hardcoded Python to markdown prompt
- Needs AI agent instructions added
- Requires context variables documentation

---

## 📝 Version History

- **v1.0.0** ({today}): Extracted from v3.9 cartridge
"""
    
    return md


def extract_cartridge_prompts(cartridge_file: Path) -> Dict[str, str]:
    """
    Extract prompts from a single cartridge file
    
    Returns:
        Dict mapping layer name to markdown content
    """
    print(f"📖 Reading {cartridge_file.name}...")
    
    try:
        code = cartridge_file.read_text(encoding='utf-8')
        tree = ast.parse(code)
    except Exception as e:
        print(f"   ❌ Failed to parse: {e}")
        return {}
    
    prompts = {}
    tech_id = cartridge_file.stem.replace('_cartridge', '')
    
    # Look for generation methods
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for generate_* methods
            if node.name.startswith('generate_'):
                layer = node.name.replace('generate_', '')
                
                # Skip if not a layer method
                if layer not in ['bronze', 'silver', 'gold', 'staging', 'intermediate', 'marts']:
                    continue
                
                print(f"   🔍 Found: {node.name}()")
                
                # Extract docstring
                docstring = ast.get_docstring(node) or ""
                
                # Extract template
                template = extract_template_from_function(node)
                
                # Create markdown
                prompt_md = create_prompt_markdown(
                    tech_id=tech_id,
                    layer=layer,
                    docstring=docstring,
                    template=template
                )
                
                prompts[layer] = prompt_md
                print(f"   ✅ Extracted {layer} layer")
    
    return prompts


def extract_all_cartridges(specific_cartridge: Optional[str] = None):
    """
    Extract prompts from all cartridges in refinement/cartridges/
    
    Args:
        specific_cartridge: If provided, only extract this cartridge
    """
    cartridges_dir = Path("apps/api/services/refinement/cartridges")
    output_dir = Path("prompt_lab/cartridges")
    
    if not cartridges_dir.exists():
        print(f"❌ Cartridges directory not found: {cartridges_dir}")
        print("   Make sure you're running from project root")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Extracting prompts from v3.9 cartridges\n")
    
    total_prompts = 0
    total_cartridges = 0
    
    # Find cartridge files
    cartridge_files = list(cartridges_dir.glob("*_cartridge.py"))
    
    if specific_cartridge:
        cartridge_files = [
            f for f in cartridge_files 
            if f.stem.replace('_cartridge', '') == specific_cartridge
        ]
        
        if not cartridge_files:
            print(f"❌ Cartridge not found: {specific_cartridge}")
            return
    
    for cartridge_file in cartridge_files:
        tech_name = cartridge_file.stem.replace('_cartridge', '')
        
        print(f"┌─ {tech_name.upper()} " + "─" * (60 - len(tech_name)))
        
        prompts = extract_cartridge_prompts(cartridge_file)
        
        if not prompts:
            print("   ⚠️  No prompts extracted (no generate_* methods found)")
            print("└" + "─" * 64 + "\n")
            continue
        
        # Create tech-specific directory
        tech_dir = output_dir / tech_name
        tech_dir.mkdir(parents=True, exist_ok=True)
        
        # Write prompts
        for layer, prompt_md in prompts.items():
            output_file = tech_dir / f"{layer}_layer.md"
            output_file.write_text(prompt_md, encoding='utf-8')
            print(f"   💾 Saved: {output_file}")
        
        # Create README
        readme = tech_dir / "README.md"
        readme_content = f"""# {tech_name.title()} Cartridge Prompts

**Extracted from:** v3.9  
**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Status:** Draft

## Available Prompts

{"".join([f"- [{layer}_layer.md]({layer}_layer.md)\n" for layer in prompts.keys()])}

## Notes

These prompts were automatically extracted from v3.9 hardcoded templates.
They require review and enhancement for v4.0 production use.

## TODO

- [ ] Review and enhance all prompts
- [ ] Add Agent C instructions
- [ ] Add examples and test cases
- [ ] Document context variables
- [ ] Add validation rules
"""
        readme.write_text(readme_content, encoding='utf-8')
        
        total_prompts += len(prompts)
        total_cartridges += 1
        
        print(f"└─ Extracted {len(prompts)} prompts\n")
    
    print("─" * 70)
    print(f"✨ Extraction complete!")
    print(f"   📦 Cartridges processed: {total_cartridges}")
    print(f"   📝 Prompts extracted: {total_prompts}")
    print(f"   📁 Output directory: {output_dir.absolute()}")
    print("\n🔄 Next steps:")
    print("   1. Review extracted prompts in prompt_lab/cartridges/")
    print("   2. Enhance prompts with Agent instructions")
    print("   3. Run: python scripts/sync_prompts.py")


def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["help", "-h", "--help"]:
            print(__doc__)
            return
        else:
            # Extract specific cartridge
            extract_all_cartridges(specific_cartridge=sys.argv[1])
    else:
        # Extract all
        extract_all_cartridges()


if __name__ == "__main__":
    main()

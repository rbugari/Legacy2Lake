import argparse
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from apps.utm.cartridges.ssis.parser import SSISCartridge
from apps.utm.kernel.logic_mapper import LogicMapper
from apps.utm.cartridges.databricks.engine import DatabricksCartridge
from apps.utm.core.persistence import UTMPersistence

def main():
    parser = argparse.ArgumentParser(description="Legacy2Lake MVP Pipeline")
    parser.add_argument("--file", required=True, help="Path to source file (.dtsx)")
    parser.add_argument("--output", required=True, help="Path to output file (.py)")
    parser.add_argument("--project", default="Legacy2Lake_MVP", help="Project name in Metadata Store")
    parser.add_argument("--persist", action="store_true", help="Enable database persistence")
    parser.add_argument("--target", default="databricks", choices=["databricks", "snowflake"], help="Target technology (default: databricks)")
    args = parser.parse_args()
    
    print(f"[*] Starting Pipeline for {args.file} -> {args.target.upper()}")
    
    # Init Persistence
    db_agent = None
    project_id = None
    if args.persist:
        print(f"[*] [Persistence] Connecting to Metadata Store...")
        db_agent = UTMPersistence()
        project_id = db_agent.get_or_create_project(args.project)
        print(f"    - Project ID: {project_id}")
    
    # 1. Ingestion
    print(f"[*] [Ingestion] Parsing SSIS...")
    parser_agent = SSISCartridge()
    metadata = parser_agent.parse(args.file)
    print(f"    - Extracted {len(metadata.components)} components.")
    
    if db_agent and project_id:
        object_id = db_agent.save_object(project_id, metadata)
        print(f"    - Persisted Object ID: {object_id}")
    
    # 2. Kernel (Normalization)
    print(f"[*] [Kernel] Normalizing to Universal IR...")
    kernel_agent = LogicMapper()
    ir_steps = kernel_agent.normalize(metadata)
    print(f"    - Generated {len(ir_steps)} logical steps.")
    
    if db_agent and 'object_id' in locals() and object_id:
        db_agent.save_logical_steps(object_id, ir_steps)
        print(f"    - Persisted Logical Steps to DB.")
    
    # 3. Synthesis
    print(f"[*] [Synthesis] Generating {args.target.title()} Code...")
    
    if args.target == "databricks":
        cartridge_agent = DatabricksCartridge()
    elif args.target == "snowflake":
        # Placeholder for future implementation
        print("[WARN] Snowflake Cartridge not implemented yet. Falling back to stub.")
        # cartridge_agent = SnowflakeCartridge()
        sys.exit(1)
        
    context = {
        "source_tech": metadata.source_tech,
        "source_name": metadata.source_name,
        "target_tech": args.target
    }
    
    final_code = cartridge_agent.render(ir_steps, context)
    
    # 4. Output
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(final_code)
        
    print(f"[*] Success! Code saved to {args.output}")

if __name__ == "__main__":
    main()

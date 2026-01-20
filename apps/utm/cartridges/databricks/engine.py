from apps.utm.core.interfaces import BaseCartridge, LogicalStep
from typing import List
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime

class DatabricksCartridge(BaseCartridge):
    def __init__(self):
        # Setup Jinja2 Environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def render(self, ir_steps: List[LogicalStep], context: dict = None) -> str:
        if context is None:
            context = {
                "source_tech": "GENERIC",
                "source_name": "UNKNOWN"
            }
            
        code_blocks = []
        
        for step in ir_steps:
            template_name = ""
            if step.step_type == "READ":
                template_name = "op_read.j2"
            elif step.step_type == "WRITE":
                template_name = "op_write.j2"
            elif step.step_type == "TRANSFORM":
                template_name = "op_transform.j2"
            # ... handle others
            
            if template_name:
                tmpl = self.env.get_template(template_name)
                # Flatten params into variable context for the template
                render_ctx = {
                    "source_alias": step.ir_payload.get("source_alias", "df"),
                    "target": step.ir_payload.get("target"),
                    "params": step.ir_payload.get("params", {}),
                    "subtype": step.ir_payload.get("subtype")
                }
                
                rendered_code = tmpl.render(**render_ctx)
                code_blocks.append({
                    "step_order": step.step_order,
                    "step_type": step.step_type,
                    "code": rendered_code
                })
        
        # Render the final notebook structure
        base_tmpl = self.env.get_template("base_notebook.j2")
        final_code = base_tmpl.render(
            metadata=context,
            generated_at=datetime.now().isoformat(),
            code_blocks=code_blocks
        )
        
        return final_code

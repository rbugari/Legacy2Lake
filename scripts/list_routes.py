
import sys
import os
import json
from fastapi.routing import APIRoute

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

try:
    from apps.api.main import app
    
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods)
            })
            
    print(json.dumps(routes, indent=2))
except Exception as e:
    print(f"Error loading app: {e}")

import os
import sys
import json
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List

class ShiftLogger:
    def __init__(self):
        # Read from environment, default to False
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def log(self, message: str, level: str = "INFO", component: str = "System"):
        """Standard log format: [TIMESTAMP] [LEVEL] [COMPONENT] Message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [{component}] {message}")
        sys.stdout.flush()

    def info(self, message: str, component: str = "System"):
        self.log(message, "INFO", component)

    def warning(self, message: str, component: str = "System"):
        self.log(message, "WARNING", component)

    def error(self, message: str, component: str = "System", exc: Exception = None):
        """Logs error with optional traceback."""
        self.log(message, "ERROR", component)
        if exc:
            tb = traceback.format_exc()
            print(f"--- ERROR TRACEBACK ({component}) ---\n{tb}\n-------------------------")
            sys.stdout.flush()

    def http_log(self, method: str, path: str, status_code: int, duration_ms: float, client_id: str = "anonymous"):
        """Structured HTTP request logging."""
        msg = f"{method} {path} - {status_code} ({duration_ms:.2f}ms) [{client_id}]"
        self.log(msg, "INFO", "HTTP")

    def debug(self, message: str, component: str = "System", data: Any = None):
        """
        Logs verbose debug info ONLY if DEBUG_MODE is True.
        Handles JSON formatting for complex data structures.
        """
        if not self.debug_mode:
            return

        self.log(message, "DEBUG", component)
        
        if data:
            try:
                if isinstance(data, (dict, list)):
                    formatted_data = json.dumps(data, indent=2, default=str)
                    print(f"--- DEBUG DATA ({component}) ---\n{formatted_data}\n-------------------------")
                else:
                    print(f"--- DEBUG DATA ({component}) ---\n{str(data)}\n-------------------------")
            except Exception as e:
                print(f"--- DEBUG DATA ({component}) [Serialization Error] ---\n{str(data)}\n-------------------------")
            
            sys.stdout.flush()

    def llm_debug(self, agent_name: str):
        """Decorator to log LLM inputs and outputs in full detail."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.debug_mode:
                    return await func(*args, **kwargs)

                start_time = time.time()
                self.log(f"--- 🤖 LLM START: {agent_name} ---", "DEBUG", agent_name)
                
                # Log inputs (assuming args[0] is self, then node_data or similar)
                # For more robustness, we just log kwargs or important params
                if len(args) > 1:
                    self.debug(f"Input Data ({agent_name})", agent_name, args[1])

                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    self.log(f"--- ✅ LLM SUCCESS: {agent_name} ({duration:.2f}s) ---", "DEBUG", agent_name)
                    # Use a truncated view for the result if it's too big, or just log the keys
                    if isinstance(result, dict):
                         self.debug(f"Response Summary ({agent_name})", agent_name, {k: (str(v)[:100] + "...") if isinstance(v, str) and len(str(v)) > 100 else v for k,v in result.items()})
                    else:
                         self.debug(f"Response ({agent_name})", agent_name, result)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.error(f"--- ❌ LLM FAILED: {agent_name} ({duration:.2f}s) --- Error: {str(e)}", agent_name)
                    raise e
            return wrapper
        return decorator

# Singleton instance for easy import
logger = ShiftLogger()


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worklow Runner
Persistent worker process that executes nodes on demand.
Reads JSON commands from stdin and writes results to stdout.
"""
import sys
import json
import importlib.util
import traceback
from pathlib import Path

def load_module_from_file(file_path):
    """Dynamically load a module from a file path"""
    try:
        module_name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        raise ImportError(f"Failed to load module {file_path}: {e}")

def handle_run_node(command):
    """Handle run_node command"""
    try:
        script_path = command.get("script_path")
        input_data = command.get("input_data", {})
        
        if not script_path:
            return {"success": False, "error": "script_path is required"}
            
        # Load the node module
        module = load_module_from_file(script_path)
        if not module:
            return {"success": False, "error": f"Could not load module from {script_path}"}
            
        if not hasattr(module, "execute"):
            return {"success": False, "error": f"Module {script_path} does not have an execute function"}
            
        # Execute the node logic
        output_data = module.execute(input_data)
        
        return {
            "success": True, 
            "data": output_data
        }
    except Exception as e:
        # Capture full traceback
        tb = traceback.format_exc()
        return {
            "success": False, 
            "error": str(e),
            "traceback": tb
        }

def main():
    """Main loop"""
    # Print ready signal
    print("READY", flush=True)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            command = json.loads(line)
            cmd_type = command.get("type")
            
            if cmd_type == "exit":
                break
                
            elif cmd_type == "run_node":
                result = handle_run_node(command)
                
                # Write result
                print("###JSON_OUTPUT###")
                print(json.dumps(result, ensure_ascii=False))
                print("###JSON_OUTPUT_END###", flush=True)
                
            else:
                error_result = {"success": False, "error": f"Unknown command: {cmd_type}"}
                print("###JSON_OUTPUT###")
                print(json.dumps(error_result, ensure_ascii=False))
                print("###JSON_OUTPUT_END###", flush=True)
                
        except json.JSONDecodeError:
            error_result = {"success": False, "error": "Invalid JSON input"}
            print("###JSON_OUTPUT###")
            print(json.dumps(error_result, ensure_ascii=False))
            print("###JSON_OUTPUT_END###", flush=True)
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            print("###JSON_OUTPUT###")
            print(json.dumps(error_result, ensure_ascii=False))
            print("###JSON_OUTPUT_END###", flush=True)

if __name__ == "__main__":
    main()

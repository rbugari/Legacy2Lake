import os
import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
from .storage_provider import StorageProvider

class R2StorageProvider(StorageProvider):
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str, public_url: str = None):
        self.bucket_name = bucket_name
        self.public_url = public_url
        
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto" # Cloudflare R2 uses 'auto'
        )

    def ensure_directory(self, path: str) -> str:
        # S3 has flat namespace; "directories" are just prefixes.
        # We don't need to physically create them, but we return the sanitized prefix.
        return path.replace("\\", "/").rstrip("/") + "/"

    def save_file(self, path: str, content: Any, is_binary: bool = False) -> str:
        key = path.replace("\\", "/")
        
        # Boto3 expects bytes or string
        if not is_binary and isinstance(content, str):
            body = content.encode('utf-8')
        else:
            body = content

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body
        )
        return key

    def read_file(self, path: str, is_binary: bool = False) -> Any:
        key = path.replace("\\", "/")
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            body = response['Body'].read()
            if is_binary:
                return body
            return body.decode('utf-8')
        except self.client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"R2 Read Error ({path}): {e}")
            return None

    def delete_file(self, path: str) -> bool:
        key = path.replace("\\", "/")
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"R2 Delete Error ({path}): {e}")
            return False

    def delete_directory(self, path: str) -> bool:
        prefix = path.replace("\\", "/").rstrip("/") + "/"
        # List and delete all objects with this prefix
        try:
            # We need pagination if many objects
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    # Batch delete (max 1000)
                    for i in range(0, len(objects), 1000):
                        batch = objects[i:i+1000]
                        self.client.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={'Objects': batch}
                        )
            return True
        except Exception as e:
            print(f"R2 Delete Directory Error ({prefix}): {e}")
            return False

    def list_files(self, path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        prefix = path.replace("\\", "/").rstrip("/") + "/"
        if prefix == "/": prefix = "" # Root
        
        # S3 listing is flat. To simulate a tree structure (nested dicts) from a flat list logic
        # is complex. Alternatively, we just return the FLATTENED list or try to build the tree?
        # The frontend expects a *nested* structure: "children": [ ... ]
        
        # Strategy: List ALL objects under prefix, then build the tree in memory.
        # Note: This might be slow for massive buckets, but for "project solutions" it should be fine.
        
        items = []
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Calculate relative path from the requested 'path'
                        if not key.startswith(prefix):
                            continue
                            
                        # e.g. prefix="proj1/", key="proj1/src/main.py" -> rel="src/main.py"
                        rel_path = key[len(prefix):]
                        if not rel_path: continue # The folder marker itself
                        
                        items.append({
                            "key": key,
                            "rel_path": rel_path,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].timestamp()
                        })
        except Exception as e:
            print(f"R2 List Error: {e}")
            return []

        # Build Tree
        # The PersistenceService.get_project_files interface expects a specific recursive structure.
        return self._build_tree(items, root_prefix=prefix)

    def _build_tree(self, flat_items: List[Dict], root_prefix: str) -> List[Dict[str, Any]]:
        # Root node container
        root_children = []
        
        # We need to implicitly create folder nodes
        # Map: "folder_path" -> { node_dict }
        nodes_map = {} 
        
        for item in flat_items:
            parts = item['rel_path'].strip("/").split("/")
            
            # walk parts to ensure directory nodes exist
            current_path = ""
            current_list = root_children
            
            for i, part in enumerate(parts):
                is_file = (i == len(parts) - 1)
                
                # Check if we already have this node in current_list
                found = next((x for x in current_list if x["name"] == part), None)
                
                if not found:
                    if is_file:
                        node = {
                            "name": part,
                            "path": item["key"], # Full S3 Key
                            "type": "file",
                            "size": item["size"],
                            "last_modified": item["last_modified"]
                        }
                    else:
                        node = {
                            "name": part,
                            "path": root_prefix + "/".join(parts[:i+1]), # Logical folder path
                            "type": "folder",
                            "last_modified": 0,
                            "children": []
                        }
                    
                    current_list.append(node)
                    if not is_file:
                        current_list = node["children"]
                else:
                    if not is_file:
                        current_list = found["children"]

        # Basic Sort
        def recursive_sort(children):
            children.sort(key=lambda x: (x["type"] != "folder", x["name"]))
            for child in children:
                if "children" in child:
                    recursive_sort(child["children"])
                    
        recursive_sort(root_children)
        return root_children

    def exists(self, path: str) -> bool:
        key = path.replace("\\", "/")
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False

    def resolve_absolute_path(self, path: str) -> str:
        # Return Key (or signed URL if needed, but Key is safer for internal ref)
        return path.replace("\\", "/")

    def generate_signed_url(self, path: str, expiration: int = 3600) -> Optional[str]:
        """Generates a pre-signed URL for direct download from R2."""
        key = path.replace("\\", "/")
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"R2 Signed URL Error ({path}): {e}")
            return None

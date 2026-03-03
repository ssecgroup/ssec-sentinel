#!/usr/bin/env python3
"""
ssec-Sentinel - Clean Empty Files
Finds and optionally deletes empty files
"""

import os
import sys
from pathlib import Path

def find_empty_files(directory):
    """Find all empty files"""
    empty_files = []
    exclude_dirs = ['__pycache__', '.git', 'venv', 'env', '__pycache__']
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) == 0:
                empty_files.append(file_path)
    
    return empty_files

def main():
    directory = os.getcwd()
    print(f"\n🔍 Scanning: {directory}")
    
    empty_files = find_empty_files(directory)
    
    if not empty_files:
        print("✅ No empty files found!")
        return
    
    print(f"\n⚠️  Found {len(empty_files)} empty files:\n")
    for f in empty_files:
        print(f"  📄 {f}")
    
    print(f"\n{'='*60}")
    response = input(f"\n❓ Delete these {len(empty_files)} files? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        deleted = 0
        for f in empty_files:
            try:
                os.remove(f)
                print(f"✅ Deleted: {f}")
                deleted += 1
            except Exception as e:
                print(f"❌ Error deleting {f}: {e}")
        
        print(f"\n✅ Deleted {deleted} files")
    else:
        print("❌ No files deleted")

if __name__ == "__main__":
    main()

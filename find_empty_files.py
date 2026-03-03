#!/usr/bin/env python3
"""
ssec-Sentinel - Empty File Finder
Scans directory and identifies empty files (0 bytes)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def find_empty_files(directory: str, exclude_dirs=None, exclude_extensions=None):
    """
    Find all empty files (0 bytes) in directory recursively
    
    Args:
        directory: Root directory to scan
        exclude_dirs: List of directory names to exclude
        exclude_extensions: List of file extensions to exclude
    """
    if exclude_dirs is None:
        exclude_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules', '__pycache__']
    
    if exclude_extensions is None:
        exclude_extensions = ['.pyc', '.log', '.tmp', '.cache']
    
    empty_files = []
    total_files = 0
    total_size = 0
    
    print(f"\n{'='*60}")
    print(f"🔍 Scanning directory: {directory}")
    print(f"{'='*60}\n")
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip excluded extensions
            if any(file.endswith(ext) for ext in exclude_extensions):
                continue
            
            try:
                file_size = os.path.getsize(file_path)
                total_files += 1
                total_size += file_size
                
                if file_size == 0:
                    empty_files.append({
                        'path': file_path,
                        'name': file,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
            except OSError as e:
                print(f"⚠️  Error accessing {file_path}: {e}")
    
    return empty_files, total_files, total_size

def format_size(size_bytes):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def main():
    # Get current directory or from command line
    if len(sys.argv) > 1:
        scan_dir = sys.argv[1]
    else:
        scan_dir = os.getcwd()
    
    # Verify directory exists
    if not os.path.exists(scan_dir):
        print(f"❌ Error: Directory '{scan_dir}' does not exist")
        sys.exit(1)
    
    # Find empty files
    empty_files, total_files, total_size = find_empty_files(scan_dir)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"📊 SCAN RESULTS")
    print(f"{'='*60}")
    print(f"📁 Total files scanned: {total_files:,}")
    print(f"💾 Total size: {format_size(total_size)}")
    print(f"🔄 Average file size: {format_size(total_size/total_files if total_files > 0 else 0)}")
    print(f"\n{'='*60}")
    
    if empty_files:
        print(f"⚠️  Found {len(empty_files)} empty files:\n")
        
        # Group by directory
        by_dir = {}
        for ef in empty_files:
            dir_name = os.path.dirname(ef['path'])
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(ef)
        
        # Print by directory
        for dir_name, files in sorted(by_dir.items()):
            rel_path = os.path.relpath(dir_name, scan_dir)
            print(f"\n📂 {rel_path}/")
            for f in sorted(files, key=lambda x: x['name']):
                modified = f['modified'].strftime('%Y-%m-%d %H:%M')
                print(f"   📄 {f['name']:40} (modified: {modified})")
        
        # Summary by file type
        print(f"\n{'='*60}")
        print("📈 Empty Files by Extension:")
        ext_count = {}
        for ef in empty_files:
            ext = os.path.splitext(ef['name'])[1] or '(no extension)'
            ext_count[ext] = ext_count.get(ext, 0) + 1
        
        for ext, count in sorted(ext_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext:15}: {count} files")
        
        # Ask if user wants to delete
        print(f"\n{'='*60}")
        response = input(f"\n❓ Do you want to delete these {len(empty_files)} empty files? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            deleted = 0
            failed = 0
            for ef in empty_files:
                try:
                    os.remove(ef['path'])
                    print(f"✅ Deleted: {ef['path']}")
                    deleted += 1
                except OSError as e:
                    print(f"❌ Failed to delete {ef['path']}: {e}")
                    failed += 1
            
            print(f"\n{'='*60}")
            print(f"🗑️  Deleted {deleted} files, {failed} failed")
        else:
            print("❌ No files deleted")
            
    else:
        print("✅ No empty files found!")
        print("\n🎉 Your project is clean!")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

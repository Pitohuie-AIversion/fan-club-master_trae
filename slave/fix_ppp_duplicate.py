#!/usr/bin/env python3
"""
Find and fix ppp-cell-iface.baud-rate duplicate configuration
"""

import os
import json
import shutil
from pathlib import Path

def find_ppp_baud_rate_configs(mbed_os_path):
    """Find all files containing ppp-cell-iface.baud-rate setting"""
    print(f"Searching for ppp-cell-iface.baud-rate in: {mbed_os_path}")
    
    found_files = []
    
    # Find all mbed_lib.json files
    for root, dirs, files in os.walk(mbed_os_path):
        if 'mbed_lib.json' in files:
            lib_file = os.path.join(root, 'mbed_lib.json')
            try:
                with open(lib_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'config' in data:
                    if 'ppp-cell-iface.baud-rate' in data['config']:
                        found_files.append(lib_file)
                        print(f"  Found in: {lib_file}")
                        
            except Exception as e:
                print(f"  Error reading {lib_file}: {e}")
    
    return found_files

def remove_ppp_baud_rate_from_secondary_files(files_with_setting):
    """Remove ppp-cell-iface.baud-rate from all but the primary file"""
    if len(files_with_setting) <= 1:
        print("No duplicates found")
        return 0
    
    # Keep the first one (usually the main one), remove from others
    primary_file = files_with_setting[0]
    secondary_files = files_with_setting[1:]
    
    print(f"\nKeeping setting in: {primary_file}")
    print(f"Removing from {len(secondary_files)} other files:")
    
    removed_count = 0
    for lib_file in secondary_files:
        try:
            # Backup original
            backup_file = lib_file + '.backup_ppp_fix'
            if not os.path.exists(backup_file):
                shutil.copy2(lib_file, backup_file)
            
            # Read and modify
            with open(lib_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'config' in data and 'ppp-cell-iface.baud-rate' in data['config']:
                del data['config']['ppp-cell-iface.baud-rate']
                print(f"  Removed from: {lib_file}")
                
                # If config section is now empty, remove it
                if not data['config']:
                    del data['config']
                
                # Write back
                with open(lib_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                removed_count += 1
                
        except Exception as e:
            print(f"  Error processing {lib_file}: {e}")
    
    return removed_count

def disable_cellular_test_directories(mbed_os_path):
    """Disable cellular test directories that might contain conflicting configs"""
    print(f"\nDisabling cellular test directories...")
    
    cellular_test_paths = [
        "connectivity/cellular",
        "connectivity/netsocket", 
        "connectivity/lwipstack",
        "features/cellular"
    ]
    
    disabled_count = 0
    for test_path in cellular_test_paths:
        full_path = os.path.join(mbed_os_path, test_path)
        if os.path.exists(full_path):
            # Look for test subdirectories
            for root, dirs, files in os.walk(full_path):
                for dir_name in dirs[:]:
                    if 'test' in dir_name.lower():
                        test_dir = os.path.join(root, dir_name)
                        backup_dir = test_dir + '.disabled_for_build'
                        if not os.path.exists(backup_dir):
                            try:
                                shutil.move(test_dir, backup_dir)
                                print(f"  Disabled: {test_dir}")
                                disabled_count += 1
                                dirs.remove(dir_name)  # Don't walk into moved directory
                            except Exception as e:
                                print(f"  Error disabling {test_dir}: {e}")
    
    return disabled_count

def main():
    # Read mbed-os path from mbed-os.lib
    mbed_os_lib_path = 'mbed-os.lib'
    if not os.path.exists(mbed_os_lib_path):
        print("Error: mbed-os.lib file not found")
        return
    
    with open(mbed_os_lib_path, 'r') as f:
        mbed_os_path = f.read().strip()
    
    if not os.path.exists(mbed_os_path):
        print(f"Error: mbed-os directory not found: {mbed_os_path}")
        return
    
    print("=== Fixing ppp-cell-iface.baud-rate duplicate configuration ===")
    
    # Step 1: Find all files with the setting
    files_with_setting = find_ppp_baud_rate_configs(mbed_os_path)
    
    # Step 2: Remove from secondary files
    removed_count = remove_ppp_baud_rate_from_secondary_files(files_with_setting)
    
    # Step 3: Disable cellular test directories
    disabled_count = disable_cellular_test_directories(mbed_os_path)
    
    print(f"\n=== Fix completed ===")
    print(f"Removed ppp-cell-iface.baud-rate from {removed_count} files")
    print(f"Disabled {disabled_count} test directories")
    
    print("\n=== Next steps ===")
    print("Try running: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Fix all duplicate configuration settings in mbed-os library by removing problematic files
"""

import os
import json
import shutil
from pathlib import Path
from collections import defaultdict

def backup_and_remove_problematic_configs(mbed_os_path):
    """Remove known problematic configuration files that cause duplicates"""
    print(f"Removing problematic configuration files from: {mbed_os_path}")
    
    # List of problematic directories/files to disable
    problematic_paths = [
        # Test directories that cause conflicts
        "tools/test",
        "tools/unittests", 
        # Storage configurations that have duplicates
        "storage/kvstore/kv_config/tdb_external",
        "storage/kvstore/kv_config/tdb_external_no_rbp",
        # Connectivity configurations that may conflict
        "connectivity/cellular/tests",
        "connectivity/netsocket/tests",
        # Platform test configurations
        "platform/tests",
        # RTOS test configurations  
        "rtos/tests",
        # Features test configurations
        "features/tests"
    ]
    
    removed_count = 0
    for prob_path in problematic_paths:
        full_path = os.path.join(mbed_os_path, prob_path)
        if os.path.exists(full_path):
            # Create backup
            backup_path = full_path + ".disabled_for_build"
            if not os.path.exists(backup_path):
                try:
                    if os.path.isdir(full_path):
                        shutil.move(full_path, backup_path)
                        print(f"  Disabled directory: {prob_path}")
                    else:
                        shutil.move(full_path, backup_path)
                        print(f"  Disabled file: {prob_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"  Error disabling {prob_path}: {e}")
    
    return removed_count

def remove_specific_duplicate_settings(mbed_os_path):
    """Remove specific duplicate settings from mbed_lib.json files"""
    print(f"\nRemoving specific duplicate settings...")
    
    # Known duplicate settings to remove
    duplicate_settings = [
        "storage_tdb_external.rbp_internal_size",
        "storage_tdb_external_no_rbp.blockdevice", 
        "ppp-cell-iface.baud-rate",
        "enable-cell",
        "port-configuration-variant"
    ]
    
    fixed_files = []
    
    # Find all mbed_lib.json files
    for root, dirs, files in os.walk(mbed_os_path):
        if 'mbed_lib.json' in files:
            lib_file = os.path.join(root, 'mbed_lib.json')
            try:
                with open(lib_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                modified = False
                if 'config' in data:
                    for setting in duplicate_settings:
                        if setting in data['config']:
                            # Only remove from non-primary locations
                            if ('test' in root.lower() or 
                                'kvstore' in root.lower() or
                                'cellular' in root.lower()):
                                del data['config'][setting]
                                modified = True
                                print(f"  Removed {setting} from {lib_file}")
                
                if modified:
                    # Backup original
                    backup_file = lib_file + '.backup_duplicate_removal'
                    if not os.path.exists(backup_file):
                        shutil.copy2(lib_file, backup_file)
                    
                    # Write modified file
                    with open(lib_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    fixed_files.append(lib_file)
                    
            except Exception as e:
                print(f"  Error processing {lib_file}: {e}")
    
    return len(fixed_files)

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
    
    print("=== Aggressive mbed-os duplicate configuration fix ===")
    
    # Step 1: Remove problematic directories/files
    print("\n=== Step 1: Removing problematic directories ===")
    removed_count = backup_and_remove_problematic_configs(mbed_os_path)
    
    # Step 2: Remove specific duplicate settings
    print("\n=== Step 2: Removing specific duplicate settings ===")
    fixed_count = remove_specific_duplicate_settings(mbed_os_path)
    
    print(f"\n=== Fix completed ===")
    print(f"Disabled {removed_count} problematic directories/files")
    print(f"Fixed {fixed_count} configuration files")
    
    print("\n=== Next steps ===")
    print("Try running: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("\nIf you need to restore disabled components later:")
    print("Look for .disabled_for_build and .backup_duplicate_removal files")

if __name__ == '__main__':
    main()
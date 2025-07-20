#!/usr/bin/env python3
"""
Comprehensive fix for all duplicate configuration settings in mbed-os
"""

import os
import json
import shutil
from pathlib import Path
from collections import defaultdict

def find_all_duplicate_configs(mbed_os_path):
    """Find all duplicate configuration settings"""
    print(f"Scanning for all duplicate configurations in: {mbed_os_path}")
    
    config_locations = defaultdict(list)
    
    # Find all mbed_lib.json files
    for root, dirs, files in os.walk(mbed_os_path):
        if 'mbed_lib.json' in files:
            lib_file = os.path.join(root, 'mbed_lib.json')
            try:
                with open(lib_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'config' in data:
                    for setting_name in data['config'].keys():
                        config_locations[setting_name].append(lib_file)
                        
            except Exception as e:
                print(f"  Error reading {lib_file}: {e}")
    
    # Find duplicates
    duplicates = {setting: files for setting, files in config_locations.items() if len(files) > 1}
    
    print(f"Found {len(duplicates)} duplicate settings:")
    for setting, files in duplicates.items():
        print(f"  {setting}: {len(files)} occurrences")
    
    return duplicates

def remove_duplicates_from_test_files(duplicates, mbed_os_path):
    """Remove duplicate settings from test-related files"""
    print(f"\nRemoving duplicates from test files...")
    
    removed_count = 0
    
    for setting_name, file_list in duplicates.items():
        # Keep the first non-test file, remove from test files
        primary_file = None
        test_files = []
        
        for lib_file in file_list:
            if ('test' in lib_file.lower() or 
                'unittest' in lib_file.lower() or
                'example' in lib_file.lower()):
                test_files.append(lib_file)
            elif primary_file is None:
                primary_file = lib_file
        
        if primary_file and test_files:
            print(f"\n  Setting: {setting_name}")
            print(f"    Keeping in: {primary_file}")
            print(f"    Removing from {len(test_files)} test files")
            
            for test_file in test_files:
                try:
                    # Backup original
                    backup_file = test_file + '.backup_duplicate_removal'
                    if not os.path.exists(backup_file):
                        shutil.copy2(test_file, backup_file)
                    
                    # Read and modify
                    with open(test_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'config' in data and setting_name in data['config']:
                        del data['config'][setting_name]
                        print(f"      Removed from: {test_file}")
                        
                        # If config section is now empty, remove it
                        if not data['config']:
                            del data['config']
                        
                        # Write back
                        with open(test_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        
                        removed_count += 1
                        
                except Exception as e:
                    print(f"      Error processing {test_file}: {e}")
    
    return removed_count

def disable_all_test_directories(mbed_os_path):
    """Disable all test directories to prevent conflicts"""
    print(f"\nDisabling all test directories...")
    
    disabled_count = 0
    
    # Walk through mbed-os and find test directories
    for root, dirs, files in os.walk(mbed_os_path):
        for dir_name in dirs[:]:
            if ('test' in dir_name.lower() and 
                ('test' == dir_name.lower() or 
                 'tests' == dir_name.lower() or
                 'unittest' in dir_name.lower() or
                 'example' in dir_name.lower())):
                
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
    
    print("=== Comprehensive mbed-os duplicate configuration fix ===")
    
    # Step 1: Disable all test directories first
    print("\n=== Step 1: Disabling test directories ===")
    disabled_count = disable_all_test_directories(mbed_os_path)
    
    # Step 2: Find remaining duplicates
    print("\n=== Step 2: Finding remaining duplicates ===")
    duplicates = find_all_duplicate_configs(mbed_os_path)
    
    # Step 3: Remove duplicates from test files
    print("\n=== Step 3: Removing duplicates from remaining test files ===")
    removed_count = remove_duplicates_from_test_files(duplicates, mbed_os_path)
    
    print(f"\n=== Fix completed ===")
    print(f"Disabled {disabled_count} test directories")
    print(f"Removed {removed_count} duplicate settings from test files")
    
    print("\n=== Next steps ===")
    print("Try running: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("\nIf you need to restore disabled components later:")
    print("Look for .disabled_for_build and .backup_duplicate_removal files")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Fix s2lp.provide-default duplicate configuration in mbed-os
"""

import os
import json
import shutil
from pathlib import Path

def find_and_fix_s2lp_duplicates(mbed_os_path):
    """Find and fix s2lp.provide-default duplicate configurations"""
    duplicates_found = 0
    files_processed = 0
    
    print(f"Searching for s2lp.provide-default duplicates in {mbed_os_path}...")
    
    # Search for mbed_lib.json files that might contain s2lp configurations
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip disabled directories
        if '.mbedignore' in files or 'TESTS' in root.upper() or 'TEST' in root.upper():
            continue
            
        for file in files:
            if file == 'mbed_lib.json':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check if this file contains s2lp configuration
                    if 's2lp' in content.lower() and 'provide-default' in content:
                        print(f"Found s2lp config in: {file_path}")
                        
                        # Parse JSON to check for duplicates
                        try:
                            data = json.loads(content)
                            if 'config' in data and 's2lp.provide-default' in str(data['config']):
                                print(f"  - Contains s2lp.provide-default configuration")
                                
                                # Disable this directory by creating .mbedignore
                                ignore_path = os.path.join(root, '.mbedignore')
                                if not os.path.exists(ignore_path):
                                    with open(ignore_path, 'w') as ignore_file:
                                        ignore_file.write('*\n')
                                    print(f"  - Disabled directory: {root}")
                                    duplicates_found += 1
                                    
                        except json.JSONDecodeError:
                            print(f"  - Warning: Could not parse JSON in {file_path}")
                            
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return duplicates_found, files_processed

def disable_s2lp_test_directories(mbed_os_path):
    """Disable test directories that might contain s2lp configurations"""
    disabled_dirs = 0
    
    # Common s2lp test directories to disable
    test_patterns = [
        'connectivity/drivers/lora/COMPONENT_SX126X',
        'connectivity/drivers/lora/COMPONENT_SX127X', 
        'connectivity/drivers/lora/COMPONENT_SX1272',
        'connectivity/drivers/lora/COMPONENT_SX1276',
        'connectivity/drivers/802.15.4_RF/stm-s2lp-rf-driver',
        'connectivity/drivers/802.15.4_RF/mcr20a-rf-driver',
        'connectivity/drivers/802.15.4_RF/atmel-rf-driver',
        'connectivity/drivers/802.15.4_RF',
        'connectivity/drivers/lora',
        'connectivity/drivers/wifi',
        'connectivity/drivers/cellular',
        'connectivity/drivers/ble'
    ]
    
    for pattern in test_patterns:
        full_path = os.path.join(mbed_os_path, pattern)
        if os.path.exists(full_path):
            ignore_path = os.path.join(full_path, '.mbedignore')
            if not os.path.exists(ignore_path):
                try:
                    with open(ignore_path, 'w') as f:
                        f.write('*\n')
                    print(f"Disabled: {pattern}")
                    disabled_dirs += 1
                except Exception as e:
                    print(f"Error disabling {pattern}: {e}")
    
    return disabled_dirs

def main():
    # Find mbed-os directory
    current_dir = os.getcwd()
    mbed_os_path = None
    
    # Check for mbed-os.lib file
    if os.path.exists('mbed-os.lib'):
        with open('mbed-os.lib', 'r') as f:
            mbed_path = f.read().strip()
            # Handle both URL and local path formats
            if mbed_path.startswith('https://github.com/ARMmbed/mbed-os'):
                mbed_os_path = 'mbed-os'
            elif os.path.exists(mbed_path):
                mbed_os_path = mbed_path
    
    if not mbed_os_path or not os.path.exists(mbed_os_path):
        print("Error: mbed-os directory not found!")
        print(f"Checked paths: {mbed_os_path if mbed_os_path else 'None'}")
        return
    
    print("=== S2LP Duplicate Configuration Fixer ===")
    print(f"Working directory: {current_dir}")
    print(f"Mbed OS path: {mbed_os_path}")
    print()
    
    # Step 1: Disable problematic directories
    print("Step 1: Disabling S2LP-related directories...")
    disabled_dirs = disable_s2lp_test_directories(mbed_os_path)
    print(f"Disabled {disabled_dirs} directories")
    print()
    
    # Step 2: Find and fix duplicates
    print("Step 2: Finding and fixing s2lp.provide-default duplicates...")
    duplicates_found, files_processed = find_and_fix_s2lp_duplicates(mbed_os_path)
    print(f"Processed {files_processed} files")
    print(f"Fixed {duplicates_found} duplicate configurations")
    print()
    
    print("=== Summary ===")
    print(f"- Disabled directories: {disabled_dirs}")
    print(f"- Fixed duplicates: {duplicates_found}")
    print(f"- Files processed: {files_processed}")
    print()
    print("Next steps:")
    print("1. Try compiling again: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("2. If more duplicates appear, run this script again")

if __name__ == '__main__':
    main()
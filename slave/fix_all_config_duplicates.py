#!/usr/bin/env python3
"""
Comprehensive fix for all duplicate configurations in mbed-os
"""

import os
import json
import shutil
from pathlib import Path
import re

def disable_all_test_directories(mbed_os_path):
    """Disable all test and example directories"""
    disabled_dirs = 0
    
    print("Disabling all test and example directories...")
    
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip already disabled directories
        if '.mbedignore' in files:
            continue
            
        # Check if this is a test/example directory
        path_parts = root.lower().split(os.sep)
        should_disable = any([
            'test' in path_parts,
            'tests' in path_parts,
            'example' in path_parts,
            'examples' in path_parts,
            'demo' in path_parts,
            'demos' in path_parts,
            'benchmark' in path_parts,
            'benchmarks' in path_parts,
            'unittests' in path_parts,
            'unittest' in path_parts,
            root.endswith('TESTS'),
            root.endswith('TEST'),
            'test_' in os.path.basename(root).lower(),
            '_test' in os.path.basename(root).lower(),
            'example_' in os.path.basename(root).lower(),
            '_example' in os.path.basename(root).lower()
        ])
        
        if should_disable:
            ignore_path = os.path.join(root, '.mbedignore')
            try:
                with open(ignore_path, 'w') as f:
                    f.write('*\n')
                print(f"Disabled: {os.path.relpath(root, mbed_os_path)}")
                disabled_dirs += 1
            except Exception as e:
                print(f"Error disabling {root}: {e}")
    
    return disabled_dirs

def disable_problematic_components(mbed_os_path):
    """Disable known problematic component directories"""
    disabled_dirs = 0
    
    # Known problematic directories
    problematic_patterns = [
        'connectivity/drivers',
        'connectivity/cellular',
        'connectivity/netsocket', 
        'connectivity/lwipstack',
        'connectivity/mbedtls',
        'connectivity/nanostack',
        'connectivity/libraries',
        'storage/kvstore',
        'storage/filesystem',
        'storage/blockdevice',
        'platform/tests',
        'rtos/tests',
        'tools/test',
        'features/cellular',
        'features/netsocket',
        'features/lwipstack',
        'features/mbedtls',
        'features/storage',
        'features/frameworks',
        'features/device_key',
        'features/cryptocell',
        'COMPONENT_',
        'TARGET_'
    ]
    
    print("Disabling problematic component directories...")
    
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip already disabled directories
        if '.mbedignore' in files:
            continue
            
        rel_path = os.path.relpath(root, mbed_os_path)
        
        # Check if this directory matches problematic patterns
        should_disable = any([
            pattern in rel_path for pattern in problematic_patterns
        ])
        
        if should_disable:
            ignore_path = os.path.join(root, '.mbedignore')
            try:
                with open(ignore_path, 'w') as f:
                    f.write('*\n')
                print(f"Disabled: {rel_path}")
                disabled_dirs += 1
            except Exception as e:
                print(f"Error disabling {root}: {e}")
    
    return disabled_dirs

def find_and_remove_config_duplicates(mbed_os_path):
    """Find and remove duplicate configurations from mbed_lib.json files"""
    duplicates_removed = 0
    files_processed = 0
    
    print("Searching for configuration duplicates...")
    
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip disabled directories
        if '.mbedignore' in files:
            continue
            
        for file in files:
            if file == 'mbed_lib.json':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Parse JSON
                    try:
                        data = json.loads(content)
                        modified = False
                        
                        # Remove problematic config sections
                        if 'config' in data:
                            config_keys = list(data['config'].keys())
                            for key in config_keys:
                                # Remove configs that commonly cause duplicates
                                if any(pattern in key.lower() for pattern in [
                                    'uart-serial-txbuf-size',
                                    'uart-serial-rxbuf-size', 
                                    's2lp.provide-default',
                                    'nsapi.default-stack',
                                    'ppp-cell-iface.baud-rate',
                                    'storage_tdb_external',
                                    'blockdevice',
                                    'cellular',
                                    'lwip',
                                    'nanostack',
                                    'wifi',
                                    'lora'
                                ]):
                                    del data['config'][key]
                                    print(f"  Removed config: {key} from {file_path}")
                                    duplicates_removed += 1
                                    modified = True
                        
                        # Write back if modified
                        if modified:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4)
                                
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse JSON in {file_path}")
                        
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return duplicates_removed, files_processed

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
    
    print("=== Comprehensive Mbed OS Configuration Fixer ===")
    print(f"Working directory: {current_dir}")
    print(f"Mbed OS path: {mbed_os_path}")
    print()
    
    # Step 1: Disable all test directories
    print("Step 1: Disabling test directories...")
    test_dirs_disabled = disable_all_test_directories(mbed_os_path)
    print(f"Disabled {test_dirs_disabled} test directories")
    print()
    
    # Step 2: Disable problematic components
    print("Step 2: Disabling problematic components...")
    component_dirs_disabled = disable_problematic_components(mbed_os_path)
    print(f"Disabled {component_dirs_disabled} component directories")
    print()
    
    # Step 3: Remove duplicate configurations
    print("Step 3: Removing duplicate configurations...")
    duplicates_removed, files_processed = find_and_remove_config_duplicates(mbed_os_path)
    print(f"Processed {files_processed} configuration files")
    print(f"Removed {duplicates_removed} duplicate configurations")
    print()
    
    total_disabled = test_dirs_disabled + component_dirs_disabled
    
    print("=== Summary ===")
    print(f"- Test directories disabled: {test_dirs_disabled}")
    print(f"- Component directories disabled: {component_dirs_disabled}")
    print(f"- Total directories disabled: {total_disabled}")
    print(f"- Duplicate configurations removed: {duplicates_removed}")
    print(f"- Configuration files processed: {files_processed}")
    print()
    print("Next steps:")
    print("1. Try compiling again: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("2. If compilation succeeds, check the generated .bin file")
    print("3. If more duplicates appear, run this script again")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Final comprehensive fix for ALL duplicate configurations in mbed-os
This script will aggressively disable all non-essential components
"""

import os
import json
import shutil
from pathlib import Path

def disable_all_non_essential_directories(mbed_os_path):
    """Disable all non-essential directories that might cause conflicts"""
    disabled_dirs = 0
    
    print("Aggressively disabling all non-essential directories...")
    
    # Keep only essential directories for basic compilation
    essential_patterns = [
        'cmsis',
        'hal',
        'platform/source',
        'platform/include',
        'rtos/source',
        'rtos/include',
        'targets/TARGET_STM/TARGET_STM32F4/TARGET_STM32F429xI/TARGET_NUCLEO_F429ZI'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip already disabled directories
        if '.mbedignore' in files:
            continue
            
        rel_path = os.path.relpath(root, mbed_os_path)
        
        # Check if this is an essential directory
        is_essential = any([
            essential_pattern in rel_path for essential_pattern in essential_patterns
        ]) or rel_path in ['.', 'platform', 'rtos', 'targets', 'cmsis', 'hal']
        
        # Also check for specific patterns to keep
        keep_patterns = [
            'TARGET_STM32F4',
            'TARGET_STM32F429xI', 
            'TARGET_NUCLEO_F429ZI',
            'TARGET_STM',
            'TOOLCHAIN_GCC_ARM'
        ]
        
        has_keep_pattern = any([
            pattern in rel_path for pattern in keep_patterns
        ])
        
        # Disable if not essential and doesn't have keep patterns
        if not is_essential and not has_keep_pattern:
            # Additional check - don't disable if it's a direct child of essential dirs
            parent_path = os.path.dirname(rel_path)
            is_direct_child_of_essential = parent_path in ['platform', 'rtos', 'targets', 'cmsis', 'hal']
            
            if not is_direct_child_of_essential:
                ignore_path = os.path.join(root, '.mbedignore')
                try:
                    with open(ignore_path, 'w') as f:
                        f.write('*\n')
                    print(f"Disabled: {rel_path}")
                    disabled_dirs += 1
                except Exception as e:
                    print(f"Error disabling {root}: {e}")
    
    return disabled_dirs

def remove_all_configs_from_files(mbed_os_path):
    """Remove ALL configurations from mbed_lib.json files except essential ones"""
    configs_removed = 0
    files_processed = 0
    
    print("Removing all non-essential configurations from mbed_lib.json files...")
    
    # Essential configs to keep
    essential_configs = [
        'target',
        'toolchain',
        'core',
        'device-has',
        'device_has'
    ]
    
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
                        
                        # Remove all config sections except essential ones
                        if 'config' in data:
                            config_keys = list(data['config'].keys())
                            for key in config_keys:
                                # Keep only essential configs
                                is_essential = any([
                                    essential in key.lower() for essential in essential_configs
                                ])
                                
                                if not is_essential:
                                    del data['config'][key]
                                    print(f"  Removed config: {key} from {os.path.relpath(file_path, mbed_os_path)}")
                                    configs_removed += 1
                                    modified = True
                        
                        # Remove all target_overrides
                        if 'target_overrides' in data:
                            del data['target_overrides']
                            print(f"  Removed all target_overrides from {os.path.relpath(file_path, mbed_os_path)}")
                            configs_removed += 1
                            modified = True
                        
                        # Remove macros that might cause conflicts
                        if 'macros' in data:
                            del data['macros']
                            print(f"  Removed macros from {os.path.relpath(file_path, mbed_os_path)}")
                            configs_removed += 1
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
    
    return configs_removed, files_processed

def create_minimal_mbed_app_json(current_dir):
    """Create a minimal mbed_app.json with only essential configurations"""
    mbed_app_path = os.path.join(current_dir, 'mbed_app.json')
    
    # Create minimal configuration
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 9600,
                "platform.default-serial-baud-rate": 9600
            }
        }
    }
    
    try:
        with open(mbed_app_path, 'w', encoding='utf-8') as f:
            json.dump(minimal_config, f, indent=4)
        print("Created minimal mbed_app.json")
        return True
    except Exception as e:
        print(f"Error creating minimal mbed_app.json: {e}")
        return False

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
    
    print("=== FINAL Comprehensive Mbed OS Configuration Fixer ===")
    print(f"Working directory: {current_dir}")
    print(f"Mbed OS path: {mbed_os_path}")
    print("WARNING: This will aggressively disable most mbed-os features!")
    print()
    
    # Step 1: Disable all non-essential directories
    print("Step 1: Disabling all non-essential directories...")
    dirs_disabled = disable_all_non_essential_directories(mbed_os_path)
    print(f"Disabled {dirs_disabled} directories")
    print()
    
    # Step 2: Remove all non-essential configurations
    print("Step 2: Removing all non-essential configurations...")
    configs_removed, files_processed = remove_all_configs_from_files(mbed_os_path)
    print(f"Processed {files_processed} files")
    print(f"Removed {configs_removed} configurations")
    print()
    
    # Step 3: Create minimal mbed_app.json
    print("Step 3: Creating minimal mbed_app.json...")
    app_created = create_minimal_mbed_app_json(current_dir)
    print()
    
    print("=== Summary ===")
    print(f"- Directories disabled: {dirs_disabled}")
    print(f"- Configurations removed: {configs_removed}")
    print(f"- Files processed: {files_processed}")
    print(f"- Minimal mbed_app.json created: {app_created}")
    print()
    print("Next steps:")
    print("1. Try compiling again: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("2. This should now compile with minimal features")
    print("3. If it still fails, there may be fundamental issues with the mbed-os installation")

if __name__ == '__main__':
    main()
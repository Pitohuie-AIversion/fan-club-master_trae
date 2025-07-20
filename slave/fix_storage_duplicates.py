#!/usr/bin/env python3
"""
Fix storage.storage_type and other storage-related duplicate configurations in mbed-os
"""

import os
import json
import shutil
from pathlib import Path

def disable_all_storage_directories(mbed_os_path):
    """Disable all storage-related directories that might cause conflicts"""
    disabled_dirs = 0
    
    print("Disabling all storage-related directories...")
    
    # Storage patterns to disable
    storage_patterns = [
        'storage',
        'features/storage',
        'features/filesystem',
        'features/kvstore',
        'blockdevice',
        'filesystem',
        'kvstore',
        'flashiap',
        'dataflash',
        'sd',
        'spif',
        'qspif'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        # Skip already disabled directories
        if '.mbedignore' in files:
            continue
            
        rel_path = os.path.relpath(root, mbed_os_path).lower()
        
        # Check if this directory matches storage patterns
        should_disable = any([
            pattern in rel_path for pattern in storage_patterns
        ]) or any([
            pattern in os.path.basename(root).lower() for pattern in storage_patterns
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

def remove_storage_configs_from_files(mbed_os_path):
    """Remove storage-related configurations from mbed_lib.json files"""
    configs_removed = 0
    files_processed = 0
    
    print("Removing storage configurations from mbed_lib.json files...")
    
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
                        
                        # Remove storage-related config sections
                        if 'config' in data:
                            config_keys = list(data['config'].keys())
                            for key in config_keys:
                                # Remove storage-related configs
                                if any(pattern in key.lower() for pattern in [
                                    'storage',
                                    'blockdevice',
                                    'filesystem',
                                    'kvstore',
                                    'flashiap',
                                    'dataflash',
                                    'sd-driver',
                                    'spif-driver',
                                    'qspif-driver',
                                    'storage_type',
                                    'storage-type',
                                    'default-kv',
                                    'kv-config',
                                    'tdb-external',
                                    'tdb_external'
                                ]):
                                    del data['config'][key]
                                    print(f"  Removed config: {key} from {os.path.relpath(file_path, mbed_os_path)}")
                                    configs_removed += 1
                                    modified = True
                        
                        # Also remove from target_overrides if present
                        if 'target_overrides' in data:
                            for target, overrides in data['target_overrides'].items():
                                if isinstance(overrides, dict):
                                    override_keys = list(overrides.keys())
                                    for key in override_keys:
                                        if any(pattern in key.lower() for pattern in [
                                            'storage',
                                            'blockdevice',
                                            'filesystem',
                                            'kvstore',
                                            'storage_type',
                                            'storage-type'
                                        ]):
                                            del overrides[key]
                                            print(f"  Removed target override: {key} from {os.path.relpath(file_path, mbed_os_path)}")
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

def clean_mbed_app_json(current_dir):
    """Clean storage configurations from mbed_app.json"""
    mbed_app_path = os.path.join(current_dir, 'mbed_app.json')
    configs_removed = 0
    
    if os.path.exists(mbed_app_path):
        print("Cleaning mbed_app.json...")
        try:
            with open(mbed_app_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            
            # Remove storage configs from target_overrides
            if 'target_overrides' in data:
                for target, overrides in data['target_overrides'].items():
                    if isinstance(overrides, dict):
                        override_keys = list(overrides.keys())
                        for key in override_keys:
                            if any(pattern in key.lower() for pattern in [
                                'storage',
                                'blockdevice',
                                'filesystem',
                                'kvstore',
                                'storage_type',
                                'storage-type'
                            ]):
                                del overrides[key]
                                print(f"  Removed from mbed_app.json: {key}")
                                configs_removed += 1
                                modified = True
            
            # Remove storage configs from config section
            if 'config' in data:
                config_keys = list(data['config'].keys())
                for key in config_keys:
                    if any(pattern in key.lower() for pattern in [
                        'storage',
                        'blockdevice',
                        'filesystem',
                        'kvstore',
                        'storage_type',
                        'storage-type'
                    ]):
                        del data['config'][key]
                        print(f"  Removed from mbed_app.json config: {key}")
                        configs_removed += 1
                        modified = True
            
            if modified:
                with open(mbed_app_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                    
        except Exception as e:
            print(f"Error processing mbed_app.json: {e}")
    
    return configs_removed

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
    
    print("=== Storage Configuration Duplicate Fixer ===")
    print(f"Working directory: {current_dir}")
    print(f"Mbed OS path: {mbed_os_path}")
    print()
    
    # Step 1: Disable all storage directories
    print("Step 1: Disabling storage directories...")
    storage_dirs_disabled = disable_all_storage_directories(mbed_os_path)
    print(f"Disabled {storage_dirs_disabled} storage directories")
    print()
    
    # Step 2: Remove storage configurations from mbed_lib.json files
    print("Step 2: Removing storage configurations...")
    configs_removed, files_processed = remove_storage_configs_from_files(mbed_os_path)
    print(f"Processed {files_processed} files")
    print(f"Removed {configs_removed} storage configurations")
    print()
    
    # Step 3: Clean mbed_app.json
    print("Step 3: Cleaning mbed_app.json...")
    app_configs_removed = clean_mbed_app_json(current_dir)
    print(f"Removed {app_configs_removed} configurations from mbed_app.json")
    print()
    
    total_configs_removed = configs_removed + app_configs_removed
    
    print("=== Summary ===")
    print(f"- Storage directories disabled: {storage_dirs_disabled}")
    print(f"- Storage configurations removed: {total_configs_removed}")
    print(f"- Files processed: {files_processed}")
    print()
    print("Next steps:")
    print("1. Try compiling again: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")
    print("2. If compilation succeeds, check the generated .bin file")
    print("3. If more duplicates appear, run this script again")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Fix nvstore.enabled duplicate configuration error in Mbed OS
"""

import os
import json
import re
from pathlib import Path

def read_mbed_os_path():
    """Read mbed-os path from mbed-os.lib file"""
    mbed_lib_file = Path('mbed-os.lib')
    if mbed_lib_file.exists():
        content = mbed_lib_file.read_text().strip()
        if content.startswith('http'):
            # GitHub URL - use default mbed-os directory
            return Path('mbed-os')
        else:
            # Local path
            return Path(content)
    return Path('mbed-os')

def disable_nvstore_directories(mbed_os_path):
    """Disable all nvstore-related directories"""
    disabled_count = 0
    
    # Patterns to match nvstore-related directories
    nvstore_patterns = [
        'nvstore',
        'storage/nvstore',
        'features/nvstore',
        'features/storage/nvstore',
        'storage/blockdevice/COMPONENT_NVSTORE',
        'storage/filesystem/nvstore',
        'components/storage/nvstore',
        'targets/TARGET_*/TARGET_*/nvstore',
        'platform/source/nvstore',
        'platform/nvstore'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        root_path = Path(root)
        relative_path = root_path.relative_to(mbed_os_path)
        
        # Check if this directory matches any nvstore pattern
        for pattern in nvstore_patterns:
            if any(part.lower() == 'nvstore' for part in relative_path.parts) or \
               'nvstore' in str(relative_path).lower():
                
                # Create .mbedignore file
                mbedignore_file = root_path / '.mbedignore'
                if not mbedignore_file.exists():
                    mbedignore_file.write_text('*\n')
                    disabled_count += 1
                    print(f"Disabled: {relative_path}")
                break
    
    return disabled_count

def remove_nvstore_configs(mbed_os_path):
    """Remove nvstore configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # Find all mbed_lib.json files
    for root, dirs, files in os.walk(mbed_os_path):
        for file in files:
            if file == 'mbed_lib.json':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = False
                    
                    # Remove nvstore configurations
                    if 'config' in data:
                        nvstore_keys = [key for key in data['config'].keys() if 'nvstore' in key.lower()]
                        for key in nvstore_keys:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                            print(f"Removed config: {key} from {file_path}")
                    
                    # Remove target_overrides with nvstore
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                nvstore_keys = [key for key in overrides.keys() if 'nvstore' in key.lower()]
                                for key in nvstore_keys:
                                    del overrides[key]
                                    removed_count += 1
                                    modified = True
                                    print(f"Removed target override: {key} from {file_path}")
                    
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        files_processed += 1
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return removed_count, files_processed

def create_minimal_mbed_app():
    """Create a minimal mbed_app.json without nvstore configurations"""
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 115200,
                "platform.stdio-convert-newlines": True
            }
        }
    }
    
    with open('mbed_app.json', 'w') as f:
        json.dump(minimal_config, f, indent=4)
    
    print("Created minimal mbed_app.json")

def main():
    print("=== Fixing nvstore.enabled duplicate configuration ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable nvstore directories
    disabled_count = disable_nvstore_directories(mbed_os_path)
    print(f"Disabled {disabled_count} nvstore-related directories")
    
    # Remove nvstore configurations
    removed_count, files_processed = remove_nvstore_configs(mbed_os_path)
    print(f"Removed {removed_count} nvstore configurations from {files_processed} files")
    
    # Create minimal mbed_app.json
    create_minimal_mbed_app()
    
    print("\n=== Fix completed ===")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
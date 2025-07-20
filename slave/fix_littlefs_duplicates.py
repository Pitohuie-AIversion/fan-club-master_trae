#!/usr/bin/env python3
"""
Fix littlefs.read_size duplicate configuration error in Mbed OS
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
            return Path('mbed-os')
        else:
            return Path(content)
    return Path('mbed-os')

def disable_littlefs_directories(mbed_os_path):
    """Disable all littlefs-related directories"""
    disabled_count = 0
    
    # Comprehensive list of littlefs-related directory patterns
    littlefs_patterns = [
        'littlefs', 'littlefsv2', 'LittleFileSystem', 'LittleFileSystem2',
        'storage/filesystem/littlefs', 'storage/filesystem/littlefsv2',
        'storage/kvstore', 'storage/filesystemstore', 'storage/platform',
        'features/storage', 'components/storage'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        root_path = Path(root)
        relative_path = root_path.relative_to(mbed_os_path)
        
        # Skip root directory
        if relative_path == Path('.'):
            continue
            
        # Check if this directory should be disabled
        should_disable = False
        path_str = str(relative_path).lower()
        
        # Check for littlefs patterns
        if 'littlefs' in path_str or 'littlefilesystem' in path_str:
            should_disable = True
        
        # Check for storage-related patterns that might contain littlefs configs
        if any(pattern in path_str for pattern in ['storage/filesystem', 'storage/kvstore', 'storage/platform']):
            should_disable = True
            
        if should_disable:
            mbedignore_file = root_path / '.mbedignore'
            if not mbedignore_file.exists():
                mbedignore_file.write_text('*\n')
                disabled_count += 1
                print(f"Disabled: {relative_path}")
    
    return disabled_count

def remove_littlefs_configs(mbed_os_path):
    """Remove littlefs configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # List of littlefs-related configuration keys to remove
    littlefs_configs = [
        'read_size', 'prog_size', 'block_size', 'cache_size', 'lookahead_size',
        'block_cycles', 'name_max', 'file_max', 'attr_max', 'metadata_max',
        'littlefs.', 'littlefs2.', 'filesystem.', 'storage.',
        'kvstore.', 'filesystemstore.'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        for file in files:
            if file == 'mbed_lib.json':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = False
                    
                    # Remove littlefs configurations
                    if 'config' in data:
                        keys_to_remove = []
                        for key in data['config'].keys():
                            for pattern in littlefs_configs:
                                if pattern in key.lower():
                                    keys_to_remove.append(key)
                                    break
                        
                        for key in keys_to_remove:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                            print(f"Removed config: {key} from {file_path}")
                    
                    # Remove target_overrides with littlefs
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                keys_to_remove = []
                                for key in overrides.keys():
                                    for pattern in littlefs_configs:
                                        if pattern in key.lower():
                                            keys_to_remove.append(key)
                                            break
                                
                                for key in keys_to_remove:
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

def create_bare_minimum_mbed_app():
    """Create a bare minimum mbed_app.json without any filesystem configurations"""
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 115200
            }
        }
    }
    
    with open('mbed_app.json', 'w') as f:
        json.dump(minimal_config, f, indent=4)
    
    print("Created bare minimum mbed_app.json")

def main():
    print("=== Fixing littlefs.read_size duplicate configuration ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable littlefs directories
    disabled_count = disable_littlefs_directories(mbed_os_path)
    print(f"Disabled {disabled_count} littlefs-related directories")
    
    # Remove littlefs configurations
    removed_count, files_processed = remove_littlefs_configs(mbed_os_path)
    print(f"Removed {removed_count} littlefs configurations from {files_processed} files")
    
    # Create bare minimum mbed_app.json
    create_bare_minimum_mbed_app()
    
    print("\n=== Fix completed ===")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
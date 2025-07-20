#!/usr/bin/env python3
"""
Fix storage_filesystem_no_rbp.filesystem duplicate configuration error in Mbed OS
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

def disable_all_filesystem_directories(mbed_os_path):
    """Disable ALL filesystem-related directories"""
    disabled_count = 0
    
    # Comprehensive list of filesystem-related directory patterns
    filesystem_patterns = [
        # Core filesystem
        'filesystem', 'storage', 'blockdevice', 'kvstore',
        'littlefs', 'fatfs', 'fat', 'spifs', 'dataflash',
        
        # Storage types
        'storage_filesystem', 'storage_filesystem_no_rbp',
        'no_rbp', 'rbp', 'rollback', 'protection',
        
        # Block devices
        'sd', 'sdhc', 'sdio', 'mmc', 'emmc', 'flash',
        'qspi', 'spi_flash', 'dataflash', 'eeprom',
        
        # File systems
        'littlefsv2', 'LittleFileSystem', 'LittleFileSystem2',
        'FATFileSystem', 'SPIFBlockDevice', 'DataFlashBlockDevice',
        
        # Storage features
        'nvstore', 'tdbstore', 'securestore', 'filesystemstore',
        'kvstore', 'kv_config', 'kv_map'
    ]
    
    # Also disable specific problematic directories
    specific_dirs = [
        'storage',
        'features/storage',
        'storage/blockdevice',
        'storage/filesystem',
        'storage/kvstore',
        'storage/platform',
        'components/storage',
        'drivers/storage'
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
        
        # Check for filesystem patterns
        for pattern in filesystem_patterns:
            if pattern in path_str or any(pattern in part.lower() for part in relative_path.parts):
                should_disable = True
                break
        
        # Check specific directories
        for specific_dir in specific_dirs:
            if specific_dir.lower() in path_str:
                should_disable = True
                break
                
        if should_disable:
            mbedignore_file = root_path / '.mbedignore'
            if not mbedignore_file.exists():
                mbedignore_file.write_text('*\n')
                disabled_count += 1
                print(f"Disabled: {relative_path}")
    
    return disabled_count

def remove_all_filesystem_configs(mbed_os_path):
    """Remove ALL filesystem-related configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # Comprehensive list of filesystem-related configuration keys to remove
    filesystem_configs = [
        # Core filesystem configs
        'filesystem', 'storage', 'blockdevice', 'kvstore',
        'littlefs', 'fatfs', 'fat', 'spifs', 'dataflash',
        
        # Storage filesystem specific
        'storage_filesystem', 'storage_filesystem_no_rbp',
        'no_rbp', 'rbp', 'rollback', 'protection',
        
        # Block device configs
        'block_size', 'block_count', 'read_size', 'prog_size',
        'cache_size', 'lookahead_size', 'block_cycles',
        
        # File system parameters
        'read_size', 'prog_size', 'block_size', 'block_count',
        'cache_size', 'lookahead_size', 'name_max', 'file_max',
        'attr_max', 'metadata_max',
        
        # Storage types
        'storage_type', 'default_kv', 'kv_config',
        'tdb_internal', 'tdb_external', 'filesystem_kv',
        
        # Device specific
        'sd_', 'sdhc_', 'sdio_', 'mmc_', 'emmc_', 'flash_',
        'qspi_', 'spi_flash_', 'dataflash_', 'eeprom_',
        
        # Enable/disable flags
        'enabled', 'enable', 'disabled', 'disable',
        'provide-default', 'default'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        for file in files:
            if file == 'mbed_lib.json':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = False
                    
                    # Remove filesystem configurations
                    if 'config' in data:
                        keys_to_remove = []
                        for key in data['config'].keys():
                            for pattern in filesystem_configs:
                                if pattern.lower() in key.lower():
                                    keys_to_remove.append(key)
                                    break
                        
                        for key in keys_to_remove:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                            print(f"Removed config: {key} from {file_path}")
                    
                    # Remove target_overrides with filesystem configs
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                keys_to_remove = []
                                for key in overrides.keys():
                                    for pattern in filesystem_configs:
                                        if pattern.lower() in key.lower():
                                            keys_to_remove.append(key)
                                            break
                                
                                for key in keys_to_remove:
                                    del overrides[key]
                                    removed_count += 1
                                    modified = True
                                    print(f"Removed target override: {key} from {file_path}")
                    
                    # Remove macros that might cause conflicts
                    if 'macros' in data:
                        macros_to_remove = []
                        for macro in data['macros']:
                            for pattern in filesystem_configs:
                                if pattern.lower() in macro.lower():
                                    macros_to_remove.append(macro)
                                    break
                        
                        for macro in macros_to_remove:
                            data['macros'].remove(macro)
                            removed_count += 1
                            modified = True
                            print(f"Removed macro: {macro} from {file_path}")
                    
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        files_processed += 1
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return removed_count, files_processed

def create_no_storage_mbed_app():
    """Create mbed_app.json that completely disables storage"""
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 115200,
                "target.features_remove": ["LWIP", "NETSOCKET", "STORAGE", "FILESYSTEM"],
                "target.components_remove": ["SD", "FLASHIAP", "QSPIF", "SPIF", "DATAFLASH"]
            }
        }
    }
    
    with open('mbed_app.json', 'w') as f:
        json.dump(minimal_config, f, indent=4)
    
    print("Created no-storage mbed_app.json")

def main():
    print("=== Fixing storage_filesystem_no_rbp.filesystem duplicate configuration ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable all filesystem directories
    disabled_count = disable_all_filesystem_directories(mbed_os_path)
    print(f"Disabled {disabled_count} filesystem-related directories")
    
    # Remove all filesystem configurations
    removed_count, files_processed = remove_all_filesystem_configs(mbed_os_path)
    print(f"Removed {removed_count} filesystem configurations from {files_processed} files")
    
    # Create no-storage mbed_app.json
    create_no_storage_mbed_app()
    
    print("\n=== Filesystem fix completed ===")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
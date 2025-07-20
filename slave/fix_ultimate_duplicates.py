#!/usr/bin/env python3
"""
Ultimate fix for all duplicate configuration errors in Mbed OS
This script will aggressively disable all non-essential components
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

def disable_all_problematic_directories(mbed_os_path):
    """Disable all directories that could cause duplicate configurations"""
    disabled_count = 0
    
    # Comprehensive list of problematic directory patterns
    problematic_patterns = [
        # Tests and examples
        'TEST_', 'TESTS', 'test', 'tests', 'example', 'examples', 'EXAMPLE', 'EXAMPLES',
        # Storage and filesystem
        'storage', 'filesystem', 'blockdevice', 'nvstore', 'kvstore', 'flashiap',
        # Connectivity
        'connectivity', 'cellular', 'wifi', 'ethernet', 'bluetooth', 'lorawan', 'nfc',
        'lwip', 'netsocket', 'network', 'socket', 'ppp', 'slip',
        # Radio and wireless
        's2lp', 'spirit1', 'cc3000', 'esp8266', 'esp32', 'at86rf', 'mcr20a',
        # USB and communication
        'usb', 'usbdevice', 'usbhost', 'serial', 'i2c', 'spi', 'can',
        # Security and crypto
        'mbedtls', 'crypto', 'security', 'tls', 'ssl',
        # RTOS and platform
        'rtos', 'cmsis', 'mbed-trace', 'mbed-client', 'mbed-coap',
        # Device specific
        'device', 'drivers/device', 'hal/device',
        # Features
        'features/FEATURE_', 'FEATURE_',
        # Components
        'COMPONENT_', 'components/',
        # Bootloader
        'bootloader', 'BOOTLOADER'
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
        
        for pattern in problematic_patterns:
            if pattern.lower() in path_str or any(pattern.lower() in part.lower() for part in relative_path.parts):
                should_disable = True
                break
        
        # Also disable if it contains certain keywords
        if any(keyword in path_str for keyword in ['test', 'example', 'demo', 'sample']):
            should_disable = True
            
        if should_disable:
            mbedignore_file = root_path / '.mbedignore'
            if not mbedignore_file.exists():
                mbedignore_file.write_text('*\n')
                disabled_count += 1
                print(f"Disabled: {relative_path}")
    
    return disabled_count

def clean_all_mbed_configs(mbed_os_path):
    """Remove all problematic configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # List of configuration keys to remove
    problematic_configs = [
        's2lp.provide-default', 'drivers.uart-serial-txbuf-size', 'drivers.uart-serial-rxbuf-size',
        'storage.storage_type', 'lwip.ipv4-enabled', 'nvstore.enabled',
        'blockdevice.', 'storage.', 'cellular.', 'wifi.', 'ethernet.', 'bluetooth.',
        'lorawan.', 'nfc.', 'lwip.', 'netsocket.', 'ppp.', 'slip.',
        'usb.', 'mbedtls.', 'crypto.', 'security.', 'tls.', 'ssl.',
        'rtos.', 'cmsis.', 'mbed-trace.', 'mbed-client.', 'mbed-coap.',
        'default-cellular-', 'target.', 'platform.default-serial-baud-rate'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        for file in files:
            if file == 'mbed_lib.json':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = False
                    
                    # Remove problematic configurations
                    if 'config' in data:
                        keys_to_remove = []
                        for key in data['config'].keys():
                            for pattern in problematic_configs:
                                if pattern in key:
                                    keys_to_remove.append(key)
                                    break
                        
                        for key in keys_to_remove:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                    
                    # Remove target_overrides
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                keys_to_remove = []
                                for key in overrides.keys():
                                    for pattern in problematic_configs:
                                        if pattern in key:
                                            keys_to_remove.append(key)
                                            break
                                
                                for key in keys_to_remove:
                                    del overrides[key]
                                    removed_count += 1
                                    modified = True
                    
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        files_processed += 1
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return removed_count, files_processed

def create_ultra_minimal_mbed_app():
    """Create an ultra-minimal mbed_app.json"""
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 115200
            }
        }
    }
    
    with open('mbed_app.json', 'w') as f:
        json.dump(minimal_config, f, indent=4)
    
    print("Created ultra-minimal mbed_app.json")

def main():
    print("=== Ultimate fix for all duplicate configurations ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable all problematic directories
    disabled_count = disable_all_problematic_directories(mbed_os_path)
    print(f"Disabled {disabled_count} problematic directories")
    
    # Clean all mbed configurations
    removed_count, files_processed = clean_all_mbed_configs(mbed_os_path)
    print(f"Removed {removed_count} configurations from {files_processed} files")
    
    # Create ultra-minimal mbed_app.json
    create_ultra_minimal_mbed_app()
    
    print("\n=== Ultimate fix completed ===")
    print("This should resolve all duplicate configuration issues.")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
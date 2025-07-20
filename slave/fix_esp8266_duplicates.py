#!/usr/bin/env python3
"""
Fix esp8266.tx duplicate configuration error in Mbed OS
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

def disable_wifi_and_connectivity_directories(mbed_os_path):
    """Disable all WiFi and connectivity-related directories"""
    disabled_count = 0
    
    # Comprehensive list of WiFi and connectivity-related directory patterns
    wifi_patterns = [
        'esp8266', 'esp32', 'wifi', 'wireless', 'connectivity',
        'at86rf', 'cc3000', 'mcr20a', 'spirit1', 's2lp',
        'bluetooth', 'ble', 'nfc', 'lorawan', 'lora',
        'cellular', 'gsm', 'gprs', '3g', '4g', 'lte',
        'ethernet', 'lwip', 'netsocket', 'network', 'socket',
        'ppp', 'slip', 'modem', 'at_cmd', 'at_handler'
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
        
        # Check for WiFi and connectivity patterns
        for pattern in wifi_patterns:
            if pattern in path_str or any(pattern in part.lower() for part in relative_path.parts):
                should_disable = True
                break
        
        # Also disable connectivity features
        if 'connectivity' in path_str or 'features/connectivity' in path_str:
            should_disable = True
            
        if should_disable:
            mbedignore_file = root_path / '.mbedignore'
            if not mbedignore_file.exists():
                mbedignore_file.write_text('*\n')
                disabled_count += 1
                print(f"Disabled: {relative_path}")
    
    return disabled_count

def remove_wifi_configs(mbed_os_path):
    """Remove WiFi and connectivity configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # List of WiFi and connectivity-related configuration keys to remove
    wifi_configs = [
        'esp8266.', 'esp32.', 'wifi.', 'wireless.', 'connectivity.',
        'at86rf.', 'cc3000.', 'mcr20a.', 'spirit1.', 's2lp.',
        'bluetooth.', 'ble.', 'nfc.', 'lorawan.', 'lora.',
        'cellular.', 'gsm.', 'gprs.', '3g.', '4g.', 'lte.',
        'ethernet.', 'lwip.', 'netsocket.', 'network.', 'socket.',
        'ppp.', 'slip.', 'modem.', 'at_cmd.', 'at_handler.',
        'tx', 'rx', 'baudrate', 'baud_rate', 'serial',
        'pin_tx', 'pin_rx', 'tx_pin', 'rx_pin'
    ]
    
    for root, dirs, files in os.walk(mbed_os_path):
        for file in files:
            if file == 'mbed_lib.json':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = False
                    
                    # Remove WiFi configurations
                    if 'config' in data:
                        keys_to_remove = []
                        for key in data['config'].keys():
                            for pattern in wifi_configs:
                                if pattern in key.lower():
                                    keys_to_remove.append(key)
                                    break
                        
                        for key in keys_to_remove:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                            print(f"Removed config: {key} from {file_path}")
                    
                    # Remove target_overrides with WiFi
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                keys_to_remove = []
                                for key in overrides.keys():
                                    for pattern in wifi_configs:
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

def create_ultra_minimal_mbed_app():
    """Create an ultra-minimal mbed_app.json without any connectivity configurations"""
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
    print("=== Fixing esp8266.tx duplicate configuration ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable WiFi and connectivity directories
    disabled_count = disable_wifi_and_connectivity_directories(mbed_os_path)
    print(f"Disabled {disabled_count} WiFi and connectivity-related directories")
    
    # Remove WiFi configurations
    removed_count, files_processed = remove_wifi_configs(mbed_os_path)
    print(f"Removed {removed_count} WiFi configurations from {files_processed} files")
    
    # Create ultra-minimal mbed_app.json
    create_ultra_minimal_mbed_app()
    
    print("\n=== Fix completed ===")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
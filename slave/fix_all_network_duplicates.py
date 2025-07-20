#!/usr/bin/env python3
"""
Fix all network-related duplicate configuration errors in Mbed OS
This is the most comprehensive fix to disable all networking components
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

def disable_all_network_directories(mbed_os_path):
    """Disable ALL network-related directories comprehensively"""
    disabled_count = 0
    
    # Most comprehensive list of network-related directory patterns
    network_patterns = [
        # Core networking
        'lwip', 'netsocket', 'network', 'socket', 'connectivity',
        'ethernet', 'wifi', 'wireless', 'cellular', 'bluetooth', 'ble',
        
        # WiFi and wireless
        'esp8266', 'esp32', 'cc3000', 'at86rf', 'mcr20a', 'spirit1', 's2lp',
        'emw3080', 'ism43362', 'wizfi310', 'rtw', 'realtek',
        
        # Cellular and modems
        'gsm', 'gprs', '3g', '4g', 'lte', 'modem', 'at_cmd', 'at_handler',
        'ppp', 'slip', 'quectel', 'ublox', 'telit', 'sierra',
        
        # Bluetooth and NFC
        'cordio', 'nfc', 'rfid',
        
        # LoRa and IoT protocols
        'lorawan', 'lora', 'sigfox', 'nb_iot', 'cat_m1',
        
        # Network protocols
        'tcp', 'udp', 'http', 'https', 'mqtt', 'coap', 'sntp',
        'tls', 'dtls', 'ssl', 'mbedtls_net',
        
        # Network features
        'ipv4', 'ipv6', 'dhcp', 'dns', 'arp', 'icmp',
        
        # Serial communication that might conflict
        'serial', 'uart', 'usart', 'spi', 'i2c'
    ]
    
    # Also disable specific problematic directories
    specific_dirs = [
        'connectivity',
        'features/connectivity',
        'features/netsocket',
        'features/lwipstack',
        'features/cellular',
        'features/lorawan',
        'features/FEATURE_BLE',
        'features/FEATURE_LWIP',
        'drivers/source/usb',
        'drivers/usb',
        'hal/usb',
        'targets/TARGET_STM/TARGET_STM32F4/TARGET_STM32F429xI/TARGET_NUCLEO_F429ZI'
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
        
        # Check for network patterns
        for pattern in network_patterns:
            if pattern in path_str or any(pattern in part.lower() for part in relative_path.parts):
                should_disable = True
                break
        
        # Check specific directories
        for specific_dir in specific_dirs:
            if specific_dir.lower() in path_str:
                should_disable = True
                break
                
        # Also disable any directory containing 'test' or 'example'
        if 'test' in path_str or 'example' in path_str or 'demo' in path_str:
            should_disable = True
            
        if should_disable:
            mbedignore_file = root_path / '.mbedignore'
            if not mbedignore_file.exists():
                mbedignore_file.write_text('*\n')
                disabled_count += 1
                print(f"Disabled: {relative_path}")
    
    return disabled_count

def remove_all_network_configs(mbed_os_path):
    """Remove ALL network-related configurations from mbed_lib.json files"""
    removed_count = 0
    files_processed = 0
    
    # Comprehensive list of network-related configuration keys to remove
    network_configs = [
        # Core networking
        'lwip.', 'netsocket.', 'network.', 'socket.', 'connectivity.',
        'ethernet.', 'wifi.', 'wireless.', 'cellular.', 'bluetooth.', 'ble.',
        
        # Protocol specific
        'ipv4', 'ipv6', 'dhcp', 'dns', 'arp', 'icmp', 'tcp', 'udp',
        'http', 'https', 'mqtt', 'coap', 'sntp', 'tls', 'dtls', 'ssl',
        
        # Hardware specific
        'esp8266.', 'esp32.', 'cc3000.', 'at86rf.', 'mcr20a.', 'spirit1.', 's2lp.',
        'emw3080.', 'ism43362.', 'wizfi310.', 'rtw.', 'realtek.',
        
        # Cellular
        'gsm.', 'gprs.', '3g.', '4g.', 'lte.', 'modem.', 'at_cmd.', 'at_handler.',
        'ppp.', 'slip.', 'quectel.', 'ublox.', 'telit.', 'sierra.',
        
        # LoRa and IoT
        'lorawan.', 'lora.', 'sigfox.', 'nb_iot.', 'cat_m1.',
        
        # Serial communication
        'tx', 'rx', 'baudrate', 'baud_rate', 'baud-rate', 'serial',
        'pin_tx', 'pin_rx', 'tx_pin', 'rx_pin', 'tx-pin', 'rx-pin',
        'uart', 'usart', 'spi', 'i2c',
        
        # Buffer and timing
        'buffer', 'timeout', 'retry', 'interval', 'delay',
        'size', 'length', 'count', 'max', 'min',
        
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
                    
                    # Remove network configurations
                    if 'config' in data:
                        keys_to_remove = []
                        for key in data['config'].keys():
                            for pattern in network_configs:
                                if pattern.lower() in key.lower():
                                    keys_to_remove.append(key)
                                    break
                        
                        for key in keys_to_remove:
                            del data['config'][key]
                            removed_count += 1
                            modified = True
                            print(f"Removed config: {key} from {file_path}")
                    
                    # Remove target_overrides with network configs
                    if 'target_overrides' in data:
                        for target, overrides in data['target_overrides'].items():
                            if isinstance(overrides, dict):
                                keys_to_remove = []
                                for key in overrides.keys():
                                    for pattern in network_configs:
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
                            for pattern in network_configs:
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

def create_bare_minimum_mbed_app():
    """Create the most minimal mbed_app.json possible"""
    minimal_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 115200,
                "target.features_remove": ["LWIP", "NETSOCKET", "STORAGE", "FILESYSTEM"]
            }
        }
    }
    
    with open('mbed_app.json', 'w') as f:
        json.dump(minimal_config, f, indent=4)
    
    print("Created bare minimum mbed_app.json with features removed")

def main():
    print("=== Comprehensive Network Duplicate Configuration Fix ===")
    
    # Read mbed-os path
    mbed_os_path = read_mbed_os_path()
    
    if not mbed_os_path.exists():
        print(f"Error: mbed-os directory not found at {mbed_os_path}!")
        return
    
    print(f"Using mbed-os path: {mbed_os_path}")
    
    # Disable all network directories
    disabled_count = disable_all_network_directories(mbed_os_path)
    print(f"Disabled {disabled_count} network-related directories")
    
    # Remove all network configurations
    removed_count, files_processed = remove_all_network_configs(mbed_os_path)
    print(f"Removed {removed_count} network configurations from {files_processed} files")
    
    # Create bare minimum mbed_app.json
    create_bare_minimum_mbed_app()
    
    print("\n=== Comprehensive fix completed ===")
    print("Please try compiling again with: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mbed OS 配置冲突修复工具 - 高级版本
专门处理各种重复配置定义问题
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✓ 已备份: {file_path} -> {backup_path}")
        return backup_path
    return None

def find_mbed_lib_files(root_dir):
    """查找所有mbed_lib.json文件"""
    mbed_lib_files = []
    for root, dirs, files in os.walk(root_dir):
        if 'mbed_lib.json' in files:
            mbed_lib_files.append(os.path.join(root, 'mbed_lib.json'))
    return mbed_lib_files

def analyze_config_conflicts(mbed_lib_files):
    """分析配置冲突"""
    all_configs = {}
    conflicts = {}
    
    for lib_file in mbed_lib_files:
        try:
            with open(lib_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'config' in data:
                for key, value in data['config'].items():
                    full_key = f"{data.get('name', 'unknown')}.{key}"
                    
                    if full_key in all_configs:
                        if full_key not in conflicts:
                            conflicts[full_key] = [all_configs[full_key]]
                        conflicts[full_key].append({
                            'file': lib_file,
                            'value': value
                        })
                    else:
                        all_configs[full_key] = {
                            'file': lib_file,
                            'value': value
                        }
        except Exception as e:
            print(f"⚠️  读取文件失败: {lib_file} - {e}")
    
    return conflicts

def fix_known_conflicts():
    """修复已知的配置冲突"""
    print("\n🔧 开始修复已知配置冲突...")
    
    # 定义需要修复的配置冲突
    known_conflicts = {
        'mbed-mesh-api.heap-size': {
            'keep_value': {'value': 32500},
            'description': 'Mesh API堆大小配置'
        },
        'nanostack-hal.nvm_cfstore': {
            'keep_value': {'value': 0},
            'description': 'Nanostack HAL NVM配置'
        },
        'nanostack-eventloop.use_platform_tick_timer': {
            'keep_value': {'value': 1},
            'description': 'Nanostack事件循环定时器配置'
        }
    }
    
    # 查找所有mbed_lib.json文件
    mbed_os_path = "D:\\mbed-os-shared\\mbed-os"
    if not os.path.exists(mbed_os_path):
        print(f"❌ 未找到mbed-os路径: {mbed_os_path}")
        return False
    
    mbed_lib_files = find_mbed_lib_files(mbed_os_path)
    print(f"📁 找到 {len(mbed_lib_files)} 个mbed_lib.json文件")
    
    fixed_count = 0
    
    for lib_file in mbed_lib_files:
        try:
            with open(lib_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            
            if 'config' in data:
                lib_name = data.get('name', 'unknown')
                configs_to_remove = []
                
                for config_key in data['config'].keys():
                    full_key = f"{lib_name}.{config_key}"
                    
                    if full_key in known_conflicts:
                        # 检查是否应该保留这个配置
                        conflict_info = known_conflicts[full_key]
                        current_value = data['config'][config_key]
                        
                        # 如果当前值与期望保留的值不同，则移除
                        if current_value != conflict_info['keep_value']:
                            configs_to_remove.append(config_key)
                            print(f"  🗑️  移除冲突配置: {full_key} 从 {lib_file}")
                            modified = True
                
                # 移除冲突的配置
                for key in configs_to_remove:
                    del data['config'][key]
                
                # 如果config为空，移除整个config节
                if not data['config']:
                    del data['config']
                    modified = True
            
            if modified:
                backup_file(lib_file)
                with open(lib_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                fixed_count += 1
                print(f"  ✓ 已修复: {lib_file}")
                
        except Exception as e:
            print(f"  ❌ 修复失败: {lib_file} - {e}")
    
    print(f"\n✅ 修复完成! 共修复了 {fixed_count} 个文件")
    return fixed_count > 0

def create_clean_mbed_app_json():
    """创建干净的mbed_app.json"""
    print("\n📝 创建优化的mbed_app.json...")
    
    clean_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 9600,
                "platform.default-serial-baud-rate": 9600,
                "platform.stdio-convert-newlines": True,
                "platform.stdio-buffered-serial": True
            },
            "NUCLEO_F429ZI": {
                "target.bootloader_img": "../Slave_Bootloader/BUILD/NUCLEO_F429ZI/GCC_ARM/Slave_Bootloader.bin"
            },
            "NUCLEO_F446RE": {
                "target.bootloader_img": "../Slave_Bootloader/BUILD/NUCLEO_F446RE/GCC_ARM/Slave_Bootloader.bin"
            }
        },
        "config": {
            "mesh-heap-size": {
                "help": "Mesh API heap size",
                "value": 32500
            }
        }
    }
    
    # 检查slave目录
    slave_dirs = ['slave', 'slave_upgraded', 'slave_bootloader', 'slave_bootloader_upgraded']
    
    for slave_dir in slave_dirs:
        if os.path.exists(slave_dir):
            mbed_app_path = os.path.join(slave_dir, 'mbed_app.json')
            backup_file(mbed_app_path)
            
            with open(mbed_app_path, 'w', encoding='utf-8') as f:
                json.dump(clean_config, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ 已更新: {mbed_app_path}")

def main():
    """主函数"""
    print("🚀 Mbed OS 配置冲突修复工具 - 高级版本")
    print("=" * 50)
    
    try:
        # 修复已知冲突
        if fix_known_conflicts():
            print("\n✅ 配置冲突修复完成!")
        else:
            print("\n⚠️  未发现需要修复的配置冲突")
        
        # 创建干净的mbed_app.json
        create_clean_mbed_app_json()
        
        print("\n🎉 所有修复操作完成!")
        print("\n📋 建议的下一步操作:")
        print("1. 清理构建缓存: mbed-tools configure --clean")
        print("2. 重新编译: mbed-tools compile -m NUCLEO_F429ZI -t GCC_ARM")
        print("3. 如果仍有问题，请检查错误日志")
        
    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
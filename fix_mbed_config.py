#!/usr/bin/env python3
"""
Mbed OS 配置冲突修复脚本
解决重复配置定义问题，确保编译成功
"""

import os
import json
import shutil
from pathlib import Path

def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path) and not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"已备份: {file_path} -> {backup_path}")

def fix_mbed_lib_json(file_path):
    """修复 mbed_lib.json 中的重复配置"""
    if not os.path.exists(file_path):
        return
    
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查并修复重复的配置
        config = data.get('config', {})
        target_overrides = data.get('target_overrides', {})
        
        # 移除可能冲突的配置
        conflicting_keys = [
            'mbed-mesh-api.heap-size',
            'nanostack-hal.nvm_cfstore',
            'nanostack-eventloop.use_platform_tick_timer',
            'nanostack-hal.event_loop_thread_stack_size'
        ]
        
        modified = False
        for key in conflicting_keys:
            if key in config:
                print(f"移除重复配置: {key} from {file_path}")
                del config[key]
                modified = True
            
            # 检查 target_overrides 中的配置
            for target, overrides in target_overrides.items():
                if key in overrides:
                    print(f"移除目标重写配置: {key} from {target} in {file_path}")
                    del overrides[key]
                    modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"已修复: {file_path}")
    
    except Exception as e:
        print(f"修复 {file_path} 时出错: {e}")

def create_clean_mbed_app_json(project_dir):
    """创建干净的 mbed_app.json 配置"""
    mbed_app_path = os.path.join(project_dir, 'mbed_app.json')
    backup_file(mbed_app_path)
    
    # 创建最小化的配置，避免冲突
    clean_config = {
        "target_overrides": {
            "*": {
                "platform.stdio-baud-rate": 9600,
                "platform.default-serial-baud-rate": 9600
            },
            "NUCLEO_F429ZI": {
                "target.bootloader_img": "../Slave_Bootloader/BUILD/NUCLEO_F429ZI/GCC_ARM/Slave_Bootloader.bin"
            },
            "NUCLEO_F446RE": {
                "target.bootloader_img": "../Slave_Bootloader/BUILD/NUCLEO_F446RE/GCC_ARM/Slave_Bootloader.bin"
            }
        }
    }
    
    with open(mbed_app_path, 'w', encoding='utf-8') as f:
        json.dump(clean_config, f, indent=2, ensure_ascii=False)
    
    print(f"已创建干净的配置文件: {mbed_app_path}")

def main():
    """主函数"""
    print("开始修复 Mbed OS 配置冲突...")
    
    # 当前工作目录
    base_dir = Path.cwd()
    
    # 需要检查的项目目录
    project_dirs = [
        base_dir / 'slave',
        base_dir / 'slave_upgraded',
        base_dir / 'slave_bootloader',
        base_dir / 'slave_bootloader_upgraded'
    ]
    
    for project_dir in project_dirs:
        if project_dir.exists():
            print(f"\n处理项目: {project_dir}")
            
            # 创建干净的 mbed_app.json
            create_clean_mbed_app_json(str(project_dir))
            
            # 检查子目录中的配置文件
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file == 'mbed_lib.json':
                        file_path = os.path.join(root, file)
                        fix_mbed_lib_json(file_path)
    
    print("\n配置修复完成！")
    print("\n建议的编译命令:")
    print("cd slave")
    print("mbed-tools.exe compile -t GCC_ARM -m NUCLEO_F446RE --clean")
    print("\n或者使用 Makefile:")
    print("cd slave")
    print("make clean && make")

if __name__ == '__main__':
    main()
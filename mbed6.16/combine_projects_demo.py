#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fan Club MkIV 项目结合演示脚本

这个脚本演示了如何正确结合 slave 和 slave_bootloader 两个项目：
1. slave_bootloader: 引导程序，负责固件更新和应用启动
2. slave: 主应用程序，包含风扇控制逻辑

作者: AI Assistant
日期: 2025年1月
"""

import os
import json
from pathlib import Path

def demonstrate_project_combination():
    """演示项目结合方式"""
    print("Fan Club MkIV 项目结合演示")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    bootloader_dir = base_dir / "slave_bootloader"
    application_dir = base_dir / "slave"
    
    print(f"基础目录: {base_dir}")
    print(f"Bootloader目录: {bootloader_dir}")
    print(f"应用程序目录: {application_dir}")
    print()
    
    # 1. 项目架构说明
    print("1. 项目架构说明:")
    print("   ┌─────────────────────────────────────┐")
    print("   │          STM32F429ZI Flash          │")
    print("   ├─────────────────────────────────────┤")
    print("   │  0x08000000 - 0x0803FFFF (256KB)    │")
    print("   │         Bootloader 区域             │")
    print("   │    (slave_bootloader.bin)           │")
    print("   ├─────────────────────────────────────┤")
    print("   │  0x08040000 - 0x081FFFFF (1.75MB)   │")
    print("   │        Application 区域             │")
    print("   │         (slave.bin)                 │")
    print("   └─────────────────────────────────────┘")
    print()
    
    # 2. 构建顺序
    print("2. 正确的构建顺序:")
    print("   步骤1: 构建 slave_bootloader")
    print("          - 生成 slave_bootloader.bin")
    print("          - 大小限制: 256KB (0x40000)")
    print("   步骤2: 构建 slave (引用 bootloader)")
    print("          - 在 mbed_app.json 中配置 target.bootloader_img")
    print("          - 生成包含 bootloader 的完整固件")
    print()
    
    # 3. 配置文件分析
    print("3. 关键配置文件:")
    
    # 检查 bootloader 配置
    bootloader_config = bootloader_dir / "mbed_app.json"
    if bootloader_config.exists():
        print(f"   ✓ Bootloader配置: {bootloader_config}")
        try:
            with open(bootloader_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'target_overrides' in config and 'NUCLEO_F429ZI' in config['target_overrides']:
                    target_config = config['target_overrides']['NUCLEO_F429ZI']
                    if 'target.restrict_size' in target_config:
                        print(f"     - 大小限制: {target_config['target.restrict_size']}")
        except Exception as e:
            print(f"     - 配置读取错误: {e}")
    else:
        print(f"   ✗ Bootloader配置不存在: {bootloader_config}")
    
    # 检查应用程序配置
    app_config = application_dir / "mbed_app.json"
    if app_config.exists():
        print(f"   ✓ 应用程序配置: {app_config}")
        try:
            with open(app_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'target_overrides' in config and 'NUCLEO_F429ZI' in config['target_overrides']:
                    target_config = config['target_overrides']['NUCLEO_F429ZI']
                    if 'target.bootloader_img' in target_config:
                        print(f"     - Bootloader引用: {target_config['target.bootloader_img']}")
        except Exception as e:
            print(f"     - 配置读取错误: {e}")
    else:
        print(f"   ✗ 应用程序配置不存在: {app_config}")
    print()
    
    # 4. 生成的文件
    print("4. 生成的关键文件:")
    
    # 检查 bootloader 二进制文件
    bootloader_bin = bootloader_dir / "BUILD" / "NUCLEO_F429ZI" / "GCC_ARM-RELEASE" / "slave_bootloader.bin"
    if bootloader_bin.exists():
        size = bootloader_bin.stat().st_size
        print(f"   ✓ Bootloader二进制: {bootloader_bin}")
        print(f"     - 大小: {size} bytes ({size/1024:.1f} KB)")
    else:
        print(f"   ✗ Bootloader二进制不存在: {bootloader_bin}")
    
    # 检查应用程序二进制文件
    app_bin = application_dir / "BUILD" / "NUCLEO_F429ZI" / "GCC_ARM-RELEASE" / "slave.bin"
    if app_bin.exists():
        size = app_bin.stat().st_size
        print(f"   ✓ 应用程序二进制: {app_bin}")
        print(f"     - 大小: {size} bytes ({size/1024:.1f} KB)")
    else:
        print(f"   ✗ 应用程序二进制不存在: {app_bin}")
    print()
    
    # 5. 功能说明
    print("5. 功能分工:")
    print("   Bootloader (slave_bootloader):")
    print("   - 系统启动和初始化")
    print("   - 网络固件更新 (通过以太网)")
    print("   - 应用程序启动和管理")
    print("   - Flash 操作和错误处理")
    print()
    print("   Application (slave):")
    print("   - 风扇控制逻辑")
    print("   - 分布式通信")
    print("   - 传感器数据处理")
    print("   - 用户界面和状态报告")
    print()
    
    # 6. 部署说明
    print("6. 部署说明:")
    print("   方法1: 分别烧录")
    print("   - 先烧录 slave_bootloader.bin 到 0x08000000")
    print("   - 再烧录 slave.bin 到 0x08040000")
    print()
    print("   方法2: 完整固件烧录")
    print("   - 烧录包含 bootloader 的完整 slave.hex")
    print("   - 一次性完成整个系统部署")
    print()
    
    print("=" * 50)
    print("演示完成！")
    print("\n要实际构建项目，请运行:")
    print("  python build_complete_firmware.py")

if __name__ == "__main__":
    demonstrate_project_combination()
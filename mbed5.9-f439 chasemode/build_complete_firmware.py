#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fan Club MkIV 完整固件构建脚本

这个脚本解决了之前bin文件生成不完善的问题。
项目使用bootloader架构，需要按正确顺序构建：
1. 先构建bootloader
2. 然后构建应用程序（会引用bootloader）
3. 生成完整的固件文件

作者: AI Assistant
日期: 2025年1月
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class FirmwareBuilder:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.bootloader_dir = self.base_dir / "slave_bootloader"
        self.application_dir = self.base_dir / "slave"
        self.output_dir = self.base_dir / "master" / "FC_MkIV_binaries"
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message):
        """打印带时间戳的日志消息"""
        print(f"[BUILD] {message}")
        
    def run_command(self, cmd, cwd=None, check=True):
        """运行命令并返回结果"""
        self.log(f"执行命令: {' '.join(cmd)}")
        if cwd:
            self.log(f"工作目录: {cwd}")
            
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                check=check
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"命令执行失败: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            if check:
                raise
            return e
            
    def check_mbed_cli(self):
        """检查mbed-cli是否可用"""
        try:
            result = self.run_command(["mbed", "--version"])
            self.log(f"Mbed CLI版本: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("错误: 未找到mbed-cli，请先安装")
            self.log("安装命令: pip install mbed-cli")
            return False
            
    def backup_config(self, config_path):
        """备份配置文件"""
        if config_path.exists():
            backup_path = config_path.with_suffix(config_path.suffix + '.backup')
            shutil.copy2(config_path, backup_path)
            self.log(f"已备份配置文件: {backup_path}")
            
    def create_bootloader_config(self):
        """创建bootloader的mbed_app.json配置"""
        config_path = self.bootloader_dir / "mbed_app.json"
        self.backup_config(config_path)
        
        # Bootloader配置 - 简化版本，避免冲突
        bootloader_config = {
            "target_overrides": {
                "*": {
                    "platform.stdio-baud-rate": 115200,
                    "platform.default-serial-baud-rate": 115200,
                    "platform.stdio-convert-newlines": True,
                    "platform.stdio-buffered-serial": True
                },
                "NUCLEO_F439ZI": {
                    # Bootloader不需要引用自己
                    "target.restrict_size": "0x40000"  # 256KB for bootloader
                }
            },
            "config": {
                "mesh-heap-size": {
                    "help": "Mesh API heap size",
                    "value": 32500
                }
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(bootloader_config, f, indent=2, ensure_ascii=False)
            
        self.log(f"已创建bootloader配置: {config_path}")
        
    def create_application_config(self):
        """创建应用程序的mbed_app.json配置"""
        config_path = self.application_dir / "mbed_app.json"
        self.backup_config(config_path)
        
        # 应用程序配置 - 引用bootloader
        app_config = {
            "target_overrides": {
                "*": {
                    "platform.stdio-baud-rate": 115200,
                    # 移除所有可能冲突的功能
                    "target.features_remove": [
                        "LWIP",
                        "NETSOCKET", 
                        "STORAGE",
                        "FILESYSTEM",
                        "BLE",
                        "CELLULAR",
                        "LORAWAN",
                        "WIFI",
                        "ETHERNET",
                        "USB",
                        "USBDEVICE",
                        "USBHOST"
                    ],
                    "target.components_remove": [
                        "SD",
                        "FLASHIAP",
                        "QSPIF",
                        "SPIF",
                        "DATAFLASH",
                        "WIFI_ESP8266",
                        "WIFI_ISM43362",
                        "WIFI_RTW",
                        "CELLULAR_QUECTEL",
                        "CELLULAR_UBLOX",
                        "CELLULAR_TELIT"
                    ]
                },
                "NUCLEO_F439ZI": {
                    # 引用bootloader二进制文件
                    "target.bootloader_img": "../slave_bootloader/BUILD/NUCLEO_F439ZI/GCC_ARM-RELEASE/slave_bootloader.bin"
                }
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(app_config, f, indent=2, ensure_ascii=False)
            
        self.log(f"已创建应用程序配置: {config_path}")
        
    def build_bootloader(self):
        """构建bootloader"""
        self.log("开始构建bootloader...")
        
        # 创建bootloader配置
        self.create_bootloader_config()
        
        # 清理之前的构建
        build_dir = self.bootloader_dir / "BUILD"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            self.log("已清理bootloader构建目录")
            
        # 构建bootloader
        cmd = ["mbed", "compile", "-t", "GCC_ARM", "-m", "NUCLEO_F439ZI", "--profile", "release"]
        result = self.run_command(cmd, cwd=self.bootloader_dir)
        
        # 检查bootloader二进制文件是否生成
        bootloader_bin = self.bootloader_dir / "BUILD" / "NUCLEO_F439ZI" / "GCC_ARM-RELEASE" / "slave_bootloader.bin"
        if bootloader_bin.exists():
            self.log(f"✓ Bootloader构建成功: {bootloader_bin}")
            self.log(f"Bootloader大小: {bootloader_bin.stat().st_size} bytes")
            return True
        else:
            self.log("✗ Bootloader构建失败")
            return False
            
    def build_application(self):
        """构建应用程序"""
        self.log("开始构建应用程序...")
        
        # 创建应用程序配置
        self.create_application_config()
        
        # 清理之前的构建
        build_dir = self.application_dir / "BUILD"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            self.log("已清理应用程序构建目录")
            
        # 构建应用程序
        cmd = ["mbed", "compile", "-t", "GCC_ARM", "-m", "NUCLEO_F439ZI", "--profile", "release"]
        result = self.run_command(cmd, cwd=self.application_dir)
        
        # 检查应用程序二进制文件是否生成
        app_bin = self.application_dir / "BUILD" / "NUCLEO_F439ZI" / "GCC_ARM-RELEASE" / "slave.bin"
        if app_bin.exists():
            self.log(f"✓ 应用程序构建成功: {app_bin}")
            self.log(f"应用程序大小: {app_bin.stat().st_size} bytes")
            return True
        else:
            self.log("✗ 应用程序构建失败")
            return False
            
    def copy_binaries(self):
        """复制二进制文件到输出目录"""
        self.log("复制二进制文件到输出目录...")
        
        # 复制bootloader
        bootloader_src = self.bootloader_dir / "BUILD" / "NUCLEO_F439ZI" / "GCC_ARM-RELEASE" / "slave_bootloader.bin"
        bootloader_dst = self.output_dir / "Slave_Bootloader.bin"
        
        if bootloader_src.exists():
            shutil.copy2(bootloader_src, bootloader_dst)
            self.log(f"✓ 已复制bootloader: {bootloader_dst}")
        else:
            self.log("✗ Bootloader二进制文件不存在")
            
        # 复制应用程序
        app_src = self.application_dir / "BUILD" / "NUCLEO_F439ZI" / "GCC_ARM-RELEASE" / "slave.bin"
        app_dst = self.output_dir / "Slave_application.bin"
        
        if app_src.exists():
            shutil.copy2(app_src, app_dst)
            self.log(f"✓ 已复制应用程序: {app_dst}")
        else:
            self.log("✗ 应用程序二进制文件不存在")
            
        # 复制完整固件（如果存在）
        full_firmware_src = self.application_dir / "BUILD" / "NUCLEO_F439ZI" / "GCC_ARM-RELEASE" / "slave.hex"
        if full_firmware_src.exists():
            full_firmware_dst = self.output_dir / "Slave_complete.hex"
            shutil.copy2(full_firmware_src, full_firmware_dst)
            self.log(f"✓ 已复制完整固件: {full_firmware_dst}")
            
    def generate_build_info(self):
        """生成构建信息文件"""
        info_file = self.output_dir / "build_info.txt"
        
        bootloader_bin = self.output_dir / "Slave_Bootloader.bin"
        app_bin = self.output_dir / "Slave_application.bin"
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("Fan Club MkIV 固件构建信息\n")
            f.write("=" * 40 + "\n\n")
            
            if bootloader_bin.exists():
                f.write(f"Bootloader: {bootloader_bin.name}\n")
                f.write(f"大小: {bootloader_bin.stat().st_size} bytes\n\n")
            
            if app_bin.exists():
                f.write(f"应用程序: {app_bin.name}\n")
                f.write(f"大小: {app_bin.stat().st_size} bytes\n\n")
                
            f.write("构建说明:\n")
            f.write("1. Bootloader负责固件更新和应用程序启动\n")
            f.write("2. 应用程序包含主要的风扇控制逻辑\n")
            f.write("3. 两个文件都需要烧录到目标设备\n")
            f.write("4. Bootloader烧录地址: 0x08000000\n")
            f.write("5. 应用程序由bootloader自动加载\n")
            
        self.log(f"✓ 已生成构建信息: {info_file}")
        
    def build_all(self):
        """构建完整固件"""
        self.log("开始构建Fan Club MkIV完整固件...")
        
        # 检查mbed-cli
        if not self.check_mbed_cli():
            return False
            
        try:
            # 步骤1: 构建bootloader
            if not self.build_bootloader():
                self.log("Bootloader构建失败，停止构建")
                return False
                
            # 步骤2: 构建应用程序
            if not self.build_application():
                self.log("应用程序构建失败，停止构建")
                return False
                
            # 步骤3: 复制二进制文件
            self.copy_binaries()
            
            # 步骤4: 生成构建信息
            self.generate_build_info()
            
            self.log("\n" + "=" * 50)
            self.log("✓ 完整固件构建成功！")
            self.log(f"输出目录: {self.output_dir}")
            self.log("=" * 50)
            
            return True
            
        except Exception as e:
            self.log(f"构建过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    # 获取脚本所在目录作为基础目录
    base_dir = Path(__file__).parent
    
    print("Fan Club MkIV 完整固件构建脚本")
    print("=" * 40)
    print(f"基础目录: {base_dir}")
    print()
    
    # 创建构建器并开始构建
    builder = FirmwareBuilder(base_dir)
    success = builder.build_all()
    
    if success:
        print("\n构建完成！可以在以下位置找到生成的文件:")
        print(f"  - {builder.output_dir}")
        sys.exit(0)
    else:
        print("\n构建失败！请检查错误信息。")
        sys.exit(1)

if __name__ == "__main__":
    main()
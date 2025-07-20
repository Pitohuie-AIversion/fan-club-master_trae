#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fan Club MkIV - 自动化固件编译脚本

此脚本自动编译 Fan Club MkIV 项目的固件文件：
- 从机固件 (slave_upgraded)
- 引导程序固件 (slave_bootloader_upgraded)

使用方法:
    python build_firmware.py
    python build_firmware.py --clean  # 清理后编译
    python build_firmware.py --verbose  # 详细输出
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

class FirmwareBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.slave_dir = self.project_root / "slave_upgraded"
        self.bootloader_dir = self.project_root / "slave_bootloader_upgraded"
        self.output_dir = self.project_root / "master" / "FC_MkIV_binaries"
        
        # 编译配置
        self.target = "NUCLEO_F446RE"
        self.toolchain = "ARMC6"
        
        # 统计信息
        self.start_time = None
        self.build_results = []
        
    def log(self, message, level="INFO"):
        """输出日志信息"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(level, "📝")
        print(f"[{timestamp}] {prefix} {message}")
        
    def check_environment(self):
        """检查编译环境"""
        self.log("检查编译环境...")
        
        # 检查 Mbed CLI
        try:
            result = subprocess.run(["mbed", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"Mbed CLI 版本: {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("Mbed CLI 未找到或版本检查失败", "ERROR")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log("Mbed CLI 未安装或不在 PATH 中", "ERROR")
            return False
            
        # 检查项目目录
        if not self.slave_dir.exists():
            self.log(f"从机项目目录不存在: {self.slave_dir}", "ERROR")
            return False
            
        if not self.bootloader_dir.exists():
            self.log(f"引导程序项目目录不存在: {self.bootloader_dir}", "ERROR")
            return False
            
        # 检查 mbed-os.lib
        slave_lib = self.slave_dir / "mbed-os.lib"
        bootloader_lib = self.bootloader_dir / "mbed-os.lib"
        
        if not slave_lib.exists():
            self.log(f"从机项目缺少 mbed-os.lib", "WARNING")
            
        if not bootloader_lib.exists():
            self.log(f"引导程序项目缺少 mbed-os.lib", "WARNING")
            
        self.log("环境检查完成", "SUCCESS")
        return True
        
    def clean_build(self, project_dir):
        """清理构建目录"""
        build_dir = project_dir / "BUILD"
        if build_dir.exists():
            self.log(f"清理构建目录: {build_dir}")
            try:
                import shutil
                shutil.rmtree(build_dir)
                self.log("构建目录已清理", "SUCCESS")
            except Exception as e:
                self.log(f"清理构建目录失败: {e}", "WARNING")
                
    def deploy_dependencies(self, project_dir):
        """部署项目依赖"""
        self.log(f"部署依赖: {project_dir.name}")
        try:
            result = subprocess.run(["mbed", "deploy"], 
                                  cwd=project_dir, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)
            if result.returncode == 0:
                self.log("依赖部署成功", "SUCCESS")
                return True
            else:
                self.log(f"依赖部署失败: {result.stderr}", "WARNING")
                return False
        except subprocess.TimeoutExpired:
            self.log("依赖部署超时", "ERROR")
            return False
        except Exception as e:
            self.log(f"依赖部署异常: {e}", "ERROR")
            return False
            
    def compile_project(self, project_dir, project_name, verbose=False):
        """编译单个项目"""
        self.log(f"开始编译: {project_name}")
        
        # 构建编译命令
        cmd = ["mbed", "compile", "-t", self.toolchain, "-m", self.target]
        if verbose:
            cmd.append("-v")
            
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, 
                                  cwd=project_dir, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=600)  # 10分钟超时
            
            compile_time = time.time() - start_time
            
            if result.returncode == 0:
                self.log(f"{project_name} 编译成功 ({compile_time:.1f}s)", "SUCCESS")
                
                # 查找生成的 bin 文件
                bin_files = list(project_dir.glob(f"BUILD/{self.target}/{self.toolchain}/*.bin"))
                if bin_files:
                    bin_file = bin_files[0]
                    file_size = bin_file.stat().st_size
                    self.log(f"生成固件: {bin_file.name} ({file_size:,} bytes)")
                    
                    self.build_results.append({
                        "project": project_name,
                        "success": True,
                        "time": compile_time,
                        "bin_file": bin_file,
                        "size": file_size
                    })
                    return True
                else:
                    self.log(f"{project_name} 编译成功但未找到 bin 文件", "WARNING")
                    
            else:
                self.log(f"{project_name} 编译失败", "ERROR")
                if verbose:
                    self.log(f"错误输出: {result.stderr}")
                    
                self.build_results.append({
                    "project": project_name,
                    "success": False,
                    "time": compile_time,
                    "error": result.stderr
                })
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"{project_name} 编译超时", "ERROR")
            self.build_results.append({
                "project": project_name,
                "success": False,
                "time": 600,
                "error": "编译超时"
            })
            return False
        except Exception as e:
            self.log(f"{project_name} 编译异常: {e}", "ERROR")
            self.build_results.append({
                "project": project_name,
                "success": False,
                "time": 0,
                "error": str(e)
            })
            return False
            
    def copy_binaries(self):
        """复制生成的固件到输出目录"""
        self.log("复制固件文件...")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        for result in self.build_results:
            if result["success"] and "bin_file" in result:
                src_file = result["bin_file"]
                dst_file = self.output_dir / src_file.name
                
                try:
                    import shutil
                    shutil.copy2(src_file, dst_file)
                    self.log(f"已复制: {src_file.name} -> {dst_file}")
                    copied_count += 1
                except Exception as e:
                    self.log(f"复制失败 {src_file.name}: {e}", "ERROR")
                    
        if copied_count > 0:
            self.log(f"已复制 {copied_count} 个固件文件到 {self.output_dir}", "SUCCESS")
        else:
            self.log("没有固件文件被复制", "WARNING")
            
    def generate_report(self):
        """生成编译报告"""
        total_time = time.time() - self.start_time
        success_count = sum(1 for r in self.build_results if r["success"])
        total_count = len(self.build_results)
        
        self.log("=" * 50)
        self.log("编译报告")
        self.log("=" * 50)
        self.log(f"总耗时: {total_time:.1f} 秒")
        self.log(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        for result in self.build_results:
            status = "✅" if result["success"] else "❌"
            project = result["project"]
            time_str = f"{result['time']:.1f}s"
            
            if result["success"] and "size" in result:
                size_str = f" ({result['size']:,} bytes)"
                self.log(f"{status} {project}: {time_str}{size_str}")
            else:
                error = result.get("error", "未知错误")
                self.log(f"{status} {project}: {time_str} - {error}")
                
        self.log("=" * 50)
        
        if success_count == total_count:
            self.log("🎉 所有固件编译成功！", "SUCCESS")
            self.log(f"固件位置: {self.output_dir}")
            return True
        else:
            self.log(f"⚠️ {total_count - success_count} 个项目编译失败", "WARNING")
            return False
            
    def build_all(self, clean=False, verbose=False):
        """编译所有固件"""
        self.start_time = time.time()
        self.log("开始 Fan Club MkIV 固件编译")
        
        # 检查环境
        if not self.check_environment():
            return False
            
        # 编译项目列表
        projects = [
            (self.slave_dir, "从机固件 (slave_upgraded)"),
            (self.bootloader_dir, "引导程序固件 (slave_bootloader_upgraded)")
        ]
        
        success = True
        
        for project_dir, project_name in projects:
            self.log(f"处理项目: {project_name}")
            
            # 清理构建（如果需要）
            if clean:
                self.clean_build(project_dir)
                
            # 部署依赖
            self.deploy_dependencies(project_dir)
            
            # 编译项目
            if not self.compile_project(project_dir, project_name, verbose):
                success = False
                
        # 复制固件文件
        self.copy_binaries()
        
        # 生成报告
        report_success = self.generate_report()
        
        return success and report_success

def main():
    parser = argparse.ArgumentParser(description="Fan Club MkIV 固件编译工具")
    parser.add_argument("--clean", action="store_true", 
                       help="编译前清理构建目录")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="显示详细编译输出")
    
    args = parser.parse_args()
    
    builder = FirmwareBuilder()
    
    try:
        success = builder.build_all(clean=args.clean, verbose=args.verbose)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        builder.log("编译被用户中断", "WARNING")
        sys.exit(1)
    except Exception as e:
        builder.log(f"编译过程发生异常: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
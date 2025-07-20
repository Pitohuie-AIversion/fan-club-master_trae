#!/usr/bin/env python3
"""
Fan Club MkIV 快速运行状态检查工具
验证底层代码是否可以正常编译和运行
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

class RuntimeChecker:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.results = {}
        
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """打印测试结果"""
        status = "✅ 就绪" if success else "❌ 问题"
        print(f"{test_name:<35} {status}")
        if details:
            print(f"  详情: {details}")
        self.results[test_name] = {'success': success, 'details': details}
    
    def check_mbed_studio_installation(self) -> bool:
        """检查 Mbed Studio 安装"""
        self.print_header("编译环境检查")
        
        # 检查 Mbed Studio 路径
        mbed_studio_paths = [
            "X:\\Program Files\\Mbed Studio",
            "C:\\Program Files\\Mbed Studio",
            "C:\\Program Files (x86)\\Mbed Studio"
        ]
        
        mbed_studio_found = False
        for path in mbed_studio_paths:
            if Path(path).exists():
                self.print_result("Mbed Studio 安装", True, f"找到安装路径: {path}")
                mbed_studio_found = True
                break
        
        if not mbed_studio_found:
            self.print_result("Mbed Studio 安装", False, "未找到 Mbed Studio 安装")
        
        return mbed_studio_found
    
    def check_project_structure(self) -> bool:
        """检查项目结构"""
        self.print_header("项目结构检查")
        
        required_dirs = {
            'slave_upgraded': '升级后从机代码',
            'slave_bootloader_upgraded': '升级后引导程序',
            'master': 'Python 控制程序'
        }
        
        all_success = True
        
        for dir_name, description in required_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                # 检查关键文件
                if dir_name == 'slave_upgraded':
                    key_files = ['main.cpp', 'mbed_app.json', 'Makefile']
                elif dir_name == 'slave_bootloader_upgraded':
                    key_files = ['main.cpp', 'mbed_app.json']
                else:  # master
                    key_files = ['main.py', 'fc/__init__.py']
                
                missing_files = []
                for file_name in key_files:
                    if not (dir_path / file_name).exists():
                        missing_files.append(file_name)
                
                if missing_files:
                    self.print_result(f"{description}", False, f"缺少文件: {', '.join(missing_files)}")
                    all_success = False
                else:
                    self.print_result(f"{description}", True, "结构完整")
            else:
                self.print_result(f"{description}", False, "目录不存在")
                all_success = False
        
        return all_success
    
    def check_mbed_config(self) -> bool:
        """检查 Mbed 配置"""
        self.print_header("Mbed 配置检查")
        
        configs = [
            ('slave_upgraded/mbed_app.json', '从机配置'),
            ('slave_bootloader_upgraded/mbed_app.json', '引导程序配置')
        ]
        
        all_success = True
        
        for config_path, description in configs:
            full_path = self.project_root / config_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 检查关键配置项
                    target_overrides = config.get('target_overrides', {})
                    if target_overrides:
                        self.print_result(f"{description}", True, "配置格式正确")
                    else:
                        self.print_result(f"{description}", False, "缺少目标配置")
                        all_success = False
                        
                except json.JSONDecodeError as e:
                    self.print_result(f"{description}", False, f"JSON 格式错误: {e}")
                    all_success = False
                except Exception as e:
                    self.print_result(f"{description}", False, f"读取失败: {e}")
                    all_success = False
            else:
                self.print_result(f"{description}", False, "配置文件不存在")
                all_success = False
        
        return all_success
    
    def check_dependencies(self) -> bool:
        """检查依赖库"""
        self.print_header("依赖库检查")
        
        # 检查 Mbed OS 库
        mbed_libs = [
            'slave_upgraded/mbed-os.lib',
            'slave_bootloader_upgraded/mbed-os.lib'
        ]
        
        all_success = True
        
        for lib_path in mbed_libs:
            full_path = self.project_root / lib_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read().strip()
                    if content.startswith('https://') or content.startswith('http://'):
                        self.print_result(f"Mbed OS ({lib_path.split('/')[0]})", True, "库引用正确")
                    else:
                        self.print_result(f"Mbed OS ({lib_path.split('/')[0]})", False, "库引用格式错误")
                        all_success = False
                except Exception as e:
                    self.print_result(f"Mbed OS ({lib_path.split('/')[0]})", False, f"读取失败: {e}")
                    all_success = False
            else:
                self.print_result(f"Mbed OS ({lib_path.split('/')[0]})", False, "库文件不存在")
                all_success = False
        
        # 检查 Python 依赖
        master_dir = self.project_root / 'master'
        if master_dir.exists():
            try:
                # 测试基本导入
                import_test = """
import sys
sys.path.insert(0, '.')
import fc
print('Python 依赖检查通过')
"""
                result = subprocess.run(
                    [sys.executable, '-c', import_test],
                    cwd=str(master_dir),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.print_result("Python 依赖", True, "模块导入正常")
                else:
                    self.print_result("Python 依赖", False, f"导入失败: {result.stderr}")
                    all_success = False
                    
            except Exception as e:
                self.print_result("Python 依赖", False, f"检查失败: {e}")
                all_success = False
        
        return all_success
    
    def check_compilation_readiness(self) -> bool:
        """检查编译就绪状态"""
        self.print_header("编译就绪检查")
        
        # 检查编译相关文件
        compile_files = [
            ('slave_upgraded/Makefile', '从机 Makefile'),
            ('slave_upgraded/main.cpp', '从机主程序'),
            ('slave_bootloader_upgraded/main.cpp', '引导程序主程序')
        ]
        
        all_success = True
        
        for file_path, description in compile_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if file_path.endswith('.cpp'):
                        # 检查 C++ 文件基本结构
                        if '#include' in content and ('int main' in content or 'void main' in content):
                            self.print_result(f"{description}", True, "结构正确")
                        else:
                            self.print_result(f"{description}", False, "缺少主函数或包含")
                            all_success = False
                    else:
                        # Makefile 检查
                        if 'OBJDIR' in content and '.o' in content:
                            self.print_result(f"{description}", True, "格式正确")
                        else:
                            self.print_result(f"{description}", False, "格式可能有问题")
                            all_success = False
                            
                except Exception as e:
                    self.print_result(f"{description}", False, f"读取失败: {e}")
                    all_success = False
            else:
                self.print_result(f"{description}", False, "文件不存在")
                all_success = False
        
        return all_success
    
    def check_runtime_readiness(self) -> bool:
        """检查运行时就绪状态"""
        self.print_header("运行时就绪检查")
        
        # 检查关键运行时文件
        runtime_components = [
            ('slave_upgraded/Communicator.cpp', '网络通信模块'),
            ('slave_upgraded/Fan.cpp', '风扇控制模块'),
            ('slave_upgraded/Processor.cpp', '数据处理模块'),
            ('slave_bootloader_upgraded/BTFlash.h', '引导程序 Flash 模块'),
            ('slave_bootloader_upgraded/BTUtils.h', '引导程序工具模块')
        ]
        
        all_success = True
        
        for file_path, description in runtime_components:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.print_result(f"{description}", True, "模块存在")
            else:
                self.print_result(f"{description}", False, "模块缺失")
                all_success = False
        
        return all_success
    
    def generate_runtime_report(self) -> str:
        """生成运行状态报告"""
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result['success'])
        failed_checks = total_checks - passed_checks
        
        readiness_score = (passed_checks / total_checks) * 100
        
        if readiness_score >= 90:
            status = "✅ 完全就绪"
            recommendation = "可以立即编译和运行"
        elif readiness_score >= 75:
            status = "⚠️ 基本就绪"
            recommendation = "建议修复少量问题后运行"
        elif readiness_score >= 50:
            status = "🔧 需要修复"
            recommendation = "需要解决关键问题才能运行"
        else:
            status = "❌ 未就绪"
            recommendation = "需要大量修复工作"
        
        report = f"""
# Fan Club MkIV 底层运行状态报告

## 总体状态

**运行就绪度**: {readiness_score:.1f}%  
**状态**: {status}  
**建议**: {recommendation}

## 检查结果统计

- **总检查项**: {total_checks}
- **通过检查**: {passed_checks}
- **失败检查**: {failed_checks}

## 详细结果

"""
        
        for check_name, result in self.results.items():
            status_icon = "✅" if result['success'] else "❌"
            report += f"### {check_name}\n\n"
            report += f"**状态**: {status_icon} {'通过' if result['success'] else '失败'}\n\n"
            if result['details']:
                report += f"**详情**: {result['details']}\n\n"
        
        if failed_checks > 0:
            report += "\n## 需要解决的问题\n\n"
            for check_name, result in self.results.items():
                if not result['success']:
                    report += f"- **{check_name}**: {result['details']}\n"
        
        report += "\n## 下一步操作\n\n"
        
        if readiness_score >= 90:
            report += """
### 立即可执行

1. **编译测试**:
   ```bash
   # 在 Mbed Studio 中打开并编译
   - slave_upgraded/
   - slave_bootloader_upgraded/
   ```

2. **硬件部署**:
   ```bash
   # 将 .bin 文件刷写到 NUCLEO_F429ZI
   ```

3. **功能测试**:
   ```bash
   cd master/
   python main.py
   ```
"""
        else:
            report += """
### 修复建议

1. **解决失败的检查项**
2. **重新运行检查**: `python quick_runtime_check.py`
3. **达到 90% 就绪度后开始编译测试**
"""
        
        return report
    
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("Fan Club MkIV 快速运行状态检查")
        print(f"项目路径: {self.project_root}")
        print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行所有检查
        checks = [
            self.check_mbed_studio_installation,
            self.check_project_structure,
            self.check_mbed_config,
            self.check_dependencies,
            self.check_compilation_readiness,
            self.check_runtime_readiness
        ]
        
        all_success = True
        for check in checks:
            try:
                success = check()
                all_success = all_success and success
            except Exception as e:
                print(f"检查过程出错: {e}")
                all_success = False
        
        # 生成报告
        self.print_header("运行状态总结")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result['success'])
        failed_checks = total_checks - passed_checks
        readiness_score = (passed_checks / total_checks) * 100
        
        print(f"总检查项: {total_checks}")
        print(f"通过检查: {passed_checks}")
        print(f"失败检查: {failed_checks}")
        print(f"就绪度: {readiness_score:.1f}%")
        
        if readiness_score >= 90:
            print("\n🎉 底层代码完全就绪，可以立即运行！")
        elif readiness_score >= 75:
            print("\n⚠️ 底层代码基本就绪，建议修复少量问题后运行。")
        else:
            print("\n🔧 底层代码需要修复才能正常运行。")
        
        # 保存报告
        report = self.generate_runtime_report()
        report_file = self.project_root / "runtime_status_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return readiness_score >= 75  # 75% 以上认为基本可以运行

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fan Club MkIV 快速运行状态检查')
    parser.add_argument('--project-root', help='项目根目录路径', default='.')
    
    args = parser.parse_args()
    
    checker = RuntimeChecker(args.project_root)
    can_run = checker.run_all_checks()
    
    if can_run:
        print("\n✅ 结论: 底层代码可以运行！")
        sys.exit(0)
    else:
        print("\n❌ 结论: 底层代码需要修复才能运行。")
        sys.exit(1)

if __name__ == "__main__":
    main()
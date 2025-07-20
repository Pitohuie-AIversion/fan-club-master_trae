#!/usr/bin/env python3
"""
Fan Club MkIV 自动化调试工具
一键运行代码质量检查、静态分析和基础测试
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

class AutoDebugger:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.results = {}
        self.start_time = time.time()
        
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """打印测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<30} {status}")
        if details:
            print(f"  详情: {details}")
        self.results[test_name] = {'success': success, 'details': details}
    
    def run_command(self, cmd: List[str], cwd: str = None, timeout: int = 300) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except FileNotFoundError:
            return False, "", f"命令未找到: {cmd[0]}"
        except Exception as e:
            return False, "", str(e)
    
    def check_python_syntax(self) -> bool:
        """检查 Python 语法"""
        self.print_header("Python 语法检查")
        
        master_dir = self.project_root / "master"
        if not master_dir.exists():
            self.print_result("Python 语法检查", False, "master 目录不存在")
            return False
        
        # 查找所有 Python 文件
        python_files = list(master_dir.rglob("*.py"))
        
        if not python_files:
            self.print_result("Python 语法检查", False, "未找到 Python 文件")
            return False
        
        syntax_errors = []
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
            except Exception as e:
                syntax_errors.append(f"{py_file}: {e}")
        
        if syntax_errors:
            self.print_result("Python 语法检查", False, f"{len(syntax_errors)} 个文件有语法错误")
            for error in syntax_errors[:5]:  # 只显示前5个错误
                print(f"    {error}")
            return False
        else:
            self.print_result("Python 语法检查", True, f"检查了 {len(python_files)} 个文件")
            return True
    
    def check_cpp_syntax(self) -> bool:
        """检查 C++ 语法"""
        self.print_header("C++ 语法检查")
        
        cpp_dirs = ['slave_upgraded', 'slave_bootloader_upgraded']
        all_success = True
        
        for cpp_dir in cpp_dirs:
            dir_path = self.project_root / cpp_dir
            if not dir_path.exists():
                self.print_result(f"C++ 语法检查 ({cpp_dir})", False, "目录不存在")
                all_success = False
                continue
            
            # 查找 C++ 文件
            cpp_files = list(dir_path.glob("*.cpp")) + list(dir_path.glob("*.h"))
            
            if not cpp_files:
                self.print_result(f"C++ 语法检查 ({cpp_dir})", False, "未找到 C++ 文件")
                all_success = False
                continue
            
            # 简单的语法检查（查找明显的语法错误）
            syntax_issues = []
            for cpp_file in cpp_files:
                try:
                    with open(cpp_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # 检查基本的语法问题
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('//') and not line.startswith('/*'):
                            # 检查未闭合的括号（简单检查）
                            if line.count('{') != line.count('}'):
                                if '{' in line and '}' not in line:
                                    continue  # 开始块，正常
                                if '}' in line and '{' not in line:
                                    continue  # 结束块，正常
                            
                            # 检查分号
                            if (line.endswith('{') or line.endswith('}') or 
                                line.startswith('#') or line.startswith('namespace') or
                                line.startswith('class') or line.startswith('struct') or
                                'if (' in line or 'for (' in line or 'while (' in line or
                                line.endswith(',') or line.endswith('\\')):
                                continue
                            
                            if (not line.endswith(';') and not line.endswith('{') and 
                                not line.endswith('}') and len(line) > 10 and
                                '=' in line and not line.startswith('//')):
                                syntax_issues.append(f"{cpp_file}:{i} 可能缺少分号: {line[:50]}")
                                
                except Exception as e:
                    syntax_issues.append(f"{cpp_file}: 读取错误 {e}")
            
            if syntax_issues:
                self.print_result(f"C++ 语法检查 ({cpp_dir})", False, f"{len(syntax_issues)} 个潜在问题")
                for issue in syntax_issues[:3]:  # 只显示前3个问题
                    print(f"    {issue}")
                all_success = False
            else:
                self.print_result(f"C++ 语法检查 ({cpp_dir})", True, f"检查了 {len(cpp_files)} 个文件")
        
        return all_success
    
    def check_python_imports(self) -> bool:
        """检查 Python 导入"""
        self.print_header("Python 导入检查")
        
        master_dir = self.project_root / "master"
        if not master_dir.exists():
            self.print_result("Python 导入检查", False, "master 目录不存在")
            return False
        
        # 检查主要模块的导入
        main_py = master_dir / "main.py"
        if main_py.exists():
            success, stdout, stderr = self.run_command(
                [sys.executable, "-m", "py_compile", str(main_py)],
                cwd=str(master_dir)
            )
            self.print_result("main.py 编译检查", success, stderr if not success else "")
        
        # 检查 fc 模块
        fc_dir = master_dir / "fc"
        if fc_dir.exists():
            init_py = fc_dir / "__init__.py"
            if init_py.exists():
                success, stdout, stderr = self.run_command(
                    [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import fc"],
                    cwd=str(master_dir)
                )
                self.print_result("fc 模块导入检查", success, stderr if not success else "")
                return success
            else:
                self.print_result("fc 模块导入检查", False, "__init__.py 不存在")
                return False
        else:
            self.print_result("fc 模块导入检查", False, "fc 目录不存在")
            return False
    
    def check_config_files(self) -> bool:
        """检查配置文件"""
        self.print_header("配置文件检查")
        
        config_files = [
            ('slave_upgraded/mbed_app.json', 'Mbed 从机配置'),
            ('slave_bootloader_upgraded/mbed_app.json', 'Mbed 引导程序配置'),
            ('master/fc/archive.py', 'Python 配置模块')
        ]
        
        all_success = True
        
        for file_path, description in config_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    if file_path.endswith('.json'):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            json.load(f)  # 验证 JSON 格式
                        self.print_result(f"{description}", True, "JSON 格式正确")
                    elif file_path.endswith('.py'):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), full_path, 'exec')
                        self.print_result(f"{description}", True, "Python 语法正确")
                except json.JSONDecodeError as e:
                    self.print_result(f"{description}", False, f"JSON 格式错误: {e}")
                    all_success = False
                except SyntaxError as e:
                    self.print_result(f"{description}", False, f"Python 语法错误: {e}")
                    all_success = False
                except Exception as e:
                    self.print_result(f"{description}", False, f"检查失败: {e}")
                    all_success = False
            else:
                self.print_result(f"{description}", False, "文件不存在")
                all_success = False
        
        return all_success
    
    def check_file_structure(self) -> bool:
        """检查文件结构"""
        self.print_header("文件结构检查")
        
        required_structure = {
            'master': ['main.py', 'fc'],
            'slave_upgraded': ['main.cpp', 'mbed_app.json', 'Makefile'],
            'slave_bootloader_upgraded': ['main.cpp', 'mbed_app.json'],
            '.': ['README.md', 'Fan_Club_MkIV_Wiki.md']
        }
        
        all_success = True
        
        for dir_name, required_files in required_structure.items():
            dir_path = self.project_root if dir_name == '.' else self.project_root / dir_name
            
            if not dir_path.exists():
                self.print_result(f"目录结构 ({dir_name})", False, "目录不存在")
                all_success = False
                continue
            
            missing_files = []
            for required_file in required_files:
                file_path = dir_path / required_file
                if not file_path.exists():
                    missing_files.append(required_file)
            
            if missing_files:
                self.print_result(
                    f"目录结构 ({dir_name})", 
                    False, 
                    f"缺少文件: {', '.join(missing_files)}"
                )
                all_success = False
            else:
                self.print_result(f"目录结构 ({dir_name})", True, "所有必需文件存在")
        
        return all_success
    
    def check_documentation(self) -> bool:
        """检查文档完整性"""
        self.print_header("文档完整性检查")
        
        doc_files = [
            ('README.md', '项目说明文档'),
            ('Fan_Club_MkIV_Wiki.md', '项目 Wiki'),
            ('COMPILATION_SETUP_GUIDE.md', '编译设置指南'),
            ('Mbed_Library_Upgrade_Guide.md', 'Mbed 升级指南'),
            ('UPGRADE_README.md', '升级说明'),
            ('AUTOMATED_DEBUGGING_GUIDE.md', '自动化调试指南')
        ]
        
        all_success = True
        
        for file_name, description in doc_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) < 100:
                        self.print_result(f"{description}", False, "文档内容过短")
                        all_success = False
                    elif not content.strip().startswith('#'):
                        self.print_result(f"{description}", False, "不是有效的 Markdown 格式")
                        all_success = False
                    else:
                        self.print_result(f"{description}", True, f"文档长度: {len(content)} 字符")
                except Exception as e:
                    self.print_result(f"{description}", False, f"读取失败: {e}")
                    all_success = False
            else:
                self.print_result(f"{description}", False, "文档不存在")
                all_success = False
        
        return all_success
    
    def run_basic_tests(self) -> bool:
        """运行基础测试"""
        self.print_header("基础功能测试")
        
        # 测试 Python 模块导入
        master_dir = self.project_root / "master"
        if master_dir.exists():
            test_script = """
import sys
import os
sys.path.insert(0, '.')

try:
    # 测试基础导入
    import fc
    print("fc 模块导入成功")
    
    # 测试子模块
    from fc import archive, standards, utils
    print("子模块导入成功")
    
    # 测试基础功能
    if hasattr(utils, 'platform'):
        platform = utils.platform()
        print(f"平台检测: {platform}")
    
    print("基础测试通过")
except Exception as e:
    print(f"测试失败: {e}")
    sys.exit(1)
"""
            
            success, stdout, stderr = self.run_command(
                [sys.executable, "-c", test_script],
                cwd=str(master_dir)
            )
            
            self.print_result("Python 模块测试", success, stdout if success else stderr)
            return success
        else:
            self.print_result("Python 模块测试", False, "master 目录不存在")
            return False
    
    def generate_report(self) -> str:
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        elapsed_time = time.time() - self.start_time
        
        report = f"""
# Fan Club MkIV 自动化调试报告

**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**执行时间**: {elapsed_time:.2f} 秒
**总测试数**: {total_tests}
**通过测试**: {passed_tests}
**失败测试**: {failed_tests}
**成功率**: {(passed_tests/total_tests*100):.1f}%

## 测试结果详情

"""
        
        for test_name, result in self.results.items():
            status = "✅ 通过" if result['success'] else "❌ 失败"
            report += f"### {test_name}\n\n"
            report += f"**状态**: {status}\n\n"
            if result['details']:
                report += f"**详情**: {result['details']}\n\n"
        
        if failed_tests > 0:
            report += "\n## 建议修复措施\n\n"
            for test_name, result in self.results.items():
                if not result['success']:
                    report += f"- **{test_name}**: {result['details']}\n"
        
        return report
    
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("Fan Club MkIV 自动化调试工具")
        print(f"项目路径: {self.project_root}")
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行所有检查
        checks = [
            self.check_file_structure,
            self.check_config_files,
            self.check_python_syntax,
            self.check_cpp_syntax,
            self.check_python_imports,
            self.check_documentation,
            self.run_basic_tests
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
        self.print_header("测试总结")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 保存报告
        report = self.generate_report()
        report_file = self.project_root / "debug_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return all_success

def main():
    parser = argparse.ArgumentParser(description='Fan Club MkIV 自动化调试工具')
    parser.add_argument('--project-root', help='项目根目录路径', default='.')
    parser.add_argument('--quick', action='store_true', help='快速检查模式')
    
    args = parser.parse_args()
    
    debugger = AutoDebugger(args.project_root)
    
    if args.quick:
        # 快速模式：只运行基础检查
        success = (debugger.check_file_structure() and 
                  debugger.check_config_files() and
                  debugger.check_python_syntax())
    else:
        # 完整模式：运行所有检查
        success = debugger.run_all_checks()
    
    if success:
        print("\n🎉 所有检查通过！代码质量良好。")
        sys.exit(0)
    else:
        print("\n⚠️  发现问题，请查看上述报告进行修复。")
        sys.exit(1)

if __name__ == "__main__":
    main()
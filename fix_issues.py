#!/usr/bin/env python3
"""
Fan Club MkIV 问题修复工具
自动修复调试过程中发现的问题
"""

import os
import sys
import re
import time
from pathlib import Path
from typing import List, Dict

class IssueFixer:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.fixed_issues = []
        
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_fix(self, issue: str, success: bool, details: str = ""):
        """打印修复结果"""
        status = "✅ 已修复" if success else "❌ 修复失败"
        print(f"{issue:<40} {status}")
        if details:
            print(f"  详情: {details}")
        self.fixed_issues.append({'issue': issue, 'success': success, 'details': details})
    
    def fix_cpp_syntax_issues(self) -> bool:
        """修复 C++ 语法问题"""
        self.print_header("修复 C++ 语法问题")
        
        cpp_dirs = ['slave_upgraded', 'slave_bootloader_upgraded']
        all_success = True
        
        for cpp_dir in cpp_dirs:
            dir_path = self.project_root / cpp_dir
            if not dir_path.exists():
                continue
            
            # 查找 C++ 文件
            cpp_files = list(dir_path.glob("*.cpp")) + list(dir_path.glob("*.h"))
            
            fixed_files = []
            for cpp_file in cpp_files:
                try:
                    with open(cpp_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original_content = content
                    modified = False
                    
                    # 修复常见的语法问题
                    lines = content.split('\n')
                    new_lines = []
                    
                    for i, line in enumerate(lines):
                        original_line = line
                        stripped = line.strip()
                        
                        # 跳过注释和预处理指令
                        if (stripped.startswith('//') or stripped.startswith('/*') or 
                            stripped.startswith('#') or not stripped):
                            new_lines.append(line)
                            continue
                        
                        # 修复缺少分号的问题
                        if (not stripped.endswith((';', '{', '}', '\\', ',')) and 
                            not stripped.startswith(('namespace', 'class', 'struct', 'enum', 'if', 'for', 'while', 'switch', 'case', 'default')) and
                            ('=' in stripped or 'return' in stripped) and
                            len(stripped) > 5 and
                            not stripped.endswith(')')  and
                            not any(keyword in stripped for keyword in ['if (', 'for (', 'while (', 'switch ('])):
                            
                            # 检查是否真的需要分号
                            if (not stripped.endswith(':') and 
                                not stripped.startswith('else') and
                                not stripped.endswith('else') and
                                'cout' not in stripped):
                                line = line.rstrip() + ';'
                                modified = True
                        
                        # 修复常见的包含问题
                        if '#include' in stripped and not (stripped.endswith('.h"') or stripped.endswith('.h>')):
                            if 'mbed' in stripped.lower():
                                # 修复 mbed 包含
                                if not stripped.endswith('.h"') and not stripped.endswith('.h>'):
                                    if '"' in stripped:
                                        line = re.sub(r'#include\s*"([^"]+)"', r'#include "\1.h"', stripped)
                                    else:
                                        line = re.sub(r'#include\s*<([^>]+)>', r'#include <\1.h>', stripped)
                                    modified = True
                        
                        # 修复命名空间问题
                        if 'using namespace' in stripped and not stripped.endswith(';'):
                            line = line.rstrip() + ';'
                            modified = True
                        
                        new_lines.append(line)
                    
                    if modified:
                        new_content = '\n'.join(new_lines)
                        
                        # 备份原文件
                        backup_file = cpp_file.with_suffix(cpp_file.suffix + '.backup')
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        
                        # 写入修复后的内容
                        with open(cpp_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        fixed_files.append(cpp_file.name)
                
                except Exception as e:
                    self.print_fix(f"修复 {cpp_file.name}", False, str(e))
                    all_success = False
            
            if fixed_files:
                self.print_fix(
                    f"C++ 语法修复 ({cpp_dir})", 
                    True, 
                    f"修复了 {len(fixed_files)} 个文件: {', '.join(fixed_files[:3])}{'...' if len(fixed_files) > 3 else ''}"
                )
            else:
                self.print_fix(f"C++ 语法修复 ({cpp_dir})", True, "无需修复")
        
        return all_success
    
    def fix_include_guards(self) -> bool:
        """添加包含保护"""
        self.print_header("添加包含保护")
        
        cpp_dirs = ['slave_upgraded', 'slave_bootloader_upgraded']
        all_success = True
        
        for cpp_dir in cpp_dirs:
            dir_path = self.project_root / cpp_dir
            if not dir_path.exists():
                continue
            
            # 查找头文件
            header_files = list(dir_path.glob("*.h"))
            
            fixed_headers = []
            for header_file in header_files:
                try:
                    with open(header_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 检查是否已有包含保护
                    if '#ifndef' in content and '#define' in content and '#endif' in content:
                        continue
                    
                    # 生成包含保护宏名
                    guard_name = header_file.name.upper().replace('.', '_').replace('-', '_')
                    guard_name = f"{cpp_dir.upper()}_{guard_name}"
                    
                    # 添加包含保护
                    new_content = f"""#ifndef {guard_name}
#define {guard_name}

{content}

#endif // {guard_name}
"""
                    
                    # 备份原文件
                    backup_file = header_file.with_suffix(header_file.suffix + '.backup')
                    if not backup_file.exists():
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                    
                    # 写入新内容
                    with open(header_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    fixed_headers.append(header_file.name)
                
                except Exception as e:
                    self.print_fix(f"添加包含保护 {header_file.name}", False, str(e))
                    all_success = False
            
            if fixed_headers:
                self.print_fix(
                    f"包含保护 ({cpp_dir})", 
                    True, 
                    f"添加了 {len(fixed_headers)} 个文件的包含保护"
                )
            else:
                self.print_fix(f"包含保护 ({cpp_dir})", True, "所有头文件已有包含保护")
        
        return all_success
    
    def fix_mbed_includes(self) -> bool:
        """修复 Mbed 包含问题"""
        self.print_header("修复 Mbed 包含")
        
        cpp_dirs = ['slave_upgraded', 'slave_bootloader_upgraded']
        all_success = True
        
        # 常见的 Mbed 包含映射
        mbed_includes = {
            'mbed.h': 'mbed.h',
            'Serial': 'drivers/Serial.h',
            'DigitalOut': 'drivers/DigitalOut.h',
            'DigitalIn': 'drivers/DigitalIn.h',
            'AnalogIn': 'drivers/AnalogIn.h',
            'AnalogOut': 'drivers/AnalogOut.h',
            'PwmOut': 'drivers/PwmOut.h',
            'InterruptIn': 'drivers/InterruptIn.h',
            'Ticker': 'drivers/Ticker.h',
            'Timer': 'drivers/Timer.h',
            'Thread': 'rtos/Thread.h',
            'Mutex': 'rtos/Mutex.h',
            'Semaphore': 'rtos/Semaphore.h',
            'EthernetInterface': 'netsocket/EthernetInterface.h',
            'TCPSocket': 'netsocket/TCPSocket.h',
            'UDPSocket': 'netsocket/UDPSocket.h'
        }
        
        for cpp_dir in cpp_dirs:
            dir_path = self.project_root / cpp_dir
            if not dir_path.exists():
                continue
            
            cpp_files = list(dir_path.glob("*.cpp")) + list(dir_path.glob("*.h"))
            
            fixed_files = []
            for cpp_file in cpp_files:
                try:
                    with open(cpp_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original_content = content
                    modified = False
                    
                    # 修复包含语句
                    for old_include, new_include in mbed_includes.items():
                        # 修复不正确的包含
                        patterns = [
                            f'#include "{old_include}"',
                            f'#include <{old_include}>',
                            f'#include "{old_include}.h"',
                            f'#include <{old_include}.h>'
                        ]
                        
                        for pattern in patterns:
                            if pattern in content:
                                content = content.replace(pattern, f'#include "{new_include}"')
                                modified = True
                    
                    # 确保有 mbed.h 包含
                    if ('#include "mbed.h"' not in content and 
                        '#include <mbed.h>' not in content and
                        cpp_file.suffix == '.cpp'):
                        
                        # 在第一个包含语句前添加 mbed.h
                        lines = content.split('\n')
                        new_lines = []
                        mbed_added = False
                        
                        for line in lines:
                            if line.strip().startswith('#include') and not mbed_added:
                                new_lines.append('#include "mbed.h"')
                                mbed_added = True
                            new_lines.append(line)
                        
                        if not mbed_added:
                            new_lines.insert(0, '#include "mbed.h"')
                        
                        content = '\n'.join(new_lines)
                        modified = True
                    
                    if modified:
                        # 备份原文件
                        backup_file = cpp_file.with_suffix(cpp_file.suffix + '.backup')
                        if not backup_file.exists():
                            with open(backup_file, 'w', encoding='utf-8') as f:
                                f.write(original_content)
                        
                        # 写入修复后的内容
                        with open(cpp_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        fixed_files.append(cpp_file.name)
                
                except Exception as e:
                    self.print_fix(f"修复 Mbed 包含 {cpp_file.name}", False, str(e))
                    all_success = False
            
            if fixed_files:
                self.print_fix(
                    f"Mbed 包含修复 ({cpp_dir})", 
                    True, 
                    f"修复了 {len(fixed_files)} 个文件"
                )
            else:
                self.print_fix(f"Mbed 包含修复 ({cpp_dir})", True, "无需修复")
        
        return all_success
    
    def create_missing_files(self) -> bool:
        """创建缺失的文件"""
        self.print_header("创建缺失文件")
        
        # 检查并创建可能缺失的重要文件
        files_to_check = [
            ('slave_upgraded/settings.h', self.create_settings_h),
            ('slave_bootloader_upgraded/BTFlash.h', self.create_btflash_h),
            ('slave_bootloader_upgraded/BTUtils.h', self.create_btutils_h)
        ]
        
        all_success = True
        
        for file_path, creator_func in files_to_check:
            full_path = self.project_root / file_path
            if not full_path.exists():
                try:
                    creator_func(full_path)
                    self.print_fix(f"创建 {file_path}", True, "文件已创建")
                except Exception as e:
                    self.print_fix(f"创建 {file_path}", False, str(e))
                    all_success = False
            else:
                self.print_fix(f"检查 {file_path}", True, "文件已存在")
        
        return all_success
    
    def create_settings_h(self, file_path: Path):
        """创建 settings.h 文件"""
        content = """#ifndef SETTINGS_H
#define SETTINGS_H

// Fan Club MkIV Settings
#define FC_VERSION "4.0"
#define FC_BUILD_DATE __DATE__
#define FC_BUILD_TIME __TIME__

// Communication settings
#define SERIAL_BAUD_RATE 115200
#define NETWORK_TIMEOUT 5000

// Hardware settings
#define LED_PIN LED1
#define BUTTON_PIN USER_BUTTON

// Debug settings
#ifdef DEBUG
#define DEBUG_PRINT(x) printf(x)
#else
#define DEBUG_PRINT(x)
#endif

#endif // SETTINGS_H
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_btflash_h(self, file_path: Path):
        """创建 BTFlash.h 文件"""
        content = """#ifndef BTFLASH_H
#define BTFLASH_H

#include "mbed.h"

class BTFlash {
public:
    BTFlash();
    ~BTFlash();
    
    bool initialize();
    bool writeData(uint32_t address, const uint8_t* data, size_t length);
    bool readData(uint32_t address, uint8_t* data, size_t length);
    bool eraseBlock(uint32_t address);
    
private:
    bool m_initialized;
};

#endif // BTFLASH_H
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_btutils_h(self, file_path: Path):
        """创建 BTUtils.h 文件"""
        content = """#ifndef BTUTILS_H
#define BTUTILS_H

#include "mbed.h"
#include <string>

class BTUtils {
public:
    static std::string bytesToHex(const uint8_t* data, size_t length);
    static bool hexToBytes(const std::string& hex, uint8_t* data, size_t maxLength);
    static uint32_t calculateCRC32(const uint8_t* data, size_t length);
    static bool validateFirmware(const uint8_t* firmware, size_t length);
};

#endif // BTUTILS_H
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_fix_report(self) -> str:
        """生成修复报告"""
        total_fixes = len(self.fixed_issues)
        successful_fixes = sum(1 for fix in self.fixed_issues if fix['success'])
        failed_fixes = total_fixes - successful_fixes
        
        report = f"""
# Fan Club MkIV 问题修复报告

**修复时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**总修复项**: {total_fixes}
**成功修复**: {successful_fixes}
**修复失败**: {failed_fixes}
**修复率**: {(successful_fixes/total_fixes*100):.1f}%

## 修复详情

"""
        
        for fix in self.fixed_issues:
            status = "✅ 成功" if fix['success'] else "❌ 失败"
            report += f"### {fix['issue']}\n\n"
            report += f"**状态**: {status}\n\n"
            if fix['details']:
                report += f"**详情**: {fix['details']}\n\n"
        
        if failed_fixes > 0:
            report += "\n## 需要手动修复的问题\n\n"
            for fix in self.fixed_issues:
                if not fix['success']:
                    report += f"- **{fix['issue']}**: {fix['details']}\n"
        
        report += "\n## 建议\n\n"
        report += "1. 重新运行自动化调试工具验证修复效果\n"
        report += "2. 使用 Mbed Studio 编译项目确认无编译错误\n"
        report += "3. 运行单元测试验证功能正确性\n"
        report += "4. 备份文件位于 *.backup，如有问题可以恢复\n"
        
        return report
    
    def run_all_fixes(self) -> bool:
        """运行所有修复"""
        print("Fan Club MkIV 问题修复工具")
        print(f"项目路径: {self.project_root}")
        
        # 运行所有修复
        fixes = [
            self.create_missing_files,
            self.fix_mbed_includes,
            self.fix_include_guards,
            self.fix_cpp_syntax_issues
        ]
        
        all_success = True
        for fix in fixes:
            try:
                success = fix()
                all_success = all_success and success
            except Exception as e:
                print(f"修复过程出错: {e}")
                all_success = False
        
        # 生成报告
        self.print_header("修复总结")
        
        total_fixes = len(self.fixed_issues)
        successful_fixes = sum(1 for fix in self.fixed_issues if fix['success'])
        failed_fixes = total_fixes - successful_fixes
        
        print(f"总修复项: {total_fixes}")
        print(f"成功修复: {successful_fixes}")
        print(f"修复失败: {failed_fixes}")
        print(f"修复率: {(successful_fixes/total_fixes*100):.1f}%")
        
        # 保存报告
        import time
        report = self.generate_fix_report()
        report_file = self.project_root / "fix_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n修复报告已保存到: {report_file}")
        
        return all_success

def main():
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='Fan Club MkIV 问题修复工具')
    parser.add_argument('--project-root', help='项目根目录路径', default='.')
    
    args = parser.parse_args()
    
    fixer = IssueFixer(args.project_root)
    success = fixer.run_all_fixes()
    
    if success:
        print("\n🎉 所有问题已修复！")
        print("建议重新运行调试工具验证修复效果：python auto_debug.py")
        sys.exit(0)
    else:
        print("\n⚠️  部分问题修复失败，请查看报告进行手动修复。")
        sys.exit(1)

if __name__ == "__main__":
    main()
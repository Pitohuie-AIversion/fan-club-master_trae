#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mbed OS Python兼容性修复脚本

修复Mbed OS 5.9中collections.Mapping导入错误的问题
在Python 3.3+中，Mapping已移动到collections.abc模块

作者: AI Assistant
日期: 2025年1月
"""

import os
import re
from pathlib import Path

def fix_collections_import(file_path):
    """修复单个文件中的collections导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原文件
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        if not backup_path.exists():
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 修复导入语句
        original_content = content
        
        # 修复 from collections import ... Mapping ...
        content = re.sub(
            r'from collections import ([^\n]*?)Mapping([^\n]*)',
            lambda m: f'from collections.abc import Mapping\nfrom collections import {m.group(1).replace(", ", "").replace("Mapping, ", "").replace(", Mapping", "")}{m.group(2)}' if m.group(1).strip() or m.group(2).strip() else 'from collections.abc import Mapping',
            content
        )
        
        # 修复 from collections import namedtuple, Mapping
        content = re.sub(
            r'from collections import namedtuple, Mapping',
            'from collections.abc import Mapping\nfrom collections import namedtuple',
            content
        )
        
        # 修复其他可能的组合
        content = re.sub(
            r'from collections import (.*?), Mapping(.*?)$',
            r'from collections.abc import Mapping\nfrom collections import \1\2',
            content,
            flags=re.MULTILINE
        )
        
        # 如果内容有变化，写入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已修复: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"✗ 修复失败 {file_path}: {e}")
        return False

def find_and_fix_python_files(base_dir):
    """查找并修复所有Python文件中的collections导入问题"""
    base_path = Path(base_dir)
    fixed_count = 0
    
    # 查找所有Python文件
    python_files = list(base_path.rglob('*.py'))
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    for py_file in python_files:
        # 跳过我们自己的脚本
        if py_file.name in ['fix_python_compatibility.py', 'build_complete_firmware.py']:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含有问题的导入
            if 'from collections import' in content and 'Mapping' in content:
                if fix_collections_import(py_file):
                    fixed_count += 1
                    
        except Exception as e:
            print(f"检查文件失败 {py_file}: {e}")
            continue
    
    return fixed_count

def main():
    """主函数"""
    print("Mbed OS Python兼容性修复脚本")
    print("=" * 40)
    
    # 获取当前目录
    base_dir = Path(__file__).parent
    print(f"扫描目录: {base_dir}")
    print()
    
    # 修复Python文件
    fixed_count = find_and_fix_python_files(base_dir)
    
    print()
    print("=" * 40)
    if fixed_count > 0:
        print(f"✓ 成功修复 {fixed_count} 个文件")
        print("现在可以重新尝试编译")
    else:
        print("没有找到需要修复的文件")
        print("可能问题已经修复或者在其他位置")
    
    # 提供手动修复建议
    print("\n如果问题仍然存在，请手动检查以下文件:")
    print("- mbed-os/tools/targets/__init__.py")
    print("- mbed-os/tools/make.py")
    print("- 将 'from collections import Mapping' 改为 'from collections.abc import Mapping'")

if __name__ == "__main__":
    main()
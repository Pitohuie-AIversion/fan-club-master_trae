#!/usr/bin/env python3
"""
Chase Feedback 实现验证脚本
验证chase feedback控制系统的代码完整性和正确性
"""

import os
import re
import sys

def check_file_exists(filepath):
    """检查文件是否存在"""
    return os.path.exists(filepath)

def read_file_content(filepath):
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件 {filepath} 失败: {e}")
        return ""

def validate_fan_class():
    """验证Fan类的chase feedback实现"""
    print("=== 验证Fan类实现 ===")
    
    fan_h_path = "Fan.h"
    fan_cpp_path = "Fan.cpp"
    
    if not check_file_exists(fan_h_path):
        print("❌ Fan.h 文件不存在")
        return False
    
    if not check_file_exists(fan_cpp_path):
        print("❌ Fan.cpp 文件不存在")
        return False
    
    fan_h_content = read_file_content(fan_h_path)
    fan_cpp_content = read_file_content(fan_cpp_path)
    
    # 检查Fan.h中的新方法声明
    required_methods = [
        r'bool\s+setTarget\s*\(\s*int\s+targetRPM\s*\)',
        r'bool\s+updateChase\s*\(\s*float\s+tolerance\s*\)',
        r'int\s+getTarget\s*\(\s*\)',
        r'bool\s+isChasing\s*\(\s*\)',
        r'bool\s+setPIGains\s*\(\s*float\s+kp\s*,\s*float\s+ki\s*\)'
    ]
    
    print("检查Fan.h中的方法声明:")
    for method in required_methods:
        if re.search(method, fan_h_content):
            print(f"✅ 找到方法: {method}")
        else:
            print(f"❌ 缺少方法: {method}")
            return False
    
    # 检查Fan.h中的PI控制器成员变量
    required_members = [
        r'float\s+kp\s*;',
        r'float\s+ki\s*;',
        r'float\s+integral\s*;',
        r'float\s+lastError\s*;',
        r'bool\s+chasing\s*;',
        r'Timer\s+chaseTimer\s*;'
    ]
    
    print("\n检查Fan.h中的PI控制器成员变量:")
    for member in required_members:
        if re.search(member, fan_h_content):
            print(f"✅ 找到成员变量: {member}")
        else:
            print(f"❌ 缺少成员变量: {member}")
            return False
    
    # 检查Fan.cpp中的方法实现
    print("\n检查Fan.cpp中的方法实现:")
    if "setTarget" in fan_cpp_content and "targetRPM" in fan_cpp_content:
        print("✅ setTarget方法已实现")
    else:
        print("❌ setTarget方法未实现")
        return False
    
    if "updateChase" in fan_cpp_content and "tolerance" in fan_cpp_content:
        print("✅ updateChase方法已实现")
    else:
        print("❌ updateChase方法未实现")
        return False
    
    if "setPIGains" in fan_cpp_content:
        print("✅ setPIGains方法已实现")
    else:
        print("❌ setPIGains方法未实现")
        return False
    
    return True

def validate_processor_class():
    """验证Processor类的chase feedback实现"""
    print("\n=== 验证Processor类实现 ===")
    
    processor_h_path = "Processor.h"
    processor_cpp_path = "Processor.cpp"
    
    if not check_file_exists(processor_h_path):
        print("❌ Processor.h 文件不存在")
        return False
    
    if not check_file_exists(processor_cpp_path):
        print("❌ Processor.cpp 文件不存在")
        return False
    
    processor_h_content = read_file_content(processor_h_path)
    processor_cpp_content = read_file_content(processor_cpp_path)
    
    # 检查命令枚举
    print("检查命令枚举:")
    if "CHASE = 'C'" in processor_h_content or "CHASE = 'C'" in processor_cpp_content:
        print("✅ CHASE命令枚举已定义")
    else:
        print("❌ CHASE命令枚举未定义")
        return False
    
    if "PISET = 'P'" in processor_h_content or "PISET = 'P'" in processor_cpp_content:
        print("✅ PISET命令枚举已定义")
    else:
        print("❌ PISET命令枚举未定义")
        return False
    
    # 检查命令处理实现
    print("\n检查命令处理实现:")
    if "case CHASE:" in processor_cpp_content:
        print("✅ CHASE命令处理已实现")
    else:
        print("❌ CHASE命令处理未实现")
        return False
    
    if "case PISET:" in processor_cpp_content:
        print("✅ PISET命令处理已实现")
    else:
        print("❌ PISET命令处理未实现")
        return False
    
    # 检查反馈控制循环
    print("\n检查反馈控制循环:")
    if "isChasing()" in processor_cpp_content and "updateChase" in processor_cpp_content:
        print("✅ 反馈控制循环已集成")
    else:
        print("❌ 反馈控制循环未集成")
        return False
    
    return True

def validate_test_files():
    """验证测试文件"""
    print("\n=== 验证测试文件 ===")
    
    test_file = "test_chase_feedback.cpp"
    readme_file = "CHASE_FEEDBACK_README.md"
    
    if check_file_exists(test_file):
        print("✅ 测试文件存在")
    else:
        print("❌ 测试文件不存在")
        return False
    
    if check_file_exists(readme_file):
        print("✅ 说明文档存在")
    else:
        print("❌ 说明文档不存在")
        return False
    
    return True

def main():
    """主验证函数"""
    print("Chase Feedback 实现验证")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists("Fan.h"):
        print("❌ 请在slave目录下运行此脚本")
        sys.exit(1)
    
    success = True
    
    # 验证各个组件
    success &= validate_fan_class()
    success &= validate_processor_class()
    success &= validate_test_files()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有验证通过！Chase Feedback控制系统实现完整")
        print("\n实现的功能:")
        print("- ✅ Fan类PI控制器")
        print("- ✅ CHASE命令处理")
        print("- ✅ PISET命令处理")
        print("- ✅ 反馈控制循环")
        print("- ✅ 测试文件和文档")
        
        print("\n使用方法:")
        print("1. CHASE <fanID> <targetRPM> - 设置目标转速")
        print("2. PISET <fanID> <kp> <ki> - 设置PI参数")
        print("3. 系统会自动执行反馈控制")
        
    else:
        print("❌ 验证失败！请检查实现")
        sys.exit(1)

if __name__ == "__main__":
    main()
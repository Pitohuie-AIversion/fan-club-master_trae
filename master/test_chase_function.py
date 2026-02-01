#!/usr/bin/env python3
"""
测试CHASE功能的脚本
验证sendChase方法是否可用
"""

import sys
import os
sys.path.append('.')

def test_chase_method():
    """测试CHASE方法是否存在并可调用"""
    try:
        from fc.backend.communicator import FCCommunicator
        
        # 检查sendChase方法是否存在
        if hasattr(FCCommunicator, 'sendChase'):
            print("✓ sendChase方法存在于FCCommunicator类中")
            
            # 获取方法签名
            import inspect
            sig = inspect.signature(FCCommunicator.sendChase)
            print(f"✓ sendChase方法签名: {sig}")
            
            # 检查方法文档
            doc = FCCommunicator.sendChase.__doc__
            if doc:
                print(f"✓ 方法文档: {doc.strip()}")
            
            return True
        else:
            print("✗ sendChase方法不存在于FCCommunicator类中")
            return False
            
    except ImportError as e:
        print(f"✗ 导入FCCommunicator失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")
        return False

def test_chase_constants():
    """测试CHASE相关常量是否存在"""
    try:
        from fc import standards as s
        
        if hasattr(s, 'CMD_CHASE'):
            print(f"✓ CMD_CHASE常量存在，值为: {s.CMD_CHASE}")
            return True
        else:
            print("✗ CMD_CHASE常量不存在")
            return False
            
    except ImportError as e:
        print(f"✗ 导入standards失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试常量时出现错误: {e}")
        return False

if __name__ == "__main__":
    print("=== CHASE功能测试 ===")
    print()
    
    print("1. 测试sendChase方法:")
    method_ok = test_chase_method()
    print()
    
    print("2. 测试CHASE常量:")
    constants_ok = test_chase_constants()
    print()
    
    if method_ok and constants_ok:
        print("✓ 所有测试通过！CHASE功能应该可以正常工作。")
        sys.exit(0)
    else:
        print("✗ 部分测试失败，CHASE功能可能无法正常工作。")
        sys.exit(1)
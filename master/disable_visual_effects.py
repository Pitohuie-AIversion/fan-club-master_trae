#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
禁用视觉效果配置工具
如果遇到难以解决的视觉效果相关错误，可以使用此工具禁用相关功能
"""

import os
import sys
import shutil
from pathlib import Path

def disable_matplotlib_animations():
    """禁用 matplotlib 动画和实时绘图"""
    config_content = """
# 禁用 matplotlib 动画配置
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
plt.ioff()  # 关闭交互模式

# 禁用动画
import matplotlib.animation
matplotlib.animation.Animation = lambda *args, **kwargs: None
"""
    
    config_file = Path("fc/frontend/gui/matplotlib_config.py")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✓ 已创建 matplotlib 禁用配置: {config_file}")

def disable_theme_animations():
    """禁用主题切换动画"""
    # 备份原始文件
    theme_file = Path("fc/frontend/gui/theme_manager.py")
    backup_file = theme_file.with_suffix('.py.backup')
    
    if theme_file.exists() and not backup_file.exists():
        shutil.copy2(theme_file, backup_file)
        print(f"✓ 已备份主题管理器: {backup_file}")
    
    # 修改主题管理器，禁用回调
    if theme_file.exists():
        with open(theme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 禁用主题回调通知
        content = content.replace(
            "self._notify_callbacks()",
            "# self._notify_callbacks()  # 已禁用主题回调"
        )
        
        with open(theme_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 已禁用主题回调通知")

def disable_visual_effects():
    """禁用视觉效果模块"""
    effects_file = Path("fc/frontend/gui/visual_effects.py")
    backup_file = effects_file.with_suffix('.py.backup')
    
    if effects_file.exists() and not backup_file.exists():
        shutil.copy2(effects_file, backup_file)
        print(f"✓ 已备份视觉效果模块: {backup_file}")
    
    # 创建空的视觉效果模块
    minimal_content = '''"""
视觉效果模块 - 已禁用版本
"""

def animate_color_transition(*args, **kwargs):
    """禁用的颜色过渡动画"""
    callback = kwargs.get('callback')
    if callback:
        callback()

def ease_in_out_cubic(t):
    """简化的缓动函数"""
    return t

class PerformanceManager:
    """简化的性能管理器"""
    def __init__(self, *args, **kwargs):
        pass
    
    def optimized_theme_switch(self, theme_manager, new_theme):
        """简化的主题切换"""
        theme_manager.set_theme(new_theme)
    
    def __getattr__(self, name):
        """返回空函数以避免错误"""
        return lambda *args, **kwargs: None
'''
    
    with open(effects_file, 'w', encoding='utf-8') as f:
        f.write(minimal_content)
    
    print(f"✓ 已禁用视觉效果模块")

def create_simple_startup_script():
    """创建简化的启动脚本"""
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化启动脚本 - 禁用视觉效果版本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入禁用配置
try:
    from fc.frontend.gui.matplotlib_config import *
except ImportError:
    pass

# 启动主程序
if __name__ == "__main__":
    try:
        from main import *
        # 这里可以添加额外的错误处理
    except Exception as e:
        print(f"启动错误: {e}")
        input("按回车键退出...")
'''
    
    script_file = Path("main_simple.py")
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✓ 已创建简化启动脚本: {script_file}")

def restore_backups():
    """恢复备份文件"""
    backup_files = [
        "fc/frontend/gui/theme_manager.py.backup",
        "fc/frontend/gui/visual_effects.py.backup"
    ]
    
    restored = 0
    for backup_path in backup_files:
        backup_file = Path(backup_path)
        if backup_file.exists():
            original_file = backup_file.with_suffix('')
            shutil.copy2(backup_file, original_file)
            print(f"✓ 已恢复: {original_file}")
            restored += 1
    
    if restored == 0:
        print("没有找到备份文件")
    else:
        print(f"✓ 已恢复 {restored} 个文件")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python disable_visual_effects.py disable  # 禁用视觉效果")
        print("  python disable_visual_effects.py restore  # 恢复原始文件")
        return
    
    action = sys.argv[1].lower()
    
    if action == "disable":
        print("正在禁用视觉效果...")
        disable_matplotlib_animations()
        disable_theme_animations()
        disable_visual_effects()
        create_simple_startup_script()
        print("\n✓ 视觉效果已禁用")
        print("现在可以使用 'python main_simple.py' 启动应用程序")
        
    elif action == "restore":
        print("正在恢复原始文件...")
        restore_backups()
        print("\n✓ 原始文件已恢复")
        
    else:
        print(f"未知操作: {action}")
        print("使用 'disable' 或 'restore'")

if __name__ == "__main__":
    main()
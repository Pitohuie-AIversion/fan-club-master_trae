################################################################################
## Project: Fan Club Mark II "Master" ## File: ux_enhancements.py          ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES       ##                     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>  ##                ##
## dashuai                    ## <dschen2018@gmail.com>     ##                ##
################################################################################

## ABOUT #######################################################################
"""
用户体验增强模块
提供键盘快捷键、工具提示优化、状态保存恢复等功能
"""
################################################################################

import tkinter as tk
from tkinter import ttk
import json
import os
from typing import Dict, Any, Optional, Callable
from functools import wraps

class KeyboardShortcuts:
    """键盘快捷键管理器"""
    
    def __init__(self, root_widget: tk.Widget):
        self.root = root_widget
        self.shortcuts: Dict[str, Callable] = {}
        self.descriptions: Dict[str, str] = {}
        
        # 绑定全局快捷键
        self._setup_default_shortcuts()
    
    def _setup_default_shortcuts(self):
        """设置默认快捷键"""
        # 主题切换
        self.register_shortcut('Control-t', self._toggle_theme, '切换主题')
        
        # 密度切换
        self.register_shortcut('Control-d', self._toggle_density, '切换UI密度')
        
        # 设置窗口
        self.register_shortcut('Control-comma', self._open_settings, '打开设置')
        
        # 帮助
        self.register_shortcut('F1', self._show_help, '显示帮助')
        
        # 刷新
        self.register_shortcut('F5', self._refresh, '刷新界面')
        
        # 退出
        self.register_shortcut('Control-q', self._quit_app, '退出应用')
        
        # 标签页切换
        self.register_shortcut('Control-1', lambda: self._switch_tab(0), '切换到Profile标签页')
        self.register_shortcut('Control-2', lambda: self._switch_tab(1), '切换到Network标签页')
        self.register_shortcut('Control-3', lambda: self._switch_tab(2), '切换到Control标签页')
        self.register_shortcut('Control-4', lambda: self._switch_tab(3), '切换到Console标签页')
        self.register_shortcut('Control-5', lambda: self._switch_tab(4), '切换到Monitoring标签页')
        self.register_shortcut('Control-6', lambda: self._switch_tab(5), '切换到Filter Config标签页')
    
    def register_shortcut(self, key_sequence: str, callback: Callable, description: str = ""):
        """注册快捷键"""
        self.shortcuts[key_sequence] = callback
        self.descriptions[key_sequence] = description
        
        try:
            self.root.bind_all(f'<{key_sequence}>', lambda e: callback())
        except tk.TclError as e:
            print(f"Failed to bind shortcut {key_sequence}: {e}")
    
    def unregister_shortcut(self, key_sequence: str):
        """取消注册快捷键"""
        if key_sequence in self.shortcuts:
            try:
                self.root.unbind_all(f'<{key_sequence}>')
                del self.shortcuts[key_sequence]
                del self.descriptions[key_sequence]
            except tk.TclError:
                pass
    
    def get_shortcuts_help(self) -> str:
        """获取快捷键帮助文本"""
        help_text = "键盘快捷键:\n\n"
        for key, desc in self.descriptions.items():
            help_text += f"{key.replace('Control', 'Ctrl')}: {desc}\n"
        return help_text
    
    def _toggle_theme(self):
        """切换主题快捷键回调"""
        try:
            from fc.frontend.gui.theme_manager import theme_manager
            theme_manager.toggle_theme()
        except ImportError:
            pass
    
    def _toggle_density(self):
        """切换密度快捷键回调"""
        # 这里需要访问主应用实例
        pass
    
    def _open_settings(self):
        """打开设置快捷键回调"""
        # 这里需要访问主应用实例
        pass
    
    def _show_help(self):
        """显示帮助快捷键回调"""
        help_window = tk.Toplevel(self.root)
        help_window.title("键盘快捷键")
        help_window.geometry("400x300")
        help_window.resizable(False, False)
        
        # 居中显示
        help_window.transient(self.root)
        help_window.grab_set()
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        text_widget.insert(tk.END, self.get_shortcuts_help())
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_btn = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def _refresh(self):
        """刷新界面快捷键回调"""
        self.root.update_idletasks()
    
    def _quit_app(self):
        """退出应用快捷键回调"""
        self.root.quit()
    
    def _switch_tab(self, tab_index: int):
        """切换标签页快捷键回调"""
        # 这里需要访问主应用实例的notebook
        pass

class EnhancedTooltip:
    """增强型工具提示"""
    
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500, wraplength: int = 250):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.tooltip_window = None
        self.show_timer = None
        self.hide_timer = None
        
        # 绑定事件
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<Motion>', self._on_motion)
    
    def _on_enter(self, event=None):
        """鼠标进入时的处理"""
        self._cancel_timers()
        self.show_timer = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """鼠标离开时的处理"""
        self._cancel_timers()
        self.hide_timer = self.widget.after(100, self._hide_tooltip)
    
    def _on_motion(self, event=None):
        """鼠标移动时的处理 - 优化性能"""
        # 只有在工具提示已显示时才更新位置，减少不必要的处理
        if self.tooltip_window and hasattr(self, '_last_motion_time'):
            import time
            current_time = time.time()
            # 限制更新频率，避免过于频繁的位置更新
            if current_time - self._last_motion_time < 0.05:  # 50ms间隔
                return
            self._last_motion_time = current_time
            
        if self.tooltip_window:
            try:
                self._update_position(event)
            except (tk.TclError, AttributeError):
                # 忽略错误，避免卡顿
                pass
        else:
            # 记录时间但不处理
            import time
            self._last_motion_time = time.time()
    
    def _cancel_timers(self):
        """取消所有定时器"""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None
        if self.hide_timer:
            self.widget.after_cancel(self.hide_timer)
            self.hide_timer = None
    
    def _show_tooltip(self):
        """显示工具提示"""
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # 设置样式
        try:
            from fc.frontend.gui.theme_manager import theme_manager
            bg_color = theme_manager.get_color('SURFACE_2')
            fg_color = theme_manager.get_color('TEXT_PRIMARY')
            border_color = theme_manager.get_color('BORDER')
        except:
            bg_color = '#f0f0f0'
            fg_color = '#000000'
            border_color = '#cccccc'
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background=bg_color,
            foreground=fg_color,
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=self.wraplength,
            justify=tk.LEFT,
            padx=8,
            pady=4,
            font=('Segoe UI', 9)
        )
        label.pack()
        
        # 设置边框颜色
        self.tooltip_window.config(highlightbackground=border_color, highlightthickness=1)
    
    def _hide_tooltip(self):
        """隐藏工具提示"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def _update_position(self, event):
        """更新工具提示位置"""
        if self.tooltip_window:
            x = event.x_root + 20
            y = event.y_root + 5
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
    
    def update_text(self, new_text: str):
        """更新工具提示文本"""
        self.text = new_text
        if self.tooltip_window:
            self._hide_tooltip()

class StateManager:
    """状态保存和恢复管理器"""
    
    def __init__(self, app_name: str = "FanClub"):
        self.app_name = app_name
        self.config_dir = os.path.expanduser(f"~/.{app_name.lower()}")
        self.config_file = os.path.join(self.config_dir, "state.json")
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.state: Dict[str, Any] = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载保存的状态"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to load state: {e}")
        
        return {
            'window': {
                'geometry': '800x600+100+100',
                'state': 'normal'
            },
            'theme': 'light',
            'ui_density': 'comfortable',
            'last_tab': 0,
            'user_preferences': {}
        }
    
    def save_state(self):
        """保存当前状态"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save state: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        keys = key.split('.')
        value = self.state
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置状态值"""
        keys = key.split('.')
        current = self.state
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_window_state(self, window: tk.Tk):
        """保存窗口状态"""
        try:
            self.set('window.geometry', window.geometry())
            self.set('window.state', window.state())
        except tk.TclError:
            pass
    
    def restore_window_state(self, window: tk.Tk):
        """恢复窗口状态"""
        try:
            geometry = self.get('window.geometry', '800x600+100+100')
            state = self.get('window.state', 'normal')
            
            window.geometry(geometry)
            if state == 'zoomed':
                window.state('zoomed')
        except tk.TclError:
            pass

def add_tooltip(widget: tk.Widget, text: str, **kwargs) -> EnhancedTooltip:
    """为控件添加工具提示的便捷函数"""
    return EnhancedTooltip(widget, text, **kwargs)

def keyboard_shortcut(key_sequence: str, description: str = ""):
    """键盘快捷键装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 存储快捷键信息
        wrapper._shortcut_key = key_sequence
        wrapper._shortcut_description = description
        return wrapper
    return decorator

class UXEnhancementManager:
    """用户体验增强管理器"""
    
    def __init__(self, root_widget: tk.Widget, app_name: str = "FanClub"):
        self.root = root_widget
        self.app_name = app_name
        
        # 初始化各个组件
        self.keyboard_shortcuts = KeyboardShortcuts(root_widget)
        self.state_manager = StateManager(app_name)
        
        # 存储工具提示引用
        self.tooltips: Dict[tk.Widget, EnhancedTooltip] = {}
        
        # 设置自动保存
        self._setup_auto_save()
    
    def _setup_auto_save(self):
        """设置自动保存"""
        def auto_save():
            self.state_manager.save_state()
            # 每30秒自动保存一次
            self.root.after(30000, auto_save)
        
        # 启动自动保存
        self.root.after(30000, auto_save)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 清理主题回调以防止关闭时的主题更新错误
            from fc.frontend.gui.theme_manager import theme_manager
            theme_manager.clear_callbacks()
            print("[DEBUG] Theme callbacks cleared during shutdown")
        except Exception as e:
            print(f"[DEBUG] Error clearing theme callbacks during shutdown: {e}")
        
        # 保存窗口状态
        if isinstance(self.root, tk.Tk):
            self.state_manager.save_window_state(self.root)
        
        # 保存最终状态
        self.state_manager.save_state()
        
        # 关闭应用
        self.root.destroy()
    
    def add_tooltip(self, widget: tk.Widget, text: str, **kwargs) -> EnhancedTooltip:
        """添加工具提示"""
        tooltip = EnhancedTooltip(widget, text, **kwargs)
        self.tooltips[widget] = tooltip
        return tooltip
    
    def remove_tooltip(self, widget: tk.Widget):
        """移除工具提示"""
        if widget in self.tooltips:
            tooltip = self.tooltips[widget]
            tooltip._hide_tooltip()
            del self.tooltips[widget]
    
    def register_shortcut(self, key_sequence: str, callback: Callable, description: str = ""):
        """注册快捷键"""
        self.keyboard_shortcuts.register_shortcut(key_sequence, callback, description)
    
    def set_app_callbacks(self, callbacks: Dict[str, Callable]):
        """设置应用回调函数"""
        # 更新快捷键回调
        if 'toggle_density' in callbacks:
            self.keyboard_shortcuts._toggle_density = callbacks['toggle_density']
        if 'open_settings' in callbacks:
            self.keyboard_shortcuts._open_settings = callbacks['open_settings']
        if 'switch_tab' in callbacks:
            self.keyboard_shortcuts._switch_tab = callbacks['switch_tab']
    
    def restore_state(self):
        """恢复应用状态"""
        # 恢复窗口状态
        if isinstance(self.root, tk.Tk):
            self.state_manager.restore_window_state(self.root)
        
        return self.state_manager.state
    
    def save_preference(self, key: str, value: Any):
        """保存用户偏好"""
        self.state_manager.set(f'user_preferences.{key}', value)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.state_manager.get(f'user_preferences.{key}', default)

# 全局UX增强管理器实例
_ux_manager = None

def get_ux_manager() -> Optional[UXEnhancementManager]:
    """获取全局UX增强管理器实例"""
    return _ux_manager

def initialize_ux_enhancements(root_widget: tk.Widget, app_name: str = "FanClub") -> UXEnhancementManager:
    """初始化用户体验增强功能"""
    global _ux_manager
    _ux_manager = UXEnhancementManager(root_widget, app_name)
    return _ux_manager
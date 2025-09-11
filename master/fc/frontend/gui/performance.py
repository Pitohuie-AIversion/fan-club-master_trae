# -*- coding: utf-8 -*-
"""
UI性能优化模块
提供图标缓存、主题切换优化、内存使用优化等功能
"""

import tkinter as tk
from tkinter import ttk
import threading
import weakref
from typing import Dict, Any, Optional, Callable
import gc
import time
from functools import lru_cache, wraps

class IconCache:
    """图标缓存管理器"""
    
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def get_icon(self, icon_path: str, size: tuple = None) -> Any:
        """获取缓存的图标"""
        cache_key = f"{icon_path}_{size}" if size else icon_path
        
        with self._lock:
            if cache_key in self._cache:
                self._access_times[cache_key] = time.time()
                return self._cache[cache_key]
        
        return None
    
    def cache_icon(self, icon_path: str, icon_data: Any, size: tuple = None):
        """缓存图标"""
        cache_key = f"{icon_path}_{size}" if size else icon_path
        
        with self._lock:
            # 如果缓存已满，移除最久未使用的项
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            self._cache[cache_key] = icon_data
            self._access_times[cache_key] = time.time()
    
    def _evict_lru(self):
        """移除最久未使用的缓存项"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[lru_key]
        del self._access_times[lru_key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
            }

class ThemeOptimizer:
    """主题切换优化器"""
    
    def __init__(self):
        self._theme_cache: Dict[str, Dict[str, Any]] = {}
        self._pending_updates: Dict[str, Any] = {}
        self._update_timer: Optional[str] = None
        self._batch_delay = 50  # 毫秒
    
    def cache_theme_config(self, theme_name: str, config: Dict[str, Any]):
        """缓存主题配置"""
        self._theme_cache[theme_name] = config.copy()
    
    def get_cached_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """获取缓存的主题配置"""
        return self._theme_cache.get(theme_name)
    
    def batch_theme_update(self, widget: tk.Widget, updates: Dict[str, Any]):
        """批量主题更新"""
        widget_id = str(widget)
        
        if widget_id not in self._pending_updates:
            self._pending_updates[widget_id] = {'widget': weakref.ref(widget), 'updates': {}}
        
        self._pending_updates[widget_id]['updates'].update(updates)
        
        # 延迟执行批量更新
        if self._update_timer:
            widget.after_cancel(self._update_timer)
        
        self._update_timer = widget.after(self._batch_delay, self._apply_pending_updates)
    
    def _apply_pending_updates(self):
        """应用待处理的更新"""
        for widget_id, data in list(self._pending_updates.items()):
            widget_ref = data['widget']
            widget = widget_ref() if widget_ref else None
            
            if widget and widget.winfo_exists():
                try:
                    for option, value in data['updates'].items():
                        widget.configure(**{option: value})
                except tk.TclError:
                    pass  # 控件可能已被销毁
        
        self._pending_updates.clear()
        self._update_timer = None

class MemoryOptimizer:
    """内存使用优化器"""
    
    def __init__(self):
        self._widget_refs: weakref.WeakSet = weakref.WeakSet()
        self._cleanup_interval = 30000  # 30秒
        self._last_cleanup = time.time()
    
    def register_widget(self, widget: tk.Widget):
        """注册控件用于内存管理"""
        self._widget_refs.add(widget)
    
    def cleanup_destroyed_widgets(self):
        """清理已销毁的控件引用"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval / 1000:
            return
        
        # 强制垃圾回收
        gc.collect()
        self._last_cleanup = current_time
    
    def optimize_widget_creation(self, widget_class):
        """优化控件创建的装饰器"""
        def decorator(create_func):
            @wraps(create_func)
            def wrapper(*args, **kwargs):
                widget = create_func(*args, **kwargs)
                if isinstance(widget, tk.Widget):
                    self.register_widget(widget)
                return widget
            return wrapper
        return decorator

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._metrics: Dict[str, list] = {
            'theme_switch_time': [],
            'widget_creation_time': [],
            'memory_usage': []
        }
        self._start_times: Dict[str, float] = {}
    
    def start_timing(self, operation: str):
        """开始计时"""
        self._start_times[operation] = time.time()
    
    def end_timing(self, operation: str):
        """结束计时并记录"""
        if operation in self._start_times:
            duration = time.time() - self._start_times[operation]
            if operation in self._metrics:
                self._metrics[operation].append(duration)
                # 只保留最近100次记录
                if len(self._metrics[operation]) > 100:
                    self._metrics[operation] = self._metrics[operation][-100:]
            del self._start_times[operation]
    
    def get_average_time(self, operation: str) -> float:
        """获取操作的平均时间"""
        times = self._metrics.get(operation, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {}
        for operation, times in self._metrics.items():
            if times:
                report[operation] = {
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        return report

def performance_timer(operation_name: str):
    """性能计时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = getattr(wrapper, '_monitor', None)
            if monitor:
                monitor.start_timing(operation_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                if monitor:
                    monitor.end_timing(operation_name)
        return wrapper
    return decorator

class PerformanceManager:
    """性能管理器 - 统一管理所有性能优化功能"""
    
    def __init__(self):
        self.icon_cache = IconCache()
        self.theme_optimizer = ThemeOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.monitor = PerformanceMonitor()
        
        # 为性能计时装饰器设置监控器
        performance_timer._monitor = self.monitor
    
    def optimize_widget_creation(self, widget_class):
        """优化控件创建"""
        return self.memory_optimizer.optimize_widget_creation(widget_class)
    
    @performance_timer('theme_switch')
    def optimized_theme_switch(self, theme_manager, new_theme: str):
        """优化的主题切换"""
        # 检查缓存的主题配置
        cached_config = self.theme_optimizer.get_cached_theme(new_theme)
        if not cached_config:
            # 如果没有缓存，正常切换并缓存结果
            theme_manager.switch_theme(new_theme)
            # 这里可以添加缓存主题配置的逻辑
        else:
            # 使用缓存的配置快速切换
            theme_manager.apply_cached_theme(cached_config)
    
    def schedule_cleanup(self, widget: tk.Widget):
        """安排定期清理"""
        def cleanup():
            self.memory_optimizer.cleanup_destroyed_widgets()
            # 安排下次清理
            widget.after(30000, cleanup)  # 30秒后再次清理
        
        widget.after(30000, cleanup)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            'icon_cache': self.icon_cache.get_cache_info(),
            'performance_metrics': self.monitor.get_performance_report(),
            'memory_info': {
                'registered_widgets': len(self.memory_optimizer._widget_refs)
            }
        }

# 全局性能管理器实例
_performance_manager = None

def get_performance_manager() -> PerformanceManager:
    """获取全局性能管理器实例"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager

def initialize_performance_optimization(root_widget: tk.Widget) -> PerformanceManager:
    """初始化性能优化"""
    manager = get_performance_manager()
    manager.schedule_cleanup(root_widget)
    return manager
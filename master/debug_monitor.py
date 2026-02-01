#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试监控模块 - 用于监控程序运行状态和诊断卡死问题
"""

import threading
import time
import logging
import json
import os
import psutil
import traceback
from datetime import datetime
from collections import defaultdict, deque

class DebugMonitor:
    """调试监控器 - 监控程序运行状态，记录关键事件"""
    
    def __init__(self, log_dir="logs", max_log_size=10*1024*1024, enabled=False):
        self.log_dir = log_dir
        self.max_log_size = max_log_size
        self.is_monitoring = False
        self.monitor_thread = None
        self.enabled = enabled  # 添加启用/禁用开关
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 设置日志记录器
        self.setup_logging()
        
        # 监控数据
        self.thread_stats = defaultdict(dict)
        self.network_stats = defaultdict(int)
        self.error_stats = defaultdict(int)
        self.performance_history = deque(maxlen=1000)
        self.lock_wait_times = defaultdict(list)
        
        # 线程监控
        self.thread_last_activity = {}
        self.thread_locks = {}
        
        self.logger.info("DebugMonitor initialized")
    
    def setup_logging(self):
        """设置日志记录"""
        log_file = os.path.join(self.log_dir, f"debug_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # 创建logger
        self.logger = logging.getLogger('DebugMonitor')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def start_monitoring(self):
        """启动监控"""
        if not self.enabled:
            self.logger.info("DebugMonitor已禁用，跳过监控启动")
            return
            
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Debug monitoring started")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Debug monitoring stopped")
    
    def _monitor_loop(self):
        """监控主循环"""
        while self.is_monitoring:
            try:
                # 记录系统状态
                self._record_system_stats()
                
                # 检查线程状态
                self._check_thread_health()
                
                # 检查死锁
                self._check_deadlocks()
                
                # 清理旧数据
                self._cleanup_old_data()
                
                time.sleep(30.0)  # 优化：每30秒监控一次，从5秒增加到30秒减少CPU占用
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                self.logger.error(traceback.format_exc())
    
    def _record_system_stats(self):
        """记录系统统计信息"""
        try:
            # CPU和内存使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            # 线程数
            thread_count = threading.active_count()
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'network_connections': connections,
                'thread_count': thread_count
            }
            
            self.performance_history.append(stats)
            
            # 如果资源使用率过高，记录警告
            if cpu_percent > 80:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 80:
                self.logger.warning(f"High memory usage: {memory.percent}%")
            if thread_count > 50:
                self.logger.warning(f"High thread count: {thread_count}")
                
        except Exception as e:
            self.logger.error(f"Failed to record system stats: {e}")
    
    def _check_thread_health(self):
        """检查线程健康状态"""
        current_time = time.time()
        
        for thread in threading.enumerate():
            thread_name = thread.name
            
            # 检查线程是否长时间无响应
            if thread_name in self.thread_last_activity:
                inactive_time = current_time - self.thread_last_activity[thread_name]
                if inactive_time > 60:  # 60秒无活动
                    self.logger.warning(f"Thread {thread_name} inactive for {inactive_time:.1f}s")
            
            # 记录线程状态
            self.thread_stats[thread_name] = {
                'is_alive': thread.is_alive(),
                'daemon': thread.daemon,
                'last_check': current_time
            }
    
    def _check_deadlocks(self):
        """检查可能的死锁"""
        # 简单的死锁检测：检查等待时间过长的锁
        current_time = time.time()
        
        for lock_name, wait_times in self.lock_wait_times.items():
            if wait_times:
                avg_wait = sum(wait_times) / len(wait_times)
                max_wait = max(wait_times)
                
                if max_wait > 30:  # 等待超过30秒
                    self.logger.warning(f"Potential deadlock on {lock_name}: max wait {max_wait:.1f}s")
                elif avg_wait > 5:  # 平均等待超过5秒
                    self.logger.warning(f"Slow lock {lock_name}: avg wait {avg_wait:.1f}s")
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        current_time = time.time()
        
        # 清理超过1小时的锁等待时间记录
        for lock_name in list(self.lock_wait_times.keys()):
            self.lock_wait_times[lock_name] = [
                t for t in self.lock_wait_times[lock_name] 
                if current_time - t < 3600
            ]
    
    def record_thread_activity(self, thread_name):
        """记录线程活动"""
        self.thread_last_activity[thread_name] = time.time()
    
    def record_lock_wait(self, lock_name, wait_time):
        """记录锁等待时间"""
        self.lock_wait_times[lock_name].append(wait_time)
        
        # 只保留最近100次记录
        if len(self.lock_wait_times[lock_name]) > 100:
            self.lock_wait_times[lock_name] = self.lock_wait_times[lock_name][-100:]
    
    def record_network_event(self, event_type, details=None):
        """记录网络事件"""
        self.network_stats[event_type] += 1
        
        if details:
            self.logger.debug(f"Network event {event_type}: {details}")
        
        # 记录频繁的网络错误
        if event_type.endswith('_error') and self.network_stats[event_type] % 10 == 0:
            self.logger.warning(f"Frequent network errors: {event_type} occurred {self.network_stats[event_type]} times")
    
    def record_error(self, error_type, error_msg, context=None):
        """记录错误"""
        self.error_stats[error_type] += 1
        
        error_info = {
            'type': error_type,
            'message': error_msg,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'count': self.error_stats[error_type]
        }
        
        self.logger.error(f"Error recorded: {json.dumps(error_info, ensure_ascii=False)}")
    
    def get_status_report(self):
        """获取状态报告"""
        current_time = time.time()
        
        # 活跃线程
        active_threads = [
            {
                'name': t.name,
                'alive': t.is_alive(),
                'daemon': t.daemon,
                'last_activity': current_time - self.thread_last_activity.get(t.name, current_time)
            }
            for t in threading.enumerate()
        ]
        
        # 最近的性能数据
        recent_perf = list(self.performance_history)[-10:] if self.performance_history else []
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.is_monitoring,
            'active_threads': active_threads,
            'network_stats': dict(self.network_stats),
            'error_stats': dict(self.error_stats),
            'recent_performance': recent_perf,
            'lock_stats': {
                name: {
                    'count': len(times),
                    'avg_wait': sum(times) / len(times) if times else 0,
                    'max_wait': max(times) if times else 0
                }
                for name, times in self.lock_wait_times.items()
            }
        }
        
        return report
    
    def save_report(self, filename=None):
        """保存状态报告到文件"""
        if filename is None:
            filename = os.path.join(self.log_dir, f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        report = self.get_status_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Status report saved to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return None

# 全局调试监控器实例 - 默认禁用
debug_monitor = DebugMonitor(enabled=False)

def start_debug_monitoring():
    """启动调试监控"""
    debug_monitor.start_monitoring()

def stop_debug_monitoring():
    """停止调试监控"""
    debug_monitor.stop_monitoring()

def get_debug_report():
    """获取调试报告"""
    return debug_monitor.get_status_report()
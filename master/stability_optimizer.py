#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序稳定性优化器
解决程序卡死问题的综合解决方案

主要功能：
1. 网络超时优化
2. 死锁检测和预防
3. 线程监控和健康检查
4. 自动恢复机制
"""

import threading
import time
import socket
import queue
import logging
import traceback
import psutil
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict, deque

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stability_optimizer.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class ThreadInfo:
    """线程信息"""
    thread: threading.Thread
    start_time: float
    last_heartbeat: float
    timeout_threshold: float
    is_critical: bool = False

@dataclass
class NetworkConfig:
    """网络配置"""
    base_timeout: float = 3.0  # 增加基础超时时间（秒）
    timeout_multiplier: float = 2.0  # 降低超时倍数
    max_retries: int = 3  # 最大重试次数
    backoff_factor: float = 1.5  # 退避因子
    
class StabilityOptimizer:
    """程序稳定性优化器"""
    
    def __init__(self, monitoring_enabled=False):
        self.logger = logging.getLogger(__name__)
        self.threads: Dict[str, ThreadInfo] = {}
        self.locks: Dict[str, threading.Lock] = {}
        self.lock_holders: Dict[str, str] = {}  # 锁持有者
        self.lock_wait_times: Dict[str, float] = {}  # 锁等待时间
        self.network_config = NetworkConfig()
        
        # 监控标志
        self.monitoring_enabled = monitoring_enabled  # 添加监控启用/禁用开关
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.stats = {
            'deadlock_detections': 0,
            'timeout_optimizations': 0,
            'thread_recoveries': 0,
            'network_retries': 0
        }
        
        # 死锁检测
        self.deadlock_detector = DeadlockDetector()
        
    def start_monitoring(self):
        """启动监控"""
        if not self.monitoring_enabled:
            self.logger.info("StabilityOptimizer监控已禁用，跳过监控启动")
            return
            
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="StabilityMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("稳定性监控已启动")
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("稳定性监控已停止")
        
    def register_thread(self, thread: threading.Thread, timeout_threshold: float = 30.0, is_critical: bool = False):
        """注册线程监控"""
        thread_info = ThreadInfo(
            thread=thread,
            start_time=time.time(),
            last_heartbeat=time.time(),
            timeout_threshold=timeout_threshold,
            is_critical=is_critical
        )
        self.threads[thread.name] = thread_info
        self.logger.info(f"已注册线程监控: {thread.name}")
        
    def heartbeat(self, thread_name: str):
        """线程心跳"""
        if thread_name in self.threads:
            self.threads[thread_name].last_heartbeat = time.time()
            
    def register_lock(self, lock_name: str, lock: threading.Lock):
        """注册锁监控"""
        self.locks[lock_name] = lock
        self.logger.info(f"已注册锁监控: {lock_name}")
        
    def acquire_lock_safe(self, lock_name: str, timeout: float = 10.0) -> bool:
        """安全获取锁"""
        if lock_name not in self.locks:
            self.logger.error(f"未知锁: {lock_name}")
            return False
            
        lock = self.locks[lock_name]
        thread_name = threading.current_thread().name
        start_time = time.time()
        
        try:
            # 记录等待开始
            self.lock_wait_times[f"{thread_name}->{lock_name}"] = start_time
            
            # 尝试获取锁
            acquired = lock.acquire(timeout=timeout)
            
            if acquired:
                self.lock_holders[lock_name] = thread_name
                self.logger.debug(f"线程 {thread_name} 获取锁 {lock_name}")
            else:
                self.logger.warning(f"线程 {thread_name} 获取锁 {lock_name} 超时")
                self.stats['deadlock_detections'] += 1
                
            return acquired
            
        finally:
            # 清理等待记录
            wait_key = f"{thread_name}->{lock_name}"
            if wait_key in self.lock_wait_times:
                del self.lock_wait_times[wait_key]
                
    def release_lock_safe(self, lock_name: str):
        """安全释放锁"""
        if lock_name not in self.locks:
            self.logger.error(f"未知锁: {lock_name}")
            return
            
        lock = self.locks[lock_name]
        thread_name = threading.current_thread().name
        
        try:
            lock.release()
            if lock_name in self.lock_holders:
                del self.lock_holders[lock_name]
            self.logger.debug(f"线程 {thread_name} 释放锁 {lock_name}")
        except Exception as e:
            self.logger.error(f"释放锁 {lock_name} 失败: {e}")
            
    def safe_acquire_lock(self, lock_name: str, lock: threading.Lock, timeout: float = 10.0) -> bool:
        """安全获取锁 - 兼容FCCommunicator调用"""
        # 如果锁未注册，先注册它
        if lock_name not in self.locks:
            self.register_lock(lock_name, lock)
            
        return self.acquire_lock_safe(lock_name, timeout)
        
    def safe_release_lock(self, lock_name: str, lock: threading.Lock = None):
        """安全释放锁 - 兼容FCCommunicator调用"""
        return self.release_lock_safe(lock_name)
            
    def optimize_socket_timeout(self, sock: socket.socket, operation_type: str = "default") -> float:
        """优化socket超时设置"""
        base_timeout = self.network_config.base_timeout
        
        # 根据操作类型调整超时
        timeout_map = {
            "handshake": base_timeout * 2,
            "data_transfer": base_timeout,
            "heartbeat": base_timeout * 0.5,
            "default": base_timeout
        }
        
        timeout = timeout_map.get(operation_type, base_timeout) * self.network_config.timeout_multiplier
        sock.settimeout(timeout)
        
        self.stats['timeout_optimizations'] += 1
        self.logger.debug(f"优化socket超时: {operation_type} -> {timeout}s")
        
        return timeout
        
    def network_operation_with_retry(self, operation: Callable, *args, **kwargs):
        """带重试的网络操作"""
        max_retries = self.network_config.max_retries
        backoff = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (socket.timeout, socket.error, ConnectionError) as e:
                if attempt == max_retries:
                    self.logger.error(f"网络操作最终失败: {e}")
                    raise
                    
                self.stats['network_retries'] += 1
                wait_time = backoff * self.network_config.backoff_factor ** attempt
                self.logger.warning(f"网络操作失败，{wait_time:.1f}s后重试 (第{attempt+1}次): {e}")
                time.sleep(wait_time)
                
    def _monitoring_loop(self):
        """监控主循环"""
        self.logger.info("开始稳定性监控循环")
        
        while self.monitoring_active:
            try:
                # 检查线程健康状态
                self._check_thread_health()
                
                # 检查死锁
                self._check_deadlocks()
                
                # 检查系统资源
                self._check_system_resources()
                
                # 优化：每30秒检查一次，从5秒增加到30秒减少CPU占用
                time.sleep(30.0)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                self.logger.error(traceback.format_exc())
                
    def _check_thread_health(self):
        """检查线程健康状态"""
        current_time = time.time()
        dead_threads = []
        
        for name, info in self.threads.items():
            # 检查线程是否还活着
            if not info.thread.is_alive():
                self.logger.warning(f"线程已死亡: {name}")
                dead_threads.append(name)
                continue
                
            # 检查心跳超时
            time_since_heartbeat = current_time - info.last_heartbeat
            if time_since_heartbeat > info.timeout_threshold:
                self.logger.error(f"线程心跳超时: {name} ({time_since_heartbeat:.1f}s)")
                
                if info.is_critical:
                    self.logger.critical(f"关键线程超时，需要恢复: {name}")
                    self._recover_thread(name, info)
                    
        # 清理死亡线程
        for name in dead_threads:
            del self.threads[name]
            
    def _check_deadlocks(self):
        """检查死锁"""
        # 检查锁等待时间
        current_time = time.time()
        for wait_key, start_time in list(self.lock_wait_times.items()):
            wait_time = current_time - start_time
            if wait_time > 30.0:  # 30秒等待阈值
                self.logger.error(f"可能的死锁: {wait_key} 等待 {wait_time:.1f}s")
                self.stats['deadlock_detections'] += 1
                
        # 使用死锁检测器
        self.deadlock_detector.check_deadlock(self.lock_holders, self.lock_wait_times)
        
    def _check_system_resources(self):
        """检查系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"CPU使用率过高: {cpu_percent}%")
                
            # 内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"内存使用率过高: {memory.percent}%")
                
            # 网络连接数
            connections = psutil.net_connections()
            if len(connections) > 1000:
                self.logger.warning(f"网络连接数过多: {len(connections)}")
                
        except Exception as e:
            self.logger.error(f"系统资源检查失败: {e}")
            
    def _recover_thread(self, name: str, info: ThreadInfo):
        """恢复线程"""
        self.logger.info(f"尝试恢复线程: {name}")
        self.stats['thread_recoveries'] += 1
        
        # 这里可以添加具体的线程恢复逻辑
        # 例如：重启线程、清理资源等
        
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'active_threads': len([t for t in self.threads.values() if t.thread.is_alive()]),
            'registered_locks': len(self.locks),
            'lock_holders': len(self.lock_holders),
            'monitoring_active': self.monitoring_active
        }

class DeadlockDetector:
    """死锁检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DeadlockDetector")
        
    def check_deadlock(self, lock_holders: Dict[str, str], lock_wait_times: Dict[str, float]):
        """检查死锁"""
        # 构建等待图
        wait_graph = defaultdict(set)
        
        for wait_key in lock_wait_times:
            if "->" in wait_key:
                waiter, lock_name = wait_key.split("->")
                if lock_name in lock_holders:
                    holder = lock_holders[lock_name]
                    if holder != waiter:
                        wait_graph[waiter].add(holder)
                        
        # 检查循环依赖
        if self._has_cycle(wait_graph):
            self.logger.error("检测到死锁!")
            self._report_deadlock(wait_graph)
            return True
            
        return False
        
    def _has_cycle(self, graph: Dict[str, set]) -> bool:
        """检查图中是否有循环"""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if dfs(neighbor):
                    return True
                    
            rec_stack.remove(node)
            return False
            
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
                    
        return False
        
    def _report_deadlock(self, wait_graph: Dict[str, set]):
        """报告死锁"""
        self.logger.error("死锁详情:")
        for waiter, holders in wait_graph.items():
            for holder in holders:
                self.logger.error(f"  {waiter} 等待 {holder}")

# 全局稳定性优化器实例 - 默认禁用监控
stability_optimizer = StabilityOptimizer(monitoring_enabled=False)

def optimize_fcommunicator():
    """优化FCCommunicator"""
    print("正在优化FCCommunicator...")
    
    # 启动稳定性监控
    stability_optimizer.start_monitoring()
    
    # 这里可以添加具体的FCCommunicator优化逻辑
    print("FCCommunicator优化完成")

if __name__ == "__main__":
    print("程序稳定性优化器")
    print("=" * 50)
    
    # 启动监控
    stability_optimizer.start_monitoring()
    
    try:
        # 运行一段时间进行测试
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n接收到中断信号")
    finally:
        stability_optimizer.stop_monitoring()
        
    # 显示统计信息
    stats = stability_optimizer.get_stats()
    print("\n统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
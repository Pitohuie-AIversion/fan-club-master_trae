#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
队列优化模块
解决数据队列满载和使用率过高的问题
"""

import threading
import time
import queue
import multiprocessing
from typing import Any, Callable, Optional, List
from collections import deque
import logging

class OptimizedQueue:
    """优化的数据队列，支持动态扩容和多消费者处理"""
    
    def __init__(self, initial_size: int = 2000, max_size: int = 10000, 
                 auto_expand: bool = True, consumer_threads: int = 2):
        """
        初始化优化队列
        
        Args:
            initial_size: 初始队列大小
            max_size: 最大队列大小
            auto_expand: 是否自动扩容
            consumer_threads: 消费者线程数量
        """
        self.initial_size = initial_size
        self.max_size = max_size
        self.auto_expand = auto_expand
        self.consumer_threads = consumer_threads
        
        # 主队列
        self.main_queue = queue.Queue(maxsize=initial_size)
        
        # 溢出缓冲区（当主队列满时使用）
        self.overflow_buffer = deque(maxlen=max_size - initial_size)
        
        # 统计信息
        self.stats = {
            'total_items_added': 0,
            'total_items_processed': 0,
            'items_dropped': 0,
            'queue_expansions': 0,
            'overflow_usage': 0,
            'current_size': 0,
            'max_usage': 0
        }
        
        # 锁和控制
        self.lock = threading.RLock()
        self.consumers = []
        self.running = False
        self.callbacks = []
        
        # 性能监控
        self.last_stats_time = time.time()
        self.throughput_samples = deque(maxlen=100)
        
        self.logger = logging.getLogger(__name__)
    
    def put(self, item: Any, timeout: float = 0.001) -> bool:
        """
        向队列添加数据项
        
        Args:
            item: 要添加的数据项
            timeout: 超时时间
            
        Returns:
            bool: 是否成功添加
        """
        with self.lock:
            self.stats['total_items_added'] += 1
            
            try:
                # 尝试放入主队列
                self.main_queue.put(item, timeout=timeout)
                self._update_size_stats()
                return True
                
            except queue.Full:
                # 主队列满，尝试使用溢出缓冲区
                if self.auto_expand and len(self.overflow_buffer) < self.overflow_buffer.maxlen:
                    self.overflow_buffer.append(item)
                    self.stats['overflow_usage'] += 1
                    self._update_size_stats()
                    return True
                else:
                    # 队列完全满，丢弃数据
                    self.stats['items_dropped'] += 1
                    return False
    
    def get(self, timeout: float = 0.1) -> Any:
        """
        从队列获取数据项
        
        Args:
            timeout: 超时时间
            
        Returns:
            Any: 获取的数据项
            
        Raises:
            queue.Empty: 队列为空
        """
        with self.lock:
            # 优先从主队列获取
            try:
                item = self.main_queue.get(timeout=timeout)
                self.stats['total_items_processed'] += 1
                self._update_size_stats()
                return item
                
            except queue.Empty:
                # 主队列空，尝试从溢出缓冲区获取
                if self.overflow_buffer:
                    item = self.overflow_buffer.popleft()
                    self.stats['total_items_processed'] += 1
                    self._update_size_stats()
                    return item
                else:
                    raise queue.Empty()
    
    def qsize(self) -> int:
        """获取队列当前大小"""
        with self.lock:
            return self.main_queue.qsize() + len(self.overflow_buffer)
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        with self.lock:
            return self.main_queue.empty() and len(self.overflow_buffer) == 0
    
    def full(self) -> bool:
        """检查队列是否已满"""
        with self.lock:
            return (self.main_queue.full() and 
                   len(self.overflow_buffer) >= self.overflow_buffer.maxlen)
    
    def get_usage_ratio(self) -> float:
        """获取队列使用率"""
        current_size = self.qsize()
        max_capacity = self.initial_size + self.overflow_buffer.maxlen
        return current_size / max_capacity if max_capacity > 0 else 0.0
    
    def start_consumers(self, processor_func: Callable[[Any], None]):
        """
        启动消费者线程
        
        Args:
            processor_func: 数据处理函数
        """
        if self.running:
            return
        
        self.running = True
        
        for i in range(self.consumer_threads):
            consumer = threading.Thread(
                target=self._consumer_loop,
                args=(processor_func, f"Consumer-{i}"),
                daemon=True
            )
            consumer.start()
            self.consumers.append(consumer)
        
        self.logger.info(f"启动了 {self.consumer_threads} 个消费者线程")
    
    def stop_consumers(self):
        """停止消费者线程"""
        self.running = False
        
        # 等待所有消费者线程结束
        for consumer in self.consumers:
            if consumer.is_alive():
                consumer.join(timeout=2.0)
        
        self.consumers.clear()
        self.logger.info("所有消费者线程已停止")
    
    def _consumer_loop(self, processor_func: Callable[[Any], None], thread_name: str):
        """消费者线程循环"""
        self.logger.info(f"消费者线程 {thread_name} 启动")
        
        while self.running:
            try:
                # 获取数据项
                item = self.get(timeout=1.0)
                
                # 处理数据
                start_time = time.time()
                processor_func(item)
                processing_time = time.time() - start_time
                
                # 记录吞吐量
                self.throughput_samples.append(processing_time)
                
                # 调用回调函数
                for callback in self.callbacks:
                    try:
                        callback(item)
                    except Exception as e:
                        self.logger.error(f"回调函数错误: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"消费者线程 {thread_name} 错误: {e}")
                time.sleep(0.01)
        
        self.logger.info(f"消费者线程 {thread_name} 结束")
    
    def add_callback(self, callback: Callable[[Any], None]):
        """添加数据处理回调函数"""
        self.callbacks.append(callback)
    
    def _update_size_stats(self):
        """更新大小统计信息"""
        current_size = self.qsize()
        self.stats['current_size'] = current_size
        self.stats['max_usage'] = max(self.stats['max_usage'], current_size)
    
    def get_stats(self) -> dict:
        """获取队列统计信息"""
        with self.lock:
            stats = self.stats.copy()
            stats.update({
                'current_size': self.qsize(),
                'usage_ratio': self.get_usage_ratio(),
                'max_capacity': self.initial_size + self.overflow_buffer.maxlen,
                'avg_processing_time': (
                    sum(self.throughput_samples) / len(self.throughput_samples)
                    if self.throughput_samples else 0.0
                ),
                'consumer_threads': len(self.consumers),
                'running': self.running
            })
            return stats
    
    def print_stats(self):
        """打印队列统计信息"""
        stats = self.get_stats()
        print(f"\n=== 队列统计信息 ===")
        print(f"当前大小: {stats['current_size']}")
        print(f"使用率: {stats['usage_ratio']:.1%}")
        print(f"最大容量: {stats['max_capacity']}")
        print(f"总添加: {stats['total_items_added']}")
        print(f"总处理: {stats['total_items_processed']}")
        print(f"丢弃数量: {stats['items_dropped']}")
        print(f"溢出使用: {stats['overflow_usage']}")
        print(f"平均处理时间: {stats['avg_processing_time']:.4f}s")
        print(f"消费者线程: {stats['consumer_threads']}")
        print(f"运行状态: {stats['running']}")


class QueueMonitor:
    """队列监控器，实时监控队列状态并提供告警"""
    
    def __init__(self, optimized_queue: OptimizedQueue, 
                 warning_threshold: float = 0.8, 
                 critical_threshold: float = 0.95,
                 enabled: bool = False):
        """
        初始化队列监控器
        
        Args:
            optimized_queue: 要监控的队列
            warning_threshold: 警告阈值
            critical_threshold: 严重阈值
            enabled: 是否启用监控
        """
        self.queue = optimized_queue
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.enabled = enabled  # 添加启用/禁用开关
        
        self.monitor_thread = None
        self.running = False
        self.last_warning_time = 0
        self.warning_interval = 30.0  # 30秒警告间隔
        
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """启动监控"""
        if not self.enabled:
            self.logger.info("QueueMonitor已禁用，跳过监控启动")
            return
            
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("队列监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("队列监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                usage_ratio = self.queue.get_usage_ratio()
                current_time = time.time()
                
                # 检查是否需要告警
                if (usage_ratio >= self.critical_threshold and 
                    current_time - self.last_warning_time >= self.warning_interval):
                    
                    self.logger.critical(
                        f"队列使用率严重过高: {usage_ratio:.1%} "
                        f"({self.queue.qsize()}/{self.queue.initial_size + self.queue.overflow_buffer.maxlen})"
                    )
                    self.last_warning_time = current_time
                    
                elif (usage_ratio >= self.warning_threshold and 
                      current_time - self.last_warning_time >= self.warning_interval):
                    
                    self.logger.warning(
                        f"队列使用率过高: {usage_ratio:.1%} "
                        f"({self.queue.qsize()}/{self.queue.initial_size + self.queue.overflow_buffer.maxlen})"
                    )
                    self.last_warning_time = current_time
                
                time.sleep(30.0)  # 优化：每30秒检查一次，从5秒增加到30秒减少CPU占用
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(1.0)


# 使用示例
if __name__ == "__main__":
    import random
    
    # 创建优化队列
    opt_queue = OptimizedQueue(
        initial_size=100,
        max_size=500,
        auto_expand=True,
        consumer_threads=3
    )
    
    # 数据处理函数
    def process_data(item):
        # 模拟数据处理
        time.sleep(random.uniform(0.001, 0.01))
        print(f"处理数据: {item}")
    
    # 启动消费者
    opt_queue.start_consumers(process_data)
    
    # 启动监控
    monitor = QueueMonitor(opt_queue)
    monitor.start_monitoring()
    
    try:
        # 模拟数据生产
        for i in range(1000):
            success = opt_queue.put(f"data_{i}")
            if not success:
                print(f"数据 {i} 被丢弃")
            
            if i % 100 == 0:
                opt_queue.print_stats()
            
            time.sleep(0.001)
    
    finally:
        # 清理
        opt_queue.stop_consumers()
        monitor.stop_monitoring()
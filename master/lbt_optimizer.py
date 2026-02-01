#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBT (Listen Before Talk) 优化器
解决信道繁忙和通信阻塞问题

主要功能：
1. 动态RSSI阈值调整
2. 智能重试策略
3. 信道质量监控
4. 自适应延迟机制
"""

import time
import threading
import logging
import random
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lbt_optimizer.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class LBTConfig:
    """LBT配置参数"""
    base_rssi_threshold: float = -80.0  # 基础RSSI阈值 (dBm)
    min_rssi_threshold: float = -90.0   # 最小RSSI阈值
    max_rssi_threshold: float = -60.0   # 最大RSSI阈值
    base_retry_delay: int = 10          # 基础重试延迟 (ms)
    max_retries: int = 5                # 最大重试次数（增加到5次）
    listen_duration: int = 5            # 监听持续时间 (ms)
    backoff_multiplier: float = 1.5     # 退避倍数
    channel_busy_threshold: int = 3     # 信道繁忙检测阈值
    adaptation_window: int = 100        # 自适应窗口大小

@dataclass
class ChannelMeasurement:
    """信道测量数据"""
    timestamp: float
    rssi: float
    is_busy: bool
    retry_count: int
    success: bool

class LBTOptimizer:
    """LBT优化器"""
    
    def __init__(self, config: Optional[LBTConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or LBTConfig()
        
        # 信道质量监控
        self.measurements: deque = deque(maxlen=self.config.adaptation_window)
        self.current_rssi_threshold = self.config.base_rssi_threshold
        self.current_retry_delay = self.config.base_retry_delay
        
        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'successful_transmissions': 0,
            'channel_busy_detections': 0,
            'threshold_adjustments': 0,
            'average_rssi': 0.0,
            'success_rate': 0.0
        }
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        self.logger.info("LBT优化器初始化完成")
    
    def listen_before_talk(self, rssi_reading: float, attempt_count: int = 0) -> Tuple[bool, int]:
        """
        执行LBT检查
        
        Args:
            rssi_reading: 当前RSSI读数 (dBm)
            attempt_count: 当前尝试次数
            
        Returns:
            (can_transmit, recommended_delay)
        """
        with self.lock:
            self.stats['total_attempts'] += 1
            
            # 记录测量数据
            measurement = ChannelMeasurement(
                timestamp=time.time(),
                rssi=rssi_reading,
                is_busy=rssi_reading > self.current_rssi_threshold,
                retry_count=attempt_count,
                success=False  # 将在传输后更新
            )
            
            # 检查信道是否繁忙
            if rssi_reading > self.current_rssi_threshold:
                self.stats['channel_busy_detections'] += 1
                self.logger.debug(f"信道繁忙: RSSI = {rssi_reading} dBm > 阈值 {self.current_rssi_threshold} dBm")
                
                # 计算自适应延迟
                delay = self._calculate_adaptive_delay(attempt_count, rssi_reading)
                
                # 记录测量并触发自适应调整
                self.measurements.append(measurement)
                self._adapt_parameters()
                
                return False, delay
            else:
                self.logger.debug(f"信道空闲: RSSI = {rssi_reading} dBm <= 阈值 {self.current_rssi_threshold} dBm")
                measurement.success = True
                self.measurements.append(measurement)
                self.stats['successful_transmissions'] += 1
                
                return True, 0
    
    def _calculate_adaptive_delay(self, attempt_count: int, rssi: float) -> int:
        """计算自适应延迟"""
        # 基础延迟随尝试次数指数增长
        base_delay = self.current_retry_delay * (self.config.backoff_multiplier ** attempt_count)
        
        # 根据RSSI强度调整延迟
        rssi_factor = max(1.0, (rssi - self.config.min_rssi_threshold) / 
                         (self.config.max_rssi_threshold - self.config.min_rssi_threshold))
        
        # 添加随机抖动以避免同步冲突
        jitter = random.uniform(0.8, 1.2)
        
        adaptive_delay = int(base_delay * rssi_factor * jitter)
        
        # 限制最大延迟
        max_delay = self.config.base_retry_delay * 10
        return min(adaptive_delay, max_delay)
    
    def _adapt_parameters(self):
        """自适应参数调整"""
        if len(self.measurements) < 10:  # 需要足够的数据点
            return
        
        recent_measurements = list(self.measurements)[-50:]  # 最近50次测量
        
        # 计算成功率
        success_count = sum(1 for m in recent_measurements if m.success)
        success_rate = success_count / len(recent_measurements)
        
        # 计算平均RSSI
        avg_rssi = statistics.mean(m.rssi for m in recent_measurements)
        
        # 更新统计信息
        self.stats['success_rate'] = success_rate
        self.stats['average_rssi'] = avg_rssi
        
        # 自适应RSSI阈值调整
        old_threshold = self.current_rssi_threshold
        
        if success_rate < 0.7:  # 成功率过低，降低阈值（更严格）
            self.current_rssi_threshold = max(
                self.config.min_rssi_threshold,
                self.current_rssi_threshold - 2.0
            )
        elif success_rate > 0.9:  # 成功率很高，可以提高阈值（更宽松）
            self.current_rssi_threshold = min(
                self.config.max_rssi_threshold,
                self.current_rssi_threshold + 1.0
            )
        
        if abs(self.current_rssi_threshold - old_threshold) > 0.1:
            self.stats['threshold_adjustments'] += 1
            self.logger.info(f"RSSI阈值调整: {old_threshold:.1f} -> {self.current_rssi_threshold:.1f} dBm")
        
        # 自适应重试延迟调整
        busy_rate = sum(1 for m in recent_measurements if m.is_busy) / len(recent_measurements)
        
        if busy_rate > 0.5:  # 信道繁忙率过高，增加延迟
            self.current_retry_delay = min(50, int(self.current_retry_delay * 1.2))
        elif busy_rate < 0.2:  # 信道繁忙率较低，减少延迟
            self.current_retry_delay = max(5, int(self.current_retry_delay * 0.9))
    
    def should_retry(self, attempt_count: int) -> bool:
        """判断是否应该重试"""
        return attempt_count < self.config.max_retries
    
    def get_optimized_config(self) -> Dict:
        """获取优化后的配置"""
        return {
            'rssi_threshold': self.current_rssi_threshold,
            'retry_delay': self.current_retry_delay,
            'max_retries': self.config.max_retries,
            'listen_duration': self.config.listen_duration
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            return self.stats.copy()
    
    def get_channel_quality_report(self) -> Dict:
        """获取信道质量报告"""
        if not self.measurements:
            return {'status': 'no_data'}
        
        recent_measurements = list(self.measurements)[-20:]  # 最近20次测量
        
        rssi_values = [m.rssi for m in recent_measurements]
        busy_count = sum(1 for m in recent_measurements if m.is_busy)
        success_count = sum(1 for m in recent_measurements if m.success)
        
        return {
            'status': 'active',
            'measurements_count': len(recent_measurements),
            'average_rssi': statistics.mean(rssi_values),
            'rssi_std': statistics.stdev(rssi_values) if len(rssi_values) > 1 else 0,
            'min_rssi': min(rssi_values),
            'max_rssi': max(rssi_values),
            'busy_rate': busy_count / len(recent_measurements),
            'success_rate': success_count / len(recent_measurements),
            'current_threshold': self.current_rssi_threshold,
            'current_delay': self.current_retry_delay
        }
    
    def export_measurements(self, filename: str):
        """导出测量数据"""
        data = {
            'config': {
                'base_rssi_threshold': self.config.base_rssi_threshold,
                'max_retries': self.config.max_retries,
                'base_retry_delay': self.config.base_retry_delay
            },
            'current_settings': {
                'rssi_threshold': self.current_rssi_threshold,
                'retry_delay': self.current_retry_delay
            },
            'stats': self.stats,
            'measurements': [
                {
                    'timestamp': m.timestamp,
                    'rssi': m.rssi,
                    'is_busy': m.is_busy,
                    'retry_count': m.retry_count,
                    'success': m.success
                }
                for m in self.measurements
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"测量数据已导出到 {filename}")

# 全局LBT优化器实例
lbt_optimizer = LBTOptimizer()

def simulate_lbt_scenario():
    """模拟LBT场景进行测试"""
    print("LBT优化器测试")
    print("=" * 50)
    
    # 模拟不同的RSSI场景
    scenarios = [
        (-85, "信道空闲"),
        (-65, "信道繁忙"),
        (-70, "中等干扰"),
        (-45, "强干扰"),
        (-90, "信道很空闲")
    ]
    
    for rssi, description in scenarios:
        print(f"\n测试场景: {description} (RSSI: {rssi} dBm)")
        
        attempt = 0
        while attempt < 5:
            can_transmit, delay = lbt_optimizer.listen_before_talk(rssi, attempt)
            
            if can_transmit:
                print(f"  尝试 {attempt + 1}: 可以传输")
                break
            else:
                print(f"  尝试 {attempt + 1}: 信道繁忙，延迟 {delay} ms")
                attempt += 1
                
                if not lbt_optimizer.should_retry(attempt):
                    print(f"  达到最大重试次数，放弃传输")
                    break
    
    # 显示统计信息
    print("\n统计信息:")
    stats = lbt_optimizer.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 显示信道质量报告
    print("\n信道质量报告:")
    report = lbt_optimizer.get_channel_quality_report()
    for key, value in report.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    simulate_lbt_scenario()
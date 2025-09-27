#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号生成演示脚本
展示系统启动后产生的信号数据
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

# 添加fc模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'fc'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'fc', 'backend'))

try:
    from fc.backend.signal_acquisition import SimulatedHardware, AcquisitionConfig, ChannelConfig
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

def demo_signal_generation():
    """演示信号生成"""
    print("信号生成演示")
    print("=" * 40)
    
    # 创建配置
    config = AcquisitionConfig()
    config.sample_rate = 1000.0  # 1kHz采样率
    config.channels = ["Channel_1", "Channel_2", "Channel_3"]  # 3通道
    config.resolution = 16
    
    # 创建模拟硬件
    hardware = SimulatedHardware()
    hardware.initialize(config)
    
    # 配置通道
    for i, ch_id in enumerate(config.channels):
        ch_config = ChannelConfig(ch_id)
        ch_config.enabled = True
        ch_config.gain = 1.0
        ch_config.offset = 0.0
        hardware.configure_channel(ch_config)
    
    # 启动采集
    print("启动信号采集...")
    hardware.start_acquisition()
    
    print("\n生成的信号数据示例:")
    print("-" * 60)
    print(f"{'时间戳':<12} {'通道':<10} {'信号值':<10} {'原始值':<8} {'质量':<6}")
    print("-" * 60)
    
    # 生成并显示信号数据
    for i in range(10):  # 显示10批数据
        samples = hardware.read_samples(3)  # 每次读取3个样本（每通道1个）
        
        for sample in samples:
            timestamp_str = f"{sample.timestamp:.3f}"
            print(f"{timestamp_str:<12} {sample.channel_id:<10} {sample.value:<10.3f} {sample.raw_value:<8} {sample.quality:<6.3f}")
        
        time.sleep(0.1)  # 100ms间隔
    
    print("-" * 60)
    
    # 停止采集
    hardware.stop_acquisition()
    
    print("\n信号特征说明:")
    print("• Channel_1: 10Hz 正弦波 + 噪声")
    print("• Channel_2: 15Hz 正弦波 + 噪声")
    print("• Channel_3: 20Hz 正弦波 + 噪声")
    print("• 每个通道都有不同的频率特征")
    print("• 信号值范围: 约 ±1.1 (包含噪声)")
    print("• 质量指标: 0.95-1.0 (模拟高质量信号)")
    
    print("\n✓ 系统启动后确实会产生连续的信号数据!")

if __name__ == "__main__":
    demo_signal_generation()
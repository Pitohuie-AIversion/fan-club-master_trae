#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tach信号实时监控工具
专门用于监控和分析风机转速反馈信号的实时状态
"""

import time
import threading
import queue
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional

# 导入FC系统模块
try:
    import fc.archive as ac
    import fc.standards as s
    from fc.backend.mkiii import FCCommunicator as fcc
except ImportError:
    print("警告: 无法导入FC模块，将使用模拟数据")
    ac = None
    s = None
    fcc = None

@dataclass
class TachSignalData:
    """Tach信号数据结构"""
    timestamp: float
    slave_id: int
    fan_id: int
    rpm: int
    duty_cycle: float
    signal_quality: float
    data_index: int
    
class TachSignalMonitor:
    """Tach信号监控器"""
    
    def __init__(self, max_slaves=8, max_fans_per_slave=16):
        self.max_slaves = max_slaves
        self.max_fans_per_slave = max_fans_per_slave
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 数据存储
        self.signal_data = deque(maxlen=10000)
        self.data_queue = queue.Queue()
        
        # 统计信息
        self.stats = {
            'total_readings': 0,
            'active_slaves': set(),
            'active_fans': {},
            'rpm_ranges': {},
            'signal_quality': {},
            'last_update': 0
        }
        
        # 模拟数据生成器（用于测试）
        self.simulation_mode = True
        self.sim_rpm_targets = {}
        
    def start_monitoring(self, simulation=True):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.simulation_mode = simulation
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            mode_str = "模拟模式" if simulation else "实际模式"
            print(f"Tach信号监控已启动 ({mode_str})")
            
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("Tach信号监控已停止")
        
    def _monitor_loop(self):
        """监控主循环"""
        while self.is_monitoring:
            try:
                if self.simulation_mode:
                    self._generate_simulation_data()
                else:
                    self._read_real_data()
                    
                time.sleep(0.1)  # 10Hz采样率
                
            except Exception as e:
                print(f"监控循环错误: {e}")
                time.sleep(1.0)
                
    def _generate_simulation_data(self):
        """生成模拟数据"""
        current_time = time.time()
        
        # 模拟2个slave，每个4个风机
        for slave_id in range(2):
            for fan_id in range(4):
                # 生成模拟RPM数据
                base_rpm = 1000 + slave_id * 500 + fan_id * 200
                noise = np.random.normal(0, 50)
                rpm = max(0, int(base_rpm + noise + 500 * np.sin(current_time * 0.1)))
                
                # 生成模拟占空比
                duty_cycle = min(1.0, rpm / 12000.0)
                
                # 生成信号质量
                signal_quality = 0.8 + 0.2 * np.random.random()
                
                # 创建数据点
                data_point = TachSignalData(
                    timestamp=current_time,
                    slave_id=slave_id,
                    fan_id=fan_id,
                    rpm=rpm,
                    duty_cycle=duty_cycle,
                    signal_quality=signal_quality,
                    data_index=self.stats['total_readings']
                )
                
                # 存储数据
                self.signal_data.append(data_point)
                self.data_queue.put(data_point)
                self.stats['total_readings'] += 1
                
                # 更新统计信息
                self._update_stats(data_point)
                
    def _read_real_data(self):
        """读取真实数据（需要与FC系统集成）"""
        # TODO: 实现与FC系统的实际集成
        # 这里需要从FCCommunicator获取实际的RPM数据
        print("实际数据读取功能待实现")
        
    def _update_stats(self, data_point: TachSignalData):
        """更新统计信息"""
        slave_fan_key = f"S{data_point.slave_id}F{data_point.fan_id}"
        
        # 更新活跃设备
        self.stats['active_slaves'].add(data_point.slave_id)
        
        if data_point.slave_id not in self.stats['active_fans']:
            self.stats['active_fans'][data_point.slave_id] = set()
        self.stats['active_fans'][data_point.slave_id].add(data_point.fan_id)
        
        # 更新RPM范围
        if slave_fan_key not in self.stats['rpm_ranges']:
            self.stats['rpm_ranges'][slave_fan_key] = {'min': data_point.rpm, 'max': data_point.rpm}
        else:
            self.stats['rpm_ranges'][slave_fan_key]['min'] = min(
                self.stats['rpm_ranges'][slave_fan_key]['min'], data_point.rpm)
            self.stats['rpm_ranges'][slave_fan_key]['max'] = max(
                self.stats['rpm_ranges'][slave_fan_key]['max'], data_point.rpm)
                
        # 更新信号质量
        if slave_fan_key not in self.stats['signal_quality']:
            self.stats['signal_quality'][slave_fan_key] = []
        self.stats['signal_quality'][slave_fan_key].append(data_point.signal_quality)
        
        # 保持最近100个质量值
        if len(self.stats['signal_quality'][slave_fan_key]) > 100:
            self.stats['signal_quality'][slave_fan_key].pop(0)
            
        self.stats['last_update'] = data_point.timestamp
        
    def get_current_stats(self) -> Dict:
        """获取当前统计信息"""
        stats_summary = {
            'total_readings': self.stats['total_readings'],
            'active_slaves': len(self.stats['active_slaves']),
            'total_fans': sum(len(fans) for fans in self.stats['active_fans'].values()),
            'last_update': self.stats['last_update'],
            'fan_details': {}
        }
        
        # 详细的风机信息
        for slave_id in self.stats['active_slaves']:
            for fan_id in self.stats['active_fans'].get(slave_id, []):
                key = f"S{slave_id}F{fan_id}"
                if key in self.stats['rpm_ranges']:
                    rpm_range = self.stats['rpm_ranges'][key]
                    quality_values = self.stats['signal_quality'].get(key, [])
                    avg_quality = np.mean(quality_values) if quality_values else 0
                    
                    stats_summary['fan_details'][key] = {
                        'rpm_min': rpm_range['min'],
                        'rpm_max': rpm_range['max'],
                        'avg_signal_quality': avg_quality,
                        'readings_count': len(quality_values)
                    }
                    
        return stats_summary
        
    def get_recent_data(self, seconds: int = 30) -> List[TachSignalData]:
        """获取最近N秒的数据"""
        cutoff_time = time.time() - seconds
        return [data for data in self.signal_data if data.timestamp >= cutoff_time]
        
    def plot_realtime_rpm(self, duration_minutes: int = 5):
        """实时绘制RPM数据"""
        plt.ion()
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Tach信号实时监控 - RPM数据', fontsize=16)
        
        # 数据缓存
        plot_data = {}
        
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        
        try:
            while self.is_monitoring and time.time() < end_time:
                try:
                    # 获取新数据
                    data_point = self.data_queue.get(timeout=0.5)
                    
                    # 组织绘图数据
                    key = f"S{data_point.slave_id}F{data_point.fan_id}"
                    if key not in plot_data:
                        plot_data[key] = {'times': deque(maxlen=300), 'rpms': deque(maxlen=300)}
                        
                    relative_time = data_point.timestamp - start_time
                    plot_data[key]['times'].append(relative_time)
                    plot_data[key]['rpms'].append(data_point.rpm)
                    
                    # 更新图表
                    if len(plot_data) > 0:
                        for i, (key, data) in enumerate(plot_data.items()):
                            if i >= 4:  # 最多显示4个风机
                                break
                                
                            ax = axes[i // 2, i % 2]
                            ax.clear()
                            
                            if len(data['times']) > 1:
                                ax.plot(data['times'], data['rpms'], 'b-', linewidth=2)
                                ax.set_title(f'风机 {key} - RPM')
                                ax.set_xlabel('时间 (s)')
                                ax.set_ylabel('RPM')
                                ax.grid(True, alpha=0.3)
                                
                                # 显示当前值
                                if data['rpms']:
                                    current_rpm = data['rpms'][-1]
                                    ax.text(0.02, 0.98, f'当前: {current_rpm} RPM', 
                                           transform=ax.transAxes, 
                                           verticalalignment='top',
                                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                        
                        plt.tight_layout()
                        plt.pause(0.01)
                        
                except queue.Empty:
                    continue
                    
        except KeyboardInterrupt:
            print("\n绘图中断")
        finally:
            plt.ioff()
            plt.show()
            
    def save_data(self, filename: str):
        """保存监控数据"""
        data_to_save = {
            'metadata': {
                'total_readings': self.stats['total_readings'],
                'monitoring_duration': time.time() - (self.signal_data[0].timestamp if self.signal_data else time.time()),
                'max_slaves': self.max_slaves,
                'max_fans_per_slave': self.max_fans_per_slave
            },
            'statistics': self.get_current_stats(),
            'raw_data': [
                {
                    'timestamp': data.timestamp,
                    'slave_id': data.slave_id,
                    'fan_id': data.fan_id,
                    'rpm': data.rpm,
                    'duty_cycle': data.duty_cycle,
                    'signal_quality': data.signal_quality,
                    'data_index': data.data_index
                }
                for data in self.signal_data
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        print(f"监控数据已保存到: {filename}")
        
    def print_status(self):
        """打印当前状态"""
        stats = self.get_current_stats()
        
        print("\n=== Tach信号监控状态 ===")
        print(f"总读数: {stats['total_readings']}")
        print(f"活跃Slave数: {stats['active_slaves']}")
        print(f"总风机数: {stats['total_fans']}")
        print(f"最后更新: {time.strftime('%H:%M:%S', time.localtime(stats['last_update']))}")
        
        print("\n风机详情:")
        for fan_key, details in stats['fan_details'].items():
            print(f"  {fan_key}: RPM范围 {details['rpm_min']}-{details['rpm_max']}, "
                  f"信号质量 {details['avg_signal_quality']:.3f}, "
                  f"读数 {details['readings_count']}")

def main():
    """主函数"""
    print("=== Tach信号实时监控工具 ===")
    print("专门用于监控风机转速反馈信号")
    
    monitor = TachSignalMonitor()
    
    try:
        # 启动监控
        monitor.start_monitoring(simulation=True)
        
        print("\n选择监控模式:")
        print("1. 状态监控 (每5秒显示统计)")
        print("2. 实时绘图")
        print("3. 数据导出")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == '1':
            print("状态监控模式，按Ctrl+C停止...")
            try:
                while True:
                    time.sleep(5)
                    monitor.print_status()
            except KeyboardInterrupt:
                pass
                
        elif choice == '2':
            print("实时绘图模式，按Ctrl+C停止...")
            monitor.plot_realtime_rpm(5)  # 5分钟
            
        elif choice == '3':
            print("数据收集模式，收集30秒数据...")
            time.sleep(30)
            
        # 保存数据
        timestamp = int(time.time())
        monitor.save_data(f"tach_monitor_{timestamp}.json")
        
        # 显示最终统计
        monitor.print_status()
        
    except KeyboardInterrupt:
        print("\n接收到中断信号")
    finally:
        monitor.stop_monitoring()
        print("监控已停止")

if __name__ == "__main__":
    main()
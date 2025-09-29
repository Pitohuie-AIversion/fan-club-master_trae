#!/usr/bin/python3
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##   ______   _    _    _____   __ _    _   _  ____                       ##
##  |__  / | | |  / \  / _ \ \ / // \  | \ | |/ ___|                      ##
##    / /| |_| | / _ \| | | \ V // _ \ |  \| | |  _                       ##
##   / /_|  _  |/ ___ \ |_| || |/ ___ \| |\  | |_| |                      ##
##  /____|_| |_/_/___\_\___/_|_/_/_  \_\_| \_\____|                      ##
##  |  _ \  / \  / ___|| | | | | | | / \  |_ _|                           ##
##  | | | |/ _ \ \___ \| |_| | | | |/ _ \  | |                            ##
##  | |_| / ___ \ ___) |  _  | |_| / ___ \ | |                            ##
##  |____/_/   \_\____/|_| |_|\___/_/   \_\___|                           ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>   ##              ##
## dashuai                    ## <dschen2018@gmail.com>      ##              ##
##                            ##                             ##              ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Tach signal analyzer for fan speed feedback signals.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import time
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import deque
import threading
import queue
import json

@dataclass
class TachSignalConfig:
    """Tach信号配置"""
    pulses_per_rotation: int = 2  # 每转脉冲数
    max_rpm: int = 11500  # 最大转速
    min_rpm: int = 100    # 最小转速
    timeout_us: int = 1000000  # 超时时间(微秒)
    counter_counts: int = 10   # 计数脉冲数
    frequency_hz: int = 1000   # 采样频率

@dataclass
class TachReading:
    """Tach读数"""
    timestamp: float
    rpm: int
    pulse_count: int
    measurement_time_us: int
    duty_cycle: float
    signal_quality: float
    timeout_occurred: bool = False

class TachSignalSimulator:
    """Tach信号模拟器"""
    
    def __init__(self, config: TachSignalConfig):
        self.config = config
        self.current_rpm = 0
        self.target_rpm = 0
        self.duty_cycle = 0.0
        self.noise_level = 0.05
        self.is_running = False
        
    def set_target_rpm(self, rpm: int):
        """设置目标转速"""
        self.target_rpm = max(0, min(rpm, self.config.max_rpm))
        
    def set_duty_cycle(self, dc: float):
        """设置占空比"""
        self.duty_cycle = max(0.0, min(1.0, dc))
        # 简单的线性模型：RPM与占空比成正比
        self.target_rpm = int(self.duty_cycle * self.config.max_rpm)
        
    def simulate_rpm_response(self, dt: float) -> int:
        """模拟RPM响应（一阶滞后）"""
        tau = 0.1  # 时间常数
        alpha = dt / (tau + dt)
        self.current_rpm += alpha * (self.target_rpm - self.current_rpm)
        
        # 添加噪声
        noise = np.random.normal(0, self.noise_level * self.current_rpm)
        measured_rpm = max(0, self.current_rpm + noise)
        
        return int(measured_rpm)
        
    def generate_pulse_train(self, rpm: int, duration_s: float) -> List[float]:
        """生成脉冲序列"""
        if rpm <= 0:
            return []
            
        # 计算脉冲间隔
        pulses_per_second = (rpm / 60.0) * self.config.pulses_per_rotation
        pulse_interval = 1.0 / pulses_per_second if pulses_per_second > 0 else float('inf')
        
        pulses = []
        t = 0
        while t < duration_s:
            pulses.append(t)
            t += pulse_interval
            
        return pulses
        
    def measure_rpm_from_pulses(self, pulses: List[float]) -> TachReading:
        """从脉冲序列测量RPM"""
        timestamp = time.time()
        
        if len(pulses) < self.config.counter_counts:
            # 脉冲数不足，返回0 RPM
            return TachReading(
                timestamp=timestamp,
                rpm=0,
                pulse_count=len(pulses),
                measurement_time_us=int(self.config.timeout_us),
                duty_cycle=self.duty_cycle,
                signal_quality=0.0,
                timeout_occurred=True
            )
            
        # 计算测量时间
        if len(pulses) >= 2:
            measurement_time = pulses[self.config.counter_counts-1] - pulses[0]
            measurement_time_us = int(measurement_time * 1e6)
        else:
            measurement_time_us = self.config.timeout_us
            
        # 计算RPM
        if measurement_time_us > 0:
            rpm = int((60e6 * self.config.counter_counts) / 
                     (measurement_time_us * self.config.pulses_per_rotation))
        else:
            rpm = 0
            
        # 计算信号质量
        signal_quality = min(1.0, len(pulses) / self.config.counter_counts)
        
        return TachReading(
            timestamp=timestamp,
            rpm=rpm,
            pulse_count=len(pulses),
            measurement_time_us=measurement_time_us,
            duty_cycle=self.duty_cycle,
            signal_quality=signal_quality
        )

class TachSignalAnalyzer:
    """Tach信号分析器"""
    
    def __init__(self, config: TachSignalConfig):
        self.config = config
        self.simulator = TachSignalSimulator(config)
        self.readings = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitor_thread = None
        self.data_queue = queue.Queue()
        
    def start_monitoring(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("Tach信号监控已启动")
            
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("Tach信号监控已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        dt = 1.0 / self.config.frequency_hz
        
        while self.is_monitoring:
            start_time = time.time()
            
            # 模拟RPM响应
            current_rpm = self.simulator.simulate_rpm_response(dt)
            
            # 生成脉冲序列
            pulses = self.simulator.generate_pulse_train(current_rpm, dt)
            
            # 测量RPM
            reading = self.simulator.measure_rpm_from_pulses(pulses)
            
            # 存储读数
            self.readings.append(reading)
            self.data_queue.put(reading)
            
            # 控制采样频率
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
            
    def set_duty_cycle(self, dc: float):
        """设置占空比"""
        self.simulator.set_duty_cycle(dc)
        print(f"设置占空比: {dc:.3f}, 目标RPM: {self.simulator.target_rpm}")
        
    def get_latest_readings(self, count: int = 10) -> List[TachReading]:
        """获取最新读数"""
        return list(self.readings)[-count:] if len(self.readings) >= count else list(self.readings)
        
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.readings:
            return {}
            
        rpms = [r.rpm for r in self.readings]
        dcs = [r.duty_cycle for r in self.readings]
        qualities = [r.signal_quality for r in self.readings]
        timeouts = sum(1 for r in self.readings if r.timeout_occurred)
        
        return {
            'total_readings': len(self.readings),
            'rpm_stats': {
                'mean': np.mean(rpms),
                'std': np.std(rpms),
                'min': np.min(rpms),
                'max': np.max(rpms)
            },
            'duty_cycle_stats': {
                'mean': np.mean(dcs),
                'std': np.std(dcs),
                'min': np.min(dcs),
                'max': np.max(dcs)
            },
            'signal_quality': {
                'mean': np.mean(qualities),
                'min': np.min(qualities)
            },
            'timeout_rate': timeouts / len(self.readings) if self.readings else 0
        }
        
    def plot_realtime_data(self, duration_s: int = 30):
        """实时绘图"""
        plt.ion()
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        timestamps = deque(maxlen=duration_s * self.config.frequency_hz)
        rpms = deque(maxlen=duration_s * self.config.frequency_hz)
        dcs = deque(maxlen=duration_s * self.config.frequency_hz)
        qualities = deque(maxlen=duration_s * self.config.frequency_hz)
        
        start_time = time.time()
        
        try:
            while self.is_monitoring:
                try:
                    # 获取新数据
                    reading = self.data_queue.get(timeout=0.1)
                    
                    relative_time = reading.timestamp - start_time
                    timestamps.append(relative_time)
                    rpms.append(reading.rpm)
                    dcs.append(reading.duty_cycle)
                    qualities.append(reading.signal_quality)
                    
                    # 更新图表
                    if len(timestamps) > 1:
                        ax1.clear()
                        ax1.plot(timestamps, rpms, 'b-', label='实际RPM')
                        ax1.set_ylabel('RPM')
                        ax1.set_title('Tach信号实时监控')
                        ax1.legend()
                        ax1.grid(True)
                        
                        ax2.clear()
                        ax2.plot(timestamps, dcs, 'r-', label='占空比')
                        ax2.set_ylabel('占空比')
                        ax2.legend()
                        ax2.grid(True)
                        
                        ax3.clear()
                        ax3.plot(timestamps, qualities, 'g-', label='信号质量')
                        ax3.set_ylabel('信号质量')
                        ax3.set_xlabel('时间 (s)')
                        ax3.legend()
                        ax3.grid(True)
                        
                        plt.tight_layout()
                        plt.pause(0.01)
                        
                except queue.Empty:
                    continue
                    
        except KeyboardInterrupt:
            print("\n绘图中断")
        finally:
            plt.ioff()
            plt.show()
            
    def run_step_response_test(self, test_duration: int = 10):
        """运行阶跃响应测试"""
        print("开始阶跃响应测试...")
        
        # 测试不同占空比
        test_points = [0.0, 0.2, 0.5, 0.8, 1.0, 0.0]
        
        for i, dc in enumerate(test_points):
            print(f"\n测试点 {i+1}/{len(test_points)}: 占空比 = {dc:.1f}")
            self.set_duty_cycle(dc)
            
            # 等待系统稳定
            time.sleep(test_duration / len(test_points))
            
            # 获取统计信息
            stats = self.get_statistics()
            if stats:
                print(f"  平均RPM: {stats['rpm_stats']['mean']:.0f}")
                print(f"  RPM标准差: {stats['rpm_stats']['std']:.1f}")
                print(f"  信号质量: {stats['signal_quality']['mean']:.3f}")
                print(f"  超时率: {stats['timeout_rate']:.3f}")
                
    def save_data(self, filename: str):
        """保存数据"""
        data = {
            'config': {
                'pulses_per_rotation': self.config.pulses_per_rotation,
                'max_rpm': self.config.max_rpm,
                'min_rpm': self.config.min_rpm,
                'timeout_us': self.config.timeout_us,
                'counter_counts': self.config.counter_counts,
                'frequency_hz': self.config.frequency_hz
            },
            'readings': [
                {
                    'timestamp': r.timestamp,
                    'rpm': r.rpm,
                    'pulse_count': r.pulse_count,
                    'measurement_time_us': r.measurement_time_us,
                    'duty_cycle': r.duty_cycle,
                    'signal_quality': r.signal_quality,
                    'timeout_occurred': r.timeout_occurred
                }
                for r in self.readings
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"数据已保存到: {filename}")

def main():
    """主函数"""
    print("=== Tach信号分析器 ===")
    print("专注于风机转速反馈信号的分析和测试")
    
    # 创建配置
    config = TachSignalConfig(
        pulses_per_rotation=2,
        max_rpm=11500,
        min_rpm=100,
        timeout_us=1000000,
        counter_counts=10,
        frequency_hz=100
    )
    
    # 创建分析器
    analyzer = TachSignalAnalyzer(config)
    
    try:
        # 启动监控
        analyzer.start_monitoring()
        
        print("\n选择测试模式:")
        print("1. 阶跃响应测试")
        print("2. 实时监控")
        print("3. 手动控制")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == '1':
            analyzer.run_step_response_test(30)
            
        elif choice == '2':
            print("启动实时监控，按Ctrl+C停止...")
            analyzer.plot_realtime_data(60)
            
        elif choice == '3':
            print("手动控制模式，输入占空比 (0.0-1.0)，输入'q'退出")
            while True:
                try:
                    user_input = input("占空比: ").strip()
                    if user_input.lower() == 'q':
                        break
                    dc = float(user_input)
                    analyzer.set_duty_cycle(dc)
                    
                    # 显示最新读数
                    time.sleep(1)
                    latest = analyzer.get_latest_readings(5)
                    if latest:
                        print(f"最新RPM: {latest[-1].rpm}, 质量: {latest[-1].signal_quality:.3f}")
                        
                except ValueError:
                    print("请输入有效的数值")
                except KeyboardInterrupt:
                    break
        
        # 保存数据
        timestamp = int(time.time())
        analyzer.save_data(f"tach_data_{timestamp}.json")
        
        # 显示最终统计
        stats = analyzer.get_statistics()
        if stats:
            print("\n=== 最终统计 ===")
            print(f"总读数: {stats['total_readings']}")
            print(f"平均RPM: {stats['rpm_stats']['mean']:.1f} ± {stats['rpm_stats']['std']:.1f}")
            print(f"RPM范围: {stats['rpm_stats']['min']:.0f} - {stats['rpm_stats']['max']:.0f}")
            print(f"平均信号质量: {stats['signal_quality']['mean']:.3f}")
            print(f"超时率: {stats['timeout_rate']:.3f}")
            
    except KeyboardInterrupt:
        print("\n接收到中断信号")
    finally:
        analyzer.stop_monitoring()
        print("分析器已停止")

if __name__ == "__main__":
    main()
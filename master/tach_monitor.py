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
 + Real-time monitoring tool for fan speed feedback signals.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

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
    
    def __init__(self, max_slaves=8, max_fans_per_slave=16, fc_communicator=None):
        self.max_slaves = max_slaves
        self.max_fans_per_slave = max_fans_per_slave
        self.fc_communicator = fc_communicator
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 数据存储
        self.signal_data = deque(maxlen=10000)
        self.data_queue = queue.Queue()
        
        # 异常处理相关
        self.error_count = 0
        self.max_consecutive_errors = 10
        self.last_error_time = 0
        self.error_recovery_delay = 1.0  # 秒
        
        # 数据质量监控
        self.data_timeout_threshold = 5.0  # 秒
        self.last_successful_read = time.time()
        
        # 性能优化相关
        self.batch_size = 8  # 批处理大小
        self.data_cache = {}  # 数据缓存
        self.cache_timeout = 0.5  # 缓存超时时间（秒）
        self.performance_stats = {
            'read_times': deque(maxlen=100),
            'process_times': deque(maxlen=100),
            'data_rates': deque(maxlen=100)
        }
        
        # 实时性优化
        self.priority_fans = set()  # 优先监控的风机
        self.adaptive_interval = True  # 自适应采样间隔
        self.min_interval = 0.05  # 最小采样间隔（50ms）
        self.max_interval = 1.0   # 最大采样间隔（1s）
        self.fan_priority_scores = {}  # 风机优先级分数
        
        # 统计信息
        self.stats = {
            'total_readings': 0,
            'active_slaves': set(),
            'active_fans': {},
            'rpm_ranges': {},
            'signal_quality': {},
            'last_update': 0,
            'error_count': 0,
            'connection_status': 'disconnected',
            'performance': {
                'avg_read_time': 0,
                'avg_process_time': 0,
                'data_rate': 0
            }
        }
        
        # 模拟数据生成器（用于测试）
        self.simulation_mode = False  # 默认禁用模拟模式
        self.sim_rpm_targets = {}
        
    def start_monitoring(self, simulation=False):
        """开始监控"""
        if self.is_monitoring:
            print("监控已在运行中")
            return
            
        self.is_monitoring = True
        self.simulation_mode = simulation
        
        # 重置统计信息
        self.error_count = 0
        self.last_successful_read = time.time()
        self.stats['error_count'] = 0
        self.stats['connection_status'] = 'starting'
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"Tach信号监控已启动 - 模式: {'模拟' if simulation else '实际'}")
            
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("Tach信号监控已停止")
        
    def _monitor_loop(self):
        """监控主循环"""
        print(f"开始监控循环 - 模式: {'模拟' if self.simulation_mode else '实际'}")
        consecutive_errors = 0
        
        while self.is_monitoring:
            try:
                # 检查连接状态
                if not self.simulation_mode:
                    self._check_connection_health()
                
                # 执行数据读取
                if self.simulation_mode:
                    self._generate_simulation_data()
                    self.stats['connection_status'] = 'simulated'
                else:
                    self._read_real_data()
                    
                # 重置错误计数
                consecutive_errors = 0
                self.last_successful_read = time.time()
                
                # 动态调整读取间隔
                sleep_interval = self._calculate_optimal_interval()
                time.sleep(sleep_interval)
                
            except KeyboardInterrupt:
                print("接收到中断信号，停止监控")
                break
            except Exception as e:
                consecutive_errors += 1
                self.error_count += 1
                self.stats['error_count'] = self.error_count
                self.last_error_time = time.time()
                
                print(f"监控循环异常 (第{consecutive_errors}次): {e}")
                
                # 检查是否超过最大连续错误数
                if consecutive_errors >= self.max_consecutive_errors:
                    print(f"连续错误次数超过限制({self.max_consecutive_errors})，保持非模拟模式")
                    # self.simulation_mode = True  # 不自动切换到模拟模式
                    consecutive_errors = 0
                    self.stats['connection_status'] = 'error_fallback'
                
                # 错误恢复延迟
                recovery_delay = min(self.error_recovery_delay * consecutive_errors, 10.0)
                time.sleep(recovery_delay)
                
        print("监控循环已停止")
        
    def _check_connection_health(self):
        """检查连接健康状态"""
        current_time = time.time()
        
        # 检查数据超时
        if current_time - self.last_successful_read > self.data_timeout_threshold:
            self.stats['connection_status'] = 'timeout'
            raise Exception(f"数据读取超时 ({current_time - self.last_successful_read:.1f}s)")
        
        # 检查FCCommunicator状态
        if self.fc_communicator is None:
            self.stats['connection_status'] = 'no_communicator'
            raise Exception("FCCommunicator未初始化")
            
        # 检查FCCommunicator是否仍然活跃
        if hasattr(self.fc_communicator, 'stopped') and self.fc_communicator.stopped.is_set():
            self.stats['connection_status'] = 'communicator_stopped'
            raise Exception("FCCommunicator已停止")
            
        self.stats['connection_status'] = 'connected'
        
    def _calculate_optimal_interval(self):
        """计算最优读取间隔"""
        base_interval = 0.1  # 基础间隔100ms
        
        # 根据错误率调整间隔
        if self.error_count > 0:
            error_rate = self.error_count / max(self.stats['total_readings'], 1)
            if error_rate > 0.1:  # 错误率超过10%
                base_interval *= 2  # 降低读取频率
        
        # 根据数据量调整间隔
        if len(self.signal_data) > 8000:  # 缓冲区接近满时
            base_interval *= 1.5  # 降低频率
            
        # 自适应间隔调整
        if self.adaptive_interval and len(self.signal_data) >= 10:
            recent_data = list(self.signal_data)[-10:]
            # 计算RPM变化率
            rpm_changes = []
            for i in range(1, len(recent_data)):
                rpm_change = abs(recent_data[i].rpm - recent_data[i-1].rpm)
                rpm_changes.append(rpm_change)
            
            if rpm_changes:
                avg_change = np.mean(rpm_changes)
                # 如果变化率高，减少间隔提高响应性
                if avg_change > 100:  # RPM变化超过100
                    base_interval *= 0.7
                elif avg_change < 10:  # RPM变化很小
                    base_interval *= 1.2
        
        # 应用间隔范围限制
        return max(self.min_interval, min(self.max_interval, base_interval))
                
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
                
                # 更新风机优先级
                self._update_fan_priority(data_point)
                
    def _read_real_data(self):
        """读取真实数据（与FC系统集成）"""
        read_start_time = time.time()
        
        try:
            # 检查缓存
            if self._can_use_cached_data():
                self._use_cached_data()
                return
            
            # 尝试从FCCommunicator获取实际RPM数据
            if self.fc_communicator is not None and hasattr(self.fc_communicator, 'get_rpm_data'):
                rpm_data = self.fc_communicator.get_rpm_data()
                
                # 记录读取时间
                read_time = time.time() - read_start_time
                self.performance_stats['read_times'].append(read_time)
                
                if rpm_data and len(rpm_data) > 0:
                    # 处理获取到的RPM数据
                    process_start_time = time.time()
                    self._process_real_rpm_data(rpm_data, read_start_time)
                    
                    # 记录处理时间
                    process_time = time.time() - process_start_time
                    self.performance_stats['process_times'].append(process_time)
                    
                    # 更新缓存
                    self._update_data_cache(rpm_data, read_start_time)
                    
                    # 更新性能统计
                    self._update_performance_stats()
                    
                else:
                    # 如果没有数据，记录警告但不抛出异常
                    self._handle_no_data_warning()
                        
            else:
                # FCCommunicator不可用，使用模拟数据作为后备
                self._handle_fallback_to_simulation()
                
        except Exception as e:
            # 记录异常但继续运行
            print(f"读取实际数据时发生异常: {e}")
            # 使用模拟数据作为后备
            self._generate_simulation_data()
            
    def _can_use_cached_data(self):
        """检查是否可以使用缓存数据"""
        if not self.data_cache:
            return False
            
        current_time = time.time()
        cache_age = current_time - self.data_cache.get('timestamp', 0)
        
        return cache_age < self.cache_timeout
        
    def _use_cached_data(self):
        """使用缓存数据"""
        if 'rpm_data' in self.data_cache:
            current_time = time.time()
            # 使用缓存的RPM数据，但更新时间戳
            self._process_real_rpm_data(self.data_cache['rpm_data'], current_time)
            
    def _update_data_cache(self, rpm_data, timestamp):
        """更新数据缓存"""
        self.data_cache = {
            'rpm_data': rpm_data.copy() if hasattr(rpm_data, 'copy') else list(rpm_data),
            'timestamp': timestamp
        }
        
    def _handle_no_data_warning(self):
        """处理无数据警告"""
        if hasattr(self, '_no_data_warning_count'):
            self._no_data_warning_count += 1
        else:
            self._no_data_warning_count = 1
        
        # 每100次警告只打印一次，避免日志过多
        if self._no_data_warning_count % 100 == 1:
            print(f"警告: FCCommunicator未返回RPM数据 (第{self._no_data_warning_count}次)")
            
    def _handle_fallback_to_simulation(self):
        """处理回退到模拟模式"""
        if not hasattr(self, '_fallback_warning_shown'):
            print("警告: FCCommunicator不可用，使用模拟数据作为后备")
            self._fallback_warning_shown = True
        self._generate_simulation_data()
        
    def _update_performance_stats(self):
        """更新性能统计"""
        if self.performance_stats['read_times']:
            avg_read_time = np.mean(list(self.performance_stats['read_times']))
            self.stats['performance']['avg_read_time'] = round(avg_read_time * 1000, 2)  # 转换为毫秒
            
        if self.performance_stats['process_times']:
            avg_process_time = np.mean(list(self.performance_stats['process_times']))
            self.stats['performance']['avg_process_time'] = round(avg_process_time * 1000, 2)  # 转换为毫秒
            
        # 计算数据率（每秒处理的数据点数）
        current_time = time.time()
        recent_data = [data for data in self.signal_data if current_time - data.timestamp <= 1.0]
        data_rate = len(recent_data)
        self.performance_stats['data_rates'].append(data_rate)
        self.stats['performance']['data_rate'] = data_rate
            
    def _process_real_rpm_data(self, rpm_data, current_time):
        """处理从FCCommunicator获取的实际RPM数据"""
        try:
            # 数据验证
            if not self._validate_rpm_data(rpm_data):
                raise ValueError("RPM数据验证失败")
            
            # 处理不同格式的RPM数据
            processed_count = 0
            
            if isinstance(rpm_data, dict):
                # 处理字典格式的RPM数据（如测试中的格式）
                for fan_key, rpm_value in rpm_data.items():
                    # 从fan_key解析slave_id和fan_id
                    if isinstance(fan_key, str) and fan_key.startswith('fan_'):
                        fan_index = int(fan_key.split('_')[1]) - 1  # fan_1 -> 0
                    else:
                        fan_index = processed_count
                    
                    # 计算slave_id和fan_id
                    slave_id = fan_index // self.max_fans_per_slave
                    fan_id = fan_index % self.max_fans_per_slave
                    
                    # 确保不超过最大slave数量
                    if slave_id >= self.max_slaves:
                        break
                        
                    # 验证单个RPM值
                    validated_rpm = self._validate_single_rpm(rpm_value, slave_id, fan_id)
                    if validated_rpm is None:
                        continue
                        
                    # 计算占空比（基于RPM值的估算）
                    duty_cycle = self._calculate_duty_cycle(validated_rpm)
                    
                    # 计算信号质量（基于RPM稳定性）
                    signal_quality = self._calculate_signal_quality(slave_id, fan_id, validated_rpm)
                    
                    # 创建数据点
                    data_point = TachSignalData(
                        timestamp=current_time,
                        slave_id=slave_id,
                        fan_id=fan_id,
                        rpm=validated_rpm,
                        duty_cycle=duty_cycle,
                        signal_quality=signal_quality,
                        data_index=self.stats['total_readings']
                    )
                    
                    # 添加到数据集合
                    self.signal_data.append(data_point)
                    self._update_stats(data_point)
                    processed_count += 1
                    
            elif isinstance(rpm_data, (list, tuple)):
                # 处理列表格式的RPM数据
                for fan_index, rpm_value in enumerate(rpm_data):
                    # 计算slave_id和fan_id
                    slave_id = fan_index // self.max_fans_per_slave
                    fan_id = fan_index % self.max_fans_per_slave
                    
                    # 确保不超过最大slave数量
                    if slave_id >= self.max_slaves:
                        break
                        
                    # 验证单个RPM值
                    validated_rpm = self._validate_single_rpm(rpm_value, slave_id, fan_id)
                    if validated_rpm is None:
                        continue
                        
                    # 计算占空比（基于RPM值的估算）
                    duty_cycle = self._calculate_duty_cycle(validated_rpm)
                    
                    # 计算信号质量（基于RPM稳定性）
                    signal_quality = self._calculate_signal_quality(slave_id, fan_id, validated_rpm)
                    
                    # 创建数据点
                    data_point = TachSignalData(
                        timestamp=current_time,
                        slave_id=slave_id,
                        fan_id=fan_id,
                        rpm=validated_rpm,
                        duty_cycle=duty_cycle,
                        signal_quality=signal_quality,
                        data_index=self.stats['total_readings']
                    )
                    
                    # 添加到数据集合
                    self.signal_data.append(data_point)
                    self._update_stats(data_point)
                    processed_count += 1
                     
            else:
                raise ValueError(f"不支持的RPM数据格式: {type(rpm_data)}")
                
            if processed_count == 0:
                raise ValueError("没有有效的RPM数据被处理")
                
        except Exception as e:
             print(f"处理实际RPM数据时发生异常: {e}")
             # 增加错误计数
             self.error_count += 1
             self.stats['error_count'] = self.error_count
             raise
            
    def _validate_rpm_data(self, rpm_data):
        """验证RPM数据的整体有效性"""
        if not rpm_data:
            return False
            
        if not isinstance(rpm_data, (list, tuple, dict)):
            return False
            
        if len(rpm_data) == 0:
            return False
            
        # 检查数据长度是否合理
        expected_max_fans = self.max_slaves * self.max_fans_per_slave
        if len(rpm_data) > expected_max_fans:
            print(f"警告: RPM数据长度({len(rpm_data)})超过预期({expected_max_fans})")
            
        return True
        
    def _validate_single_rpm(self, rpm_value, slave_id, fan_id):
        """验证单个RPM值"""
        # 类型检查
        if not isinstance(rpm_value, (int, float)):
            return None
            
        # 范围检查
        if rpm_value < 0 or rpm_value > 20000:
            return None
            
        # 转换为整数
        rpm_int = int(rpm_value)
        
        # 异常值检测
        if self._is_rpm_outlier(rpm_int, slave_id, fan_id):
            print(f"检测到异常RPM值: S{slave_id}F{fan_id} = {rpm_int}")
            # 可以选择过滤异常值或使用平滑处理
            return self._smooth_rpm_value(rpm_int, slave_id, fan_id)
            
        return rpm_int
        
    def _is_rpm_outlier(self, rpm_value, slave_id, fan_id):
        """检测RPM值是否为异常值"""
        # 获取该风机的历史数据
        recent_data = [data for data in list(self.signal_data)[-20:] 
                      if data.slave_id == slave_id and data.fan_id == fan_id]
        
        if len(recent_data) < 3:
            return False  # 数据不足，不判断为异常
            
        # 计算历史平均值和标准差
        recent_rpms = [data.rpm for data in recent_data]
        mean_rpm = np.mean(recent_rpms)
        std_rpm = np.std(recent_rpms)
        
        # 使用3-sigma规则检测异常值
        if std_rpm > 0:
            z_score = abs(rpm_value - mean_rpm) / std_rpm
            return z_score > 3.0
            
        return False
        
    def _smooth_rpm_value(self, rpm_value, slave_id, fan_id):
        """对异常RPM值进行平滑处理"""
        # 获取该风机的最近几个有效数据点
        recent_data = [data for data in list(self.signal_data)[-5:] 
                      if data.slave_id == slave_id and data.fan_id == fan_id]
        
        if len(recent_data) >= 2:
            # 使用移动平均
            recent_rpms = [data.rpm for data in recent_data]
            smoothed_rpm = int(np.mean(recent_rpms))
            print(f"RPM值平滑处理: {rpm_value} -> {smoothed_rpm}")
            return smoothed_rpm
            
        return rpm_value
        
    def _calculate_duty_cycle(self, rpm_value):
        """计算占空比"""
        if rpm_value <= 0:
            return 0.0
            
        # 基于典型风机特性曲线计算占空比
        # 这里使用简化的线性模型，实际应用中可能需要更复杂的模型
        max_rpm = 12000  # 假设最大RPM
        duty_cycle = min(1.0, rpm_value / max_rpm)
        
        # 考虑风机启动特性
        if rpm_value < 500:  # 低转速时可能需要更高的占空比
            duty_cycle = max(duty_cycle, 0.3)
            
        return round(duty_cycle, 3)
        
    def _is_data_point_valid(self, data_point):
        """检查数据点是否有效"""
        # 基本有效性检查
        if data_point.rpm < 0 or data_point.rpm > 20000:
            return False
            
        if data_point.duty_cycle < 0 or data_point.duty_cycle > 1.0:
            return False
            
        if data_point.signal_quality < 0 or data_point.signal_quality > 1.0:
            return False
            
        # 时间戳检查
        current_time = time.time()
        if abs(data_point.timestamp - current_time) > 10:  # 时间戳不能偏差超过10秒
            return False
            
        return True
            
    def _calculate_signal_quality(self, slave_id, fan_id, current_rpm):
        """计算信号质量（基于RPM稳定性和历史数据）"""
        try:
            # 获取历史RPM数据
            recent_data = [data for data in list(self.signal_data)[-10:] 
                          if data.slave_id == slave_id and data.fan_id == fan_id]
            
            if len(recent_data) < 2:
                # 数据不足，返回默认质量
                return 0.9
                
            # 计算RPM变化的标准差
            recent_rpms = [data.rpm for data in recent_data]
            rpm_std = np.std(recent_rpms) if len(recent_rpms) > 1 else 0
            
            # 基于标准差计算信号质量
            # 标准差越小，信号质量越高
            if rpm_std <= 50:
                quality = 1.0
            elif rpm_std <= 100:
                quality = 0.9
            elif rpm_std <= 200:
                quality = 0.8
            elif rpm_std <= 500:
                quality = 0.7
            else:
                quality = 0.6
                
            # 考虑RPM值的合理性
            if current_rpm == 0:
                quality *= 0.5  # 零转速可能表示问题
            elif current_rpm > 12000:
                quality *= 0.8  # 过高转速可能不稳定
                
            return max(0.1, min(1.0, quality))
            
        except Exception:
            # 计算失败时返回默认值
            return 0.8
        
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
        
    def _update_fan_priority(self, data_point: TachSignalData):
        """更新风机优先级分数"""
        fan_key = f"S{data_point.slave_id}F{data_point.fan_id}"
        
        if fan_key not in self.fan_priority_scores:
            self.fan_priority_scores[fan_key] = {
                'recent_rpms': deque(maxlen=10),
                'error_count': 0,
                'priority_score': 0.0
            }
        
        fan_stats = self.fan_priority_scores[fan_key]
        fan_stats['recent_rpms'].append(data_point.rpm)
        
        # 计算优先级分数
        if len(fan_stats['recent_rpms']) >= 3:
            rpms = list(fan_stats['recent_rpms'])
            variance = np.var(rpms)
            avg_rpm = np.mean(rpms)
            
            # 基于方差和RPM异常程度计算分数
            score = variance / 1000.0  # 归一化方差
            
            # 异常RPM范围加分
            if avg_rpm > 3000 or avg_rpm < 500:
                score += 2.0
            
            # 信号质量差加分
            if data_point.signal_quality < 0.7:
                score += 1.0
                
            fan_stats['priority_score'] = score
            
            # 更新优先风机集合
            self._update_priority_fans()
    
    def _update_priority_fans(self):
        """更新优先监控的风机集合"""
        # 按优先级分数排序，选择前5个
        sorted_fans = sorted(
            self.fan_priority_scores.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        self.priority_fans = set(fan_key for fan_key, _ in sorted_fans[:5])
    
    def _should_prioritize_fan(self, slave_id, fan_id):
        """判断是否应该优先处理某个风机的数据"""
        fan_key = f"S{slave_id}F{fan_id}"
        return fan_key in self.priority_fans
        
    def get_current_stats(self) -> Dict:
        """获取当前统计信息"""
        stats_summary = {
            'total_readings': self.stats['total_readings'],
            'active_slaves': self.stats['active_slaves'],
            'active_fans': self.stats['active_fans'],
            'error_count': self.stats['error_count'],
            'connection_status': self.stats['connection_status'],
            'performance': self.stats['performance'],
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
        monitor.start_monitoring(simulation=False)
        
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
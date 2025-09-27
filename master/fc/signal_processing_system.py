#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号采集与滤波系统集成模块
整合信号采集、数字滤波、质量监测和数据存储功能
"""

import numpy as np
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import queue
import logging
import sys
import os

# 添加backend模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

try:
    from backend.signal_acquisition import (
        AcquisitionConfig, SignalAcquisitionEngine, 
        MultiChannelSynchronizer, AcquisitionManager
    )
    from backend.digital_filtering import (
        FilterType, FilterConfig, FilterFactory,
        RealTimeFilterProcessor
    )
    from backend.data_storage import (
        DataFormat, StorageConfig, DataMetadata,
        DataStorageManager
    )
    from backend.signal_quality_monitor import (
        QualityLevel, QualityMetrics, AnomalyEvent,
        QualityMonitor
    )
except ImportError as e:
    print(f"警告: 无法导入某些模块: {e}")
    print("系统将使用模拟实现")
    
    # 定义模拟类以防导入失败
    class DataFormat:
        HDF5 = "hdf5"
        CSV = "csv"
        JSON = "json"

class SystemState(Enum):
    """系统状态"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class SystemConfig:
    """系统配置"""
    # 采集配置
    acquisition_config: 'AcquisitionConfig'
    
    # 滤波配置
    filter_configs: List['FilterConfig']
    
    # 存储配置
    storage_config: 'StorageConfig'
    
    # 质量监测配置
    quality_monitoring_enabled: bool = True
    quality_check_interval: float = 1.0  # 秒
    
    # 系统配置
    buffer_size: int = 10000
    processing_threads: int = 2
    auto_save_enabled: bool = True
    auto_save_interval: float = 60.0  # 秒
    
    # 实时处理配置
    real_time_processing: bool = True
    processing_chunk_size: int = 1024

class SignalProcessingSystem:
    """信号处理系统主类"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.state = SystemState.IDLE
        
        # 初始化打印队列
        self.pqueue = queue.Queue()
        
        # 初始化日志
        self.setup_logging()
        
        # 初始化组件
        self.acquisition_manager = None
        self.filter_processor = None
        self.storage_manager = None
        self.quality_monitor = None
        
        # 数据缓冲区
        self.raw_data_buffer = queue.Queue(maxsize=self.config.buffer_size)
        self.filtered_data_buffer = queue.Queue(maxsize=self.config.buffer_size)
        
        # 线程管理
        self.processing_threads = []
        self.monitoring_thread = None
        self.auto_save_thread = None
        
        # 事件回调
        self.event_callbacks = {
            'data_acquired': [],
            'data_filtered': [],
            'quality_updated': [],
            'anomaly_detected': [],
            'data_saved': [],
            'error_occurred': []
        }
        
        # 统计信息
        self.statistics = {
            'total_samples_acquired': 0,
            'total_samples_processed': 0,
            'total_files_saved': 0,
            'total_anomalies_detected': 0,
            'system_start_time': None,
            'last_quality_check': None
        }
        
        # 控制标志
        self.running = False
        self.paused = False
        
        self.logger.info("信号处理系统初始化完成")
    
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('signal_processing_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SignalProcessingSystem')
    
    def initialize_components(self) -> bool:
        """初始化系统组件"""
        try:
            self.state = SystemState.INITIALIZING
            self.logger.info("开始初始化系统组件")
            
            # 初始化采集管理器
            self.acquisition_manager = AcquisitionManager(self.pqueue)
            self.logger.info("信号采集管理器初始化完成")
            
            # 初始化滤波处理器
            if self.config.filter_configs:
                self.filter_processor = RealTimeFilterProcessor(self.pqueue)
                
                # 添加滤波器
                for i, filter_config in enumerate(self.config.filter_configs):
                    # 为每个滤波器分配一个通道ID
                    channel_id = i
                    self.filter_processor.add_filter(channel_id, filter_config)
                
                self.logger.info(f"数字滤波处理器初始化完成，加载了 {len(self.config.filter_configs)} 个滤波器")
            
            # 初始化存储管理器
            self.storage_manager = DataStorageManager(self.config.storage_config)
            self.logger.info("数据存储管理器初始化完成")
            
            # 初始化质量监测器
            if self.config.quality_monitoring_enabled:
                self.quality_monitor = QualityMonitor(
                    self.config.acquisition_config.sample_rate
                )
                self.logger.info("信号质量监测器初始化完成")
            
            self.state = SystemState.IDLE
            self.logger.info("所有系统组件初始化完成")
            return True
            
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.error(f"组件初始化失败: {e}")
            self._trigger_event('error_occurred', {'error': str(e), 'component': 'initialization'})
            return False
    
    def start_system(self) -> bool:
        """启动系统"""
        try:
            if self.state != SystemState.IDLE:
                self.logger.warning(f"系统状态不正确，当前状态: {self.state}")
                return False
            
            self.logger.info("启动信号处理系统")
            self.state = SystemState.RUNNING
            self.running = True
            self.paused = False
            
            # 记录启动时间
            self.statistics['system_start_time'] = datetime.now()
            
            # 启动采集
            if not self.acquisition_manager.start_all():
                raise Exception("信号采集启动失败")
            
            # 启动处理线程
            self.start_processing_threads()
            
            # 启动监测线程
            if self.config.quality_monitoring_enabled:
                self.start_monitoring_thread()
            
            # 启动自动保存线程
            if self.config.auto_save_enabled:
                self.start_auto_save_thread()
            
            self.logger.info("信号处理系统启动成功")
            return True
            
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.error(f"系统启动失败: {e}")
            self._trigger_event('error_occurred', {'error': str(e), 'component': 'system_start'})
            return False
    
    def stop_system(self):
        """停止系统"""
        try:
            self.logger.info("停止信号处理系统")
            self.state = SystemState.STOPPING
            self.running = False
            
            # 停止采集
            if self.acquisition_manager:
                self.acquisition_manager.stop_acquisition()
            
            # 等待处理线程结束
            for thread in self.processing_threads:
                if thread.is_alive():
                    thread.join(timeout=5.0)
            
            # 停止监测线程
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            # 停止自动保存线程
            if self.auto_save_thread and self.auto_save_thread.is_alive():
                self.auto_save_thread.join(timeout=5.0)
            
            # 保存剩余数据
            self.save_remaining_data()
            
            self.state = SystemState.IDLE
            self.logger.info("信号处理系统已停止")
            
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.error(f"系统停止时发生错误: {e}")
    
    def pause_system(self):
        """暂停系统"""
        if self.state == SystemState.RUNNING:
            self.paused = True
            self.state = SystemState.PAUSED
            self.logger.info("系统已暂停")
    
    def resume_system(self):
        """恢复系统"""
        if self.state == SystemState.PAUSED:
            self.paused = False
            self.state = SystemState.RUNNING
            self.logger.info("系统已恢复")
    
    def start_processing_threads(self):
        """启动处理线程"""
        # 数据处理线程
        for i in range(self.config.processing_threads):
            thread = threading.Thread(
                target=self.data_processing_loop,
                name=f"DataProcessor-{i}",
                daemon=True
            )
            thread.start()
            self.processing_threads.append(thread)
        
        # 数据采集线程
        acquisition_thread = threading.Thread(
            target=self.data_acquisition_loop,
            name="DataAcquisition",
            daemon=True
        )
        acquisition_thread.start()
        self.processing_threads.append(acquisition_thread)
    
    def start_monitoring_thread(self):
        """启动监测线程"""
        self.monitoring_thread = threading.Thread(
            target=self.quality_monitoring_loop,
            name="QualityMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
    
    def start_auto_save_thread(self):
        """启动自动保存线程"""
        self.auto_save_thread = threading.Thread(
            target=self.auto_save_loop,
            name="AutoSave",
            daemon=True
        )
        self.auto_save_thread.start()
    
    def data_acquisition_loop(self):
        """数据采集循环"""
        self.logger.info("数据采集线程启动")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # 获取数据
                data = self.acquisition_manager.get_latest_data()
                if data is not None and len(data) > 0:
                    # 添加到缓冲区
                    try:
                        self.raw_data_buffer.put(data, timeout=0.1)
                        self.statistics['total_samples_acquired'] += len(data)
                        
                        # 触发数据采集事件
                        self._trigger_event('data_acquired', {
                            'data_shape': data.shape,
                            'timestamp': datetime.now()
                        })
                        
                    except queue.Full:
                        self.logger.warning("原始数据缓冲区已满，丢弃数据")
                
                time.sleep(0.001)  # 1ms延迟
                
            except Exception as e:
                self.logger.error(f"数据采集循环错误: {e}")
                self._trigger_event('error_occurred', {'error': str(e), 'component': 'data_acquisition'})
        
        self.logger.info("数据采集线程结束")
    
    def data_processing_loop(self):
        """数据处理循环"""
        thread_name = threading.current_thread().name
        self.logger.info(f"数据处理线程 {thread_name} 启动")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # 从缓冲区获取数据
                try:
                    raw_data = self.raw_data_buffer.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 应用滤波器
                filtered_data = raw_data.copy()
                if self.filter_processor and self.config.real_time_processing:
                    try:
                        filtered_data = self.filter_processor.process_chunk(raw_data)
                        
                        # 触发滤波事件
                        self._trigger_event('data_filtered', {
                            'original_shape': raw_data.shape,
                            'filtered_shape': filtered_data.shape,
                            'timestamp': datetime.now()
                        })
                        
                    except Exception as e:
                        self.logger.error(f"滤波处理错误: {e}")
                        filtered_data = raw_data  # 使用原始数据
                
                # 添加到滤波数据缓冲区
                try:
                    self.filtered_data_buffer.put(filtered_data, timeout=0.1)
                    self.statistics['total_samples_processed'] += len(filtered_data)
                except queue.Full:
                    self.logger.warning("滤波数据缓冲区已满，丢弃数据")
                
                # 标记任务完成
                self.raw_data_buffer.task_done()
                
            except Exception as e:
                self.logger.error(f"数据处理循环错误 ({thread_name}): {e}")
                self._trigger_event('error_occurred', {'error': str(e), 'component': 'data_processing'})
        
        self.logger.info(f"数据处理线程 {thread_name} 结束")
    
    def quality_monitoring_loop(self):
        """质量监测循环"""
        self.logger.info("质量监测线程启动")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(1.0)
                    continue
                
                # 收集一段时间的数据进行质量分析
                data_for_analysis = []
                start_time = time.time()
                
                while (time.time() - start_time) < self.config.quality_check_interval and self.running:
                    try:
                        data = self.filtered_data_buffer.get(timeout=0.1)
                        data_for_analysis.append(data)
                        self.filtered_data_buffer.task_done()
                    except queue.Empty:
                        continue
                
                if data_for_analysis:
                    # 合并数据
                    combined_data = np.vstack(data_for_analysis)
                    
                    # 分析每个通道的质量
                    for channel_idx in range(combined_data.shape[1]):
                        channel_data = combined_data[:, channel_idx]
                        channel_name = f"Channel_{channel_idx}"
                        
                        # 质量分析
                        metrics = self.quality_monitor.analyze_quality(channel_data, channel_name)
                        if metrics:
                            self.statistics['last_quality_check'] = datetime.now()
                            
                            # 触发质量更新事件
                            self._trigger_event('quality_updated', {
                                'channel': channel_name,
                                'metrics': metrics
                            })
                        
                        # 异常检测
                        anomalies = self.quality_monitor.detect_anomalies(channel_data, channel_name)
                        if anomalies:
                            self.statistics['total_anomalies_detected'] += len(anomalies)
                            
                            # 触发异常检测事件
                            for anomaly in anomalies:
                                self._trigger_event('anomaly_detected', {
                                    'channel': channel_name,
                                    'anomaly': anomaly
                                })
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"质量监测循环错误: {e}")
                self._trigger_event('error_occurred', {'error': str(e), 'component': 'quality_monitoring'})
        
        self.logger.info("质量监测线程结束")
    
    def auto_save_loop(self):
        """自动保存循环"""
        self.logger.info("自动保存线程启动")
        last_save_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                if (current_time - last_save_time) >= self.config.auto_save_interval:
                    self.save_buffered_data()
                    last_save_time = current_time
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"自动保存循环错误: {e}")
                self._trigger_event('error_occurred', {'error': str(e), 'component': 'auto_save'})
        
        self.logger.info("自动保存线程结束")
    
    def save_buffered_data(self):
        """保存缓冲区数据"""
        try:
            # 收集缓冲区中的所有数据
            data_to_save = []
            
            while not self.filtered_data_buffer.empty():
                try:
                    data = self.filtered_data_buffer.get_nowait()
                    data_to_save.append(data)
                    self.filtered_data_buffer.task_done()
                except queue.Empty:
                    break
            
            if data_to_save:
                # 合并数据
                combined_data = np.vstack(data_to_save)
                
                # 创建元数据
                metadata = DataMetadata(
                    data_type="filtered_signal",
                    channels=[f"Channel_{i}" for i in range(combined_data.shape[1])],
                    sample_rate=self.config.acquisition_config.sample_rate,
                    duration=len(combined_data) / self.config.acquisition_config.sample_rate
                )
                
                # 保存数据
                filename = f"signal_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                saved_path = self.storage_manager.save_data(
                    combined_data, metadata, filename, DataFormat.HDF5
                )
                
                if saved_path:
                    self.statistics['total_files_saved'] += 1
                    self.logger.info(f"自动保存数据到: {saved_path}")
                    
                    # 触发保存事件
                    self._trigger_event('data_saved', {
                        'filepath': saved_path,
                        'data_shape': combined_data.shape,
                        'timestamp': datetime.now()
                    })
        
        except Exception as e:
            self.logger.error(f"保存缓冲区数据失败: {e}")
    
    def save_remaining_data(self):
        """保存剩余数据"""
        self.logger.info("保存剩余数据")
        self.save_buffered_data()
    
    def manual_save_data(self, filename: str, format_type: DataFormat = DataFormat.HDF5) -> Optional[str]:
        """手动保存数据"""
        try:
            # 收集当前缓冲区数据
            data_to_save = []
            temp_buffer = []
            
            # 从缓冲区取出数据，但保留副本
            while not self.filtered_data_buffer.empty():
                try:
                    data = self.filtered_data_buffer.get_nowait()
                    data_to_save.append(data)
                    temp_buffer.append(data)
                    self.filtered_data_buffer.task_done()
                except queue.Empty:
                    break
            
            # 将数据放回缓冲区
            for data in temp_buffer:
                try:
                    self.filtered_data_buffer.put_nowait(data)
                except queue.Full:
                    break
            
            if data_to_save:
                combined_data = np.vstack(data_to_save)
                
                metadata = DataMetadata(
                    data_type="manual_save",
                    channels=[f"Channel_{i}" for i in range(combined_data.shape[1])],
                    sample_rate=self.config.acquisition_config.sample_rate,
                    duration=len(combined_data) / self.config.acquisition_config.sample_rate
                )
                
                saved_path = self.storage_manager.save_data(
                    combined_data, metadata, filename, format_type
                )
                
                if saved_path:
                    self.statistics['total_files_saved'] += 1
                    self.logger.info(f"手动保存数据到: {saved_path}")
                    
                    self._trigger_event('data_saved', {
                        'filepath': saved_path,
                        'data_shape': combined_data.shape,
                        'timestamp': datetime.now(),
                        'manual': True
                    })
                
                return saved_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"手动保存数据失败: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'state': self.state.value,
            'running': self.running,
            'paused': self.paused,
            'statistics': self.statistics.copy(),
            'buffer_status': {
                'raw_data_buffer_size': self.raw_data_buffer.qsize(),
                'filtered_data_buffer_size': self.filtered_data_buffer.qsize(),
                'raw_data_buffer_full': self.raw_data_buffer.full(),
                'filtered_data_buffer_full': self.filtered_data_buffer.full()
            },
            'thread_status': {
                'processing_threads': len([t for t in self.processing_threads if t.is_alive()]),
                'monitoring_thread_alive': self.monitoring_thread.is_alive() if self.monitoring_thread else False,
                'auto_save_thread_alive': self.auto_save_thread.is_alive() if self.auto_save_thread else False
            }
        }
        
        # 添加运行时间
        if self.statistics['system_start_time']:
            runtime = datetime.now() - self.statistics['system_start_time']
            status['runtime_seconds'] = runtime.total_seconds()
        
        return status
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """获取质量摘要"""
        if self.quality_monitor:
            return self.quality_monitor.get_quality_summary(timedelta(minutes=10))
        return {}
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """移除事件回调"""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败 ({event_type}): {e}")

# 使用示例
if __name__ == "__main__":
    try:
        # 创建配置
        acquisition_config = AcquisitionConfig()
        acquisition_config.sample_rate = 1000.0
        acquisition_config.channels = ["Channel_1", "Channel_2"]
        acquisition_config.buffer_size = 10000
        
        filter_config = FilterConfig()
        filter_config.filter_type = FilterType.IIR_BUTTERWORTH
        filter_config.cutoff_freq = 100.0
        filter_config.sample_rate = 1000.0
        filter_config.order = 4
        
        storage_config = StorageConfig()
        storage_config.base_path = "./signal_data"
        
        system_config = SystemConfig(
            acquisition_config=acquisition_config,
            filter_configs=[filter_config],
            storage_config=storage_config,
            quality_monitoring_enabled=True,
            auto_save_enabled=True,
            auto_save_interval=30.0
        )
        
        # 创建系统
        system = SignalProcessingSystem(system_config)
        
        # 添加事件回调
        def on_data_acquired(data):
            print(f"数据采集: {data['data_shape']}")
        
        def on_quality_updated(data):
            metrics = data['metrics']
            print(f"质量更新 - {data['channel']}: 分数={metrics.quality_score:.1f}, 等级={metrics.quality_level.value}")
        
        def on_anomaly_detected(data):
            anomaly = data['anomaly']
            print(f"异常检测 - {data['channel']}: {anomaly.anomaly_type.value}, 严重程度={anomaly.severity:.2f}")
        
        system.add_event_callback('data_acquired', on_data_acquired)
        system.add_event_callback('quality_updated', on_quality_updated)
        system.add_event_callback('anomaly_detected', on_anomaly_detected)
        
        # 初始化并启动系统
        if system.initialize_components():
            print("系统组件初始化成功")
            
            if system.start_system():
                print("系统启动成功")
                
                # 运行一段时间
                try:
                    time.sleep(60)  # 运行1分钟
                except KeyboardInterrupt:
                    print("\n接收到中断信号")
                
                # 获取系统状态
                status = system.get_system_status()
                print(f"\n系统状态: {status}")
                
                # 手动保存数据
                saved_path = system.manual_save_data("manual_test")
                if saved_path:
                    print(f"手动保存成功: {saved_path}")
                
                # 停止系统
                system.stop_system()
                print("系统已停止")
            else:
                print("系统启动失败")
        else:
            print("系统组件初始化失败")
    
    except Exception as e:
        print(f"系统运行错误: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/python3
################################################################################
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Signal Acquisition Module for Fan Club System                             ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + 信号采集模块：支持多通道数据同步采集，可配置采样率和分辨率
 + 提供硬件接口适配层，确保数据采集的实时性和准确性
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import threading
import time
import queue
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from fc import printer as pt

## CONFIGURATION ###############################################################
@dataclass
class AcquisitionConfig:
    """信号采集配置参数"""
    sampling_rate: float = 1000.0  # 采样率 (Hz)
    resolution: int = 16           # 分辨率 (bits)
    buffer_size: int = 1024        # 缓冲区大小
    channels: List[int] = None     # 通道列表
    sync_mode: bool = True         # 同步采集模式
    trigger_mode: str = 'continuous'  # 触发模式: 'continuous', 'external', 'software'
    hardware_type: str = 'simulated'  # 硬件类型: 'simulated', 'real', 'auto'
    prefer_real_hardware: bool = False  # 是否优先使用真实硬件
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [0, 1, 2, 3]  # 默认4通道
        
        # 验证配置参数
        if self.sampling_rate <= 0:
            raise ValueError("采样率必须大于0")
        if self.sampling_rate > 100000:  # 100kHz限制
            raise ValueError("采样率不能超过100kHz")
        
        if self.resolution not in [8, 12, 16, 24]:
            raise ValueError("分辨率必须是8, 12, 16或24位")
        
        if self.buffer_size <= 0 or self.buffer_size > 65536:
            raise ValueError("缓冲区大小必须在1-65536之间")
        
        if not self.channels or len(self.channels) > 32:
            raise ValueError("通道数量必须在1-32之间")
        
        if self.trigger_mode not in ['continuous', 'external', 'software']:
            raise ValueError("触发模式必须是continuous, external或software")
        
        if self.hardware_type not in ['simulated', 'real', 'auto']:
            raise ValueError("硬件类型必须是simulated, real或auto")

@dataclass
class ChannelConfig:
    """单通道配置参数"""
    channel_id: int
    enabled: bool = True
    gain: float = 1.0
    offset: float = 0.0
    coupling: str = 'DC'  # 'DC' or 'AC'
    range_min: float = -10.0
    range_max: float = 10.0
    calibration_factor: float = 1.0

@dataclass
class SampleData:
    """采样数据结构"""
    timestamp: float
    channel_id: int
    value: float
    raw_value: int
    quality: float = 1.0  # 信号质量指标 (0-1)

## HARDWARE INTERFACE ##########################################################
class HardwareInterface(ABC):
    """硬件接口抽象基类"""
    
    @abstractmethod
    def initialize(self, config: AcquisitionConfig) -> bool:
        """初始化硬件"""
        pass
    
    @abstractmethod
    def start_acquisition(self) -> bool:
        """开始数据采集"""
        pass
    
    @abstractmethod
    def stop_acquisition(self) -> bool:
        """停止数据采集"""
        pass
    
    @abstractmethod
    def read_samples(self, num_samples: int) -> List[SampleData]:
        """读取采样数据"""
        pass
    
    @abstractmethod
    def configure_channel(self, channel_config: ChannelConfig) -> bool:
        """配置通道参数"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取硬件状态"""
        pass

class SimulatedHardware(HardwareInterface):
    """模拟硬件接口实现"""
    
    def __init__(self):
        self.config = None
        self.channels = {}
        self.is_running = False
        self.sample_counter = 0
        
    def initialize(self, config: AcquisitionConfig) -> bool:
        """初始化模拟硬件"""
        self.config = config
        # 初始化通道配置
        for ch_id in config.channels:
            self.channels[ch_id] = ChannelConfig(ch_id)
        return True
    
    def start_acquisition(self) -> bool:
        """开始模拟数据采集"""
        self.is_running = True
        self.sample_counter = 0
        return True
    
    def stop_acquisition(self) -> bool:
        """停止模拟数据采集"""
        self.is_running = False
        return True
    
    def read_samples(self, num_samples: int) -> List[SampleData]:
        """生成模拟采样数据"""
        if not self.is_running:
            return []
        
        samples = []
        current_time = time.time()
        
        for i in range(num_samples):
            for ch_idx, ch_id in enumerate(self.config.channels):
                if ch_id in self.channels and self.channels[ch_id].enabled:
                    # 生成模拟信号：正弦波 + 噪声
                    t = self.sample_counter / self.config.sampling_rate
                    freq = 10.0 + ch_idx * 5.0  # 不同通道不同频率
                    signal = np.sin(2 * np.pi * freq * t) + 0.1 * np.random.randn()
                    
                    # 应用通道配置
                    ch_config = self.channels[ch_id]
                    signal = signal * ch_config.gain + ch_config.offset
                    
                    # 转换为数字值
                    max_val = 2**(self.config.resolution - 1) - 1
                    raw_value = int(signal * max_val / 10.0)  # 假设±10V量程
                    
                    sample = SampleData(
                        timestamp=current_time + i / self.config.sampling_rate,
                        channel_id=ch_id,
                        value=signal,
                        raw_value=raw_value,
                        quality=0.95 + 0.05 * np.random.rand()  # 模拟信号质量
                    )
                    samples.append(sample)
            
            self.sample_counter += 1
        
        return samples
    
    def configure_channel(self, channel_config: ChannelConfig) -> bool:
        """配置模拟通道"""
        self.channels[channel_config.channel_id] = channel_config
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取模拟硬件状态"""
        return {
            'running': self.is_running,
            'sample_count': self.sample_counter,
            'channels': len(self.channels),
            'sampling_rate': self.config.sampling_rate if self.config else 0
        }

class RealHardware(HardwareInterface):
    """真实硬件接口实现"""
    
    def __init__(self):
        self.config = None
        self.channels = {}
        self.is_running = False
        self.device_handle = None
        self.device_name = "Unknown Device"
        self.connection_status = False
        
    def initialize(self, config: AcquisitionConfig) -> bool:
        """初始化真实硬件"""
        self.config = config
        # 初始化通道配置
        for ch_id in config.channels:
            self.channels[ch_id] = ChannelConfig(ch_id)
        
        # 尝试连接硬件设备
        return self.connect_device()
    
    def start_acquisition(self) -> bool:
        """启动真实硬件采集"""
        if not self.connection_status:
            return False
            
        try:
            # TODO: 实现真实硬件启动逻辑
            # 这里应该调用具体的硬件驱动API
            self.is_running = True
            return True
        except Exception as e:
            return False
    
    def stop_acquisition(self) -> bool:
        """停止真实硬件采集"""
        try:
            # TODO: 实现真实硬件停止逻辑
            self.is_running = False
            return True
        except Exception as e:
            return False
    
    def read_samples(self, num_samples: int) -> List[SampleData]:
        """读取真实硬件采样数据"""
        if not self.is_running or not self.connection_status:
            return []
            
        try:
            # TODO: 实现真实硬件数据读取逻辑
            # 这里应该调用具体的硬件驱动API读取数据
            # 暂时返回空列表作为占位符
            return []
            
        except Exception as e:
            return []
    
    def configure_channel(self, channel_config: ChannelConfig) -> bool:
        """配置真实硬件通道"""
        if not self.connection_status:
            return False
            
        try:
            # TODO: 实现真实硬件通道配置逻辑
            self.channels[channel_config.channel_id] = channel_config
            return True
        except Exception as e:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取真实硬件状态"""
        return {
            'type': 'real',
            'running': self.is_running,
            'connected': self.connection_status,
            'device_name': self.device_name,
            'channels': len(self.channels),
            'sampling_rate': self.config.sampling_rate if self.config else 0,
            'device_handle': self.device_handle is not None
        }
    
    def connect_device(self) -> bool:
        """连接硬件设备"""
        try:
            # TODO: 实现设备连接逻辑
            # 这里应该扫描和连接可用的硬件设备
            
            # 模拟连接失败（因为没有真实硬件）
            self.connection_status = False
            self.device_name = "No Device Found"
            return False
            
        except Exception as e:
            self.connection_status = False
            return False
    
    def disconnect_device(self) -> bool:
        """断开硬件设备"""
        try:
            # TODO: 实现设备断开逻辑
            self.connection_status = False
            self.device_handle = None
            return True
        except Exception as e:
            return False

## SIGNAL ACQUISITION ENGINE ###################################################
class SignalAcquisitionEngine(pt.PrintClient):
    """信号采集引擎"""
    
    SYMBOL = "[SA]"
    
    def __init__(self, pqueue, hardware_interface: HardwareInterface = None):
        """初始化信号采集引擎"""
        pt.PrintClient.__init__(self, pqueue)
        
        self.config = AcquisitionConfig()
        
        # 硬件接口选择
        if hardware_interface:
            self.hardware = hardware_interface
        else:
            # 根据配置选择硬件类型
            self.hardware = self._create_hardware_interface()
        
        # 数据队列和回调 - 限制队列大小防止内存溢出
        self.data_queue = queue.Queue(maxsize=100)  # 减少队列大小
        self.acquisition_thread = None
        self.is_running = False
        self.callbacks = []  # 数据回调函数列表
        self.statistics = {
            'samples_acquired': 0,
            'errors': 0,
            'start_time': None,
            'last_sample_time': None,
            'queue_overflows': 0,  # 队列溢出计数
            'callback_errors': 0   # 回调错误计数
        }
        
    def configure(self, config: AcquisitionConfig) -> bool:
        """配置采集参数"""
        try:
            self.config = config
            success = self.hardware.initialize(config)
            if success:
                self.printr(f"采集配置成功: {len(config.channels)}通道, {config.sampling_rate}Hz")
            else:
                self.printe("采集配置失败")
            return success
        except Exception as e:
            self.printe(f"配置错误: {e}")
            return False
    
    def configure_channel(self, channel_config: ChannelConfig) -> bool:
        """配置单个通道"""
        try:
            success = self.hardware.configure_channel(channel_config)
            if success:
                self.printr(f"通道{channel_config.channel_id}配置成功")
            return success
        except Exception as e:
            self.printe(f"通道配置错误: {e}")
            return False
    
    def start_acquisition(self) -> bool:
        """开始数据采集"""
        if self.is_running:
            self.printr("采集已在运行中")
            return True
        
        try:
            # 启动硬件采集
            if not self.hardware.start_acquisition():
                self.printe("硬件启动失败")
                return False
            
            # 启动采集线程
            self.is_running = True
            self.statistics['start_time'] = time.time()
            self.statistics['samples_acquired'] = 0
            self.statistics['errors'] = 0
            
            self.acquisition_thread = threading.Thread(
                target=self._acquisition_loop,
                daemon=True
            )
            self.acquisition_thread.start()
            
            self.printr("信号采集已启动")
            return True
            
        except Exception as e:
            self.printe(f"启动采集失败: {e}")
            self.is_running = False
            return False
    
    def stop_acquisition(self) -> bool:
        """停止数据采集"""
        if not self.is_running:
            return True
        
        try:
            self.is_running = False
            
            # 等待采集线程结束
            if self.acquisition_thread and self.acquisition_thread.is_alive():
                self.acquisition_thread.join(timeout=2.0)
            
            # 停止硬件采集
            self.hardware.stop_acquisition()
            
            self.printr("信号采集已停止")
            return True
            
        except Exception as e:
            self.printe(f"停止采集失败: {e}")
            return False
    
    def add_data_callback(self, callback: Callable[[List[SampleData]], None]):
        """添加数据回调函数"""
        self.callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable[[List[SampleData]], None]):
        """移除数据回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_data(self, timeout: float = 0.1) -> List[SampleData]:
        """获取采集数据"""
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        stats = self.statistics.copy()
        stats.update(self.hardware.get_status())
        
        if stats['start_time']:
            stats['runtime'] = time.time() - stats['start_time']
            if stats['runtime'] > 0:
                stats['avg_sample_rate'] = stats['samples_acquired'] / stats['runtime']
        
        return stats
    
    def switch_hardware_type(self, hardware_type: str) -> bool:
        """切换硬件类型"""
        if self.is_running:
            self.printr("采集正在运行，无法切换硬件类型")
            return False
        
        try:
            # 更新配置
            old_type = self.config.hardware_type
            self.config.hardware_type = hardware_type
            
            # 断开当前硬件
            if hasattr(self.hardware, 'disconnect_device'):
                self.hardware.disconnect_device()
            
            # 创建新的硬件接口
            new_hardware = self._create_hardware_interface()
            
            if new_hardware:
                self.hardware = new_hardware
                self.printr(f"硬件类型已从 {old_type} 切换到 {hardware_type}")
                return True
            else:
                # 切换失败，恢复原配置
                self.config.hardware_type = old_type
                self.printe(f"切换到 {hardware_type} 失败，保持原硬件类型")
                return False
                
        except Exception as e:
            self.printe(f"切换硬件类型失败: {e}")
            return False
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """获取硬件状态信息"""
        status = self.hardware.get_status()
        status['config_type'] = self.config.hardware_type
        status['prefer_real'] = self.config.prefer_real_hardware
        return status
    
    def _acquisition_loop(self):
        """采集循环线程"""
        self.printr("采集线程启动")
        
        samples_per_read = max(1, int(self.config.sampling_rate * 0.01))  # 10ms批次
        
        while self.is_running:
            try:
                # 读取硬件数据
                samples = self.hardware.read_samples(samples_per_read)
                
                if samples:
                    # 更新统计信息
                    self.statistics['samples_acquired'] += len(samples)
                    self.statistics['last_sample_time'] = time.time()
                    
                    # 将数据放入队列
                    try:
                        self.data_queue.put(samples, timeout=0.001)
                    except queue.Full:
                        self.statistics['queue_overflows'] += 1
                        self.printr("数据队列已满，丢弃数据")
                    
                    # 调用回调函数
                    for callback in self.callbacks:
                        try:
                            callback(samples)
                        except Exception as e:
                            self.statistics['callback_errors'] += 1
                            self.printe(f"回调函数错误: {e}")
                
                # 控制采集频率
                time.sleep(0.001)  # 1ms延迟
                
            except Exception as e:
                self.statistics['errors'] += 1
                self.printe(f"采集循环错误: {e}")
                time.sleep(0.01)  # 错误后稍长延迟
        
        self.printr("采集线程结束")
    
    def _create_hardware_interface(self) -> HardwareInterface:
        """根据配置创建硬件接口"""
        if self.config.hardware_type == 'real' or (self.config.hardware_type == 'auto' and self.config.prefer_real_hardware):
            # 尝试创建真实硬件接口
            real_hw = RealHardware()
            if real_hw.initialize(self.config):
                self.printr("使用真实硬件接口")
                return real_hw
            else:
                self.printr("真实硬件初始化失败，回退到模拟硬件")
        
        # 默认使用模拟硬件
        self.printr("使用模拟硬件接口")
        return SimulatedHardware()

## MULTI-CHANNEL SYNCHRONIZER ##################################################
class MultiChannelSynchronizer:
    """多通道同步器"""
    
    def __init__(self, channels: List[int], sync_tolerance: float = 1e-6):
        """初始化多通道同步器"""
        self.channels = channels
        self.sync_tolerance = sync_tolerance  # 同步容差 (秒)
        self.channel_buffers = {ch: [] for ch in channels}
        self.last_sync_time = 0.0
    
    def add_samples(self, samples: List[SampleData]):
        """添加采样数据"""
        for sample in samples:
            if sample.channel_id in self.channel_buffers:
                self.channel_buffers[sample.channel_id].append(sample)
    
    def get_synchronized_samples(self) -> List[Dict[int, SampleData]]:
        """获取同步的采样数据"""
        synchronized_sets = []
        
        while self._has_complete_set():
            sync_set = {}
            base_time = None
            
            # 找到最早的时间戳作为基准
            for ch in self.channels:
                if self.channel_buffers[ch]:
                    if base_time is None or self.channel_buffers[ch][0].timestamp < base_time:
                        base_time = self.channel_buffers[ch][0].timestamp
            
            # 收集同步时间窗口内的样本
            for ch in self.channels:
                buffer = self.channel_buffers[ch]
                for i, sample in enumerate(buffer):
                    if abs(sample.timestamp - base_time) <= self.sync_tolerance:
                        sync_set[ch] = sample
                        buffer.pop(i)
                        break
            
            if len(sync_set) == len(self.channels):
                synchronized_sets.append(sync_set)
            
            # 清理过期数据
            self._cleanup_old_samples(base_time)
        
        return synchronized_sets
    
    def _has_complete_set(self) -> bool:
        """检查是否有完整的同步数据集"""
        return all(len(self.channel_buffers[ch]) > 0 for ch in self.channels)
    
    def _cleanup_old_samples(self, reference_time: float):
        """清理过期的采样数据"""
        cleanup_threshold = reference_time - 10 * self.sync_tolerance
        
        for ch in self.channels:
            buffer = self.channel_buffers[ch]
            while buffer and buffer[0].timestamp < cleanup_threshold:
                buffer.pop(0)

## ACQUISITION MANAGER #########################################################
class AcquisitionManager(pt.PrintClient):
    """采集管理器 - 统一管理多个采集引擎"""
    
    SYMBOL = "[AM]"
    
    def __init__(self, pqueue):
        """初始化采集管理器"""
        pt.PrintClient.__init__(self, pqueue)
        
        self.engines = {}  # 采集引擎字典
        self.synchronizer = None
        self.global_config = AcquisitionConfig()
        
    def add_engine(self, name: str, engine: SignalAcquisitionEngine):
        """添加采集引擎"""
        self.engines[name] = engine
        self.printr(f"添加采集引擎: {name}")
    
    def remove_engine(self, name: str):
        """移除采集引擎"""
        if name in self.engines:
            self.engines[name].stop_acquisition()
            del self.engines[name]
            self.printr(f"移除采集引擎: {name}")
    
    def configure_global(self, config: AcquisitionConfig):
        """全局配置"""
        self.global_config = config
        
        # 配置同步器
        all_channels = []
        for engine in self.engines.values():
            all_channels.extend(config.channels)
        
        if config.sync_mode and all_channels:
            self.synchronizer = MultiChannelSynchronizer(list(set(all_channels)))
        
        # 配置所有引擎
        for name, engine in self.engines.items():
            success = engine.configure(config)
            if not success:
                self.printe(f"引擎{name}配置失败")
    
    def start_all(self) -> bool:
        """启动所有采集引擎"""
        success = True
        for name, engine in self.engines.items():
            if not engine.start_acquisition():
                self.printe(f"引擎{name}启动失败")
                success = False
        
        if success:
            self.printr("所有采集引擎已启动")
        return success
    
    def stop_all(self) -> bool:
        """停止所有采集引擎"""
        success = True
        for name, engine in self.engines.items():
            if not engine.stop_acquisition():
                self.printe(f"引擎{name}停止失败")
                success = False
        
        if success:
            self.printr("所有采集引擎已停止")
        return success
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        stats = {
            'engines': {},
            'total_samples': 0,
            'total_errors': 0,
            'active_engines': 0
        }
        
        for name, engine in self.engines.items():
            engine_stats = engine.get_statistics()
            stats['engines'][name] = engine_stats
            stats['total_samples'] += engine_stats.get('samples_acquired', 0)
            stats['total_errors'] += engine_stats.get('errors', 0)
            if engine_stats.get('running', False):
                stats['active_engines'] += 1
        
        return stats
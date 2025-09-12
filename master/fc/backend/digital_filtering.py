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
## Digital Filtering Module for Signal Processing                            ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + 数字滤波处理模块：实现多种滤波器（低通/高通/带通/带阻）
 + 支持实时滤波处理，提供滤波参数配置和性能监测
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import numpy as np
import threading
import time
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from fc import printer as pt
from fc.backend.signal_acquisition import SampleData

## FILTER TYPES ################################################################
class FilterType(Enum):
    """滤波器类型枚举"""
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    BANDSTOP = "bandstop"
    NOTCH = "notch"
    MOVING_AVERAGE = "moving_average"
    MEDIAN = "median"
    BUTTERWORTH = "butterworth"
    CHEBYSHEV1 = "chebyshev1"
    CHEBYSHEV2 = "chebyshev2"
    ELLIPTIC = "elliptic"
    BESSEL = "bessel"
    KALMAN = "kalman"
    HUBER_ROBUST = "huber_robust"
    ALPHA_BETA = "alpha_beta"

class FilterMethod(Enum):
    """滤波方法枚举"""
    IIR = "iir"  # 无限冲激响应
    FIR = "fir"  # 有限冲激响应
    ADAPTIVE = "adaptive"  # 自适应滤波
    KALMAN = "kalman"  # 卡尔曼滤波
    ROBUST = "robust"  # 鲁棒滤波
    STATE_SPACE = "state_space"  # 状态空间滤波

## FILTER CONFIGURATION ########################################################
@dataclass
class FilterConfig:
    """滤波器配置参数"""
    filter_type: FilterType = FilterType.LOWPASS
    filter_method: FilterMethod = FilterMethod.IIR
    sampling_rate: float = 1000.0
    cutoff_freq: Union[float, List[float]] = 100.0  # 截止频率
    order: int = 4  # 滤波器阶数
    ripple: float = 0.5  # 纹波 (dB) - 用于Chebyshev滤波器
    attenuation: float = 40.0  # 阻带衰减 (dB)
    window: str = 'hamming'  # 窗函数类型 - 用于FIR滤波器
    enabled: bool = True
    
    # 自适应滤波参数
    adaptation_rate: float = 0.01
    filter_length: int = 32
    
    # 卡尔曼滤波参数
    process_noise: float = 0.01  # 过程噪声方差 Q
    measurement_noise: float = 0.1  # 观测噪声方差 R
    initial_estimate: float = 0.0  # 初始状态估计
    initial_error: float = 1.0  # 初始估计误差方差 P
    
    # Huber鲁棒滤波参数
    huber_threshold: float = 1.345  # Huber阈值参数
    robust_window_size: int = 10  # 鲁棒滤波窗口大小
    
    # α-β滤波参数
    alpha: float = 0.85  # 位置平滑因子
    beta: float = 0.005  # 速度平滑因子
    
    # 实时处理参数
    buffer_size: int = 1024
    overlap: float = 0.5  # 重叠比例
    
    def __post_init__(self):
        # 确保截止频率格式正确
        if isinstance(self.cutoff_freq, (int, float)):
            if self.filter_type in [FilterType.BANDPASS, FilterType.BANDSTOP]:
                # 带通和带阻滤波器需要两个频率
                self.cutoff_freq = [self.cutoff_freq * 0.8, self.cutoff_freq * 1.2]
            else:
                self.cutoff_freq = float(self.cutoff_freq)

@dataclass
class FilteredData:
    """滤波后的数据结构"""
    original_sample: SampleData
    filtered_value: float
    filter_delay: float = 0.0  # 滤波器延迟
    filter_gain: float = 1.0   # 滤波器增益
    processing_time: float = 0.0  # 处理时间

## FILTER BASE CLASS ###########################################################
class DigitalFilter(ABC):
    """数字滤波器抽象基类"""
    
    def __init__(self, config: FilterConfig):
        self.config = config
        self.is_initialized = False
        self.state = {}  # 滤波器状态
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time()
        }
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化滤波器"""
        pass
    
    @abstractmethod
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        pass
    
    @abstractmethod
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        pass
    
    @abstractmethod
    def reset(self):
        """重置滤波器状态"""
        pass
    
    def get_frequency_response(self, frequencies: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """获取频率响应"""
        # 默认实现，子类可以重写
        return frequencies, np.ones_like(frequencies)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取滤波器统计信息"""
        stats = self.statistics.copy()
        if stats['samples_processed'] > 0:
            stats['avg_processing_time'] = stats['processing_time_total'] / stats['samples_processed']
        return stats

## IIR FILTER IMPLEMENTATION ###################################################
class IIRFilter(DigitalFilter):
    """IIR滤波器实现"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        self.b_coeffs = None  # 前向系数
        self.a_coeffs = None  # 反馈系数
        self.x_history = []   # 输入历史
        self.y_history = []   # 输出历史
    
    def initialize(self) -> bool:
        """初始化IIR滤波器"""
        try:
            # 计算滤波器系数
            self._calculate_coefficients()
            
            # 初始化历史缓冲区
            self.x_history = [0.0] * len(self.b_coeffs)
            self.y_history = [0.0] * (len(self.a_coeffs) - 1)
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"IIR滤波器初始化失败: {e}")
            return False
    
    def _calculate_coefficients(self):
        """计算滤波器系数"""
        nyquist = self.config.sampling_rate / 2.0
        
        if self.config.filter_type == FilterType.LOWPASS:
            self._design_lowpass(nyquist)
        elif self.config.filter_type == FilterType.HIGHPASS:
            self._design_highpass(nyquist)
        elif self.config.filter_type == FilterType.BANDPASS:
            self._design_bandpass(nyquist)
        elif self.config.filter_type == FilterType.BANDSTOP:
            self._design_bandstop(nyquist)
        else:
            # 默认低通滤波器
            self._design_lowpass(nyquist)
    
    def _design_lowpass(self, nyquist: float):
        """设计低通滤波器"""
        # 简化的Butterworth低通滤波器设计
        wc = self.config.cutoff_freq / nyquist
        
        if self.config.order == 1:
            # 一阶低通
            alpha = np.exp(-2.0 * np.pi * wc)
            self.b_coeffs = [1.0 - alpha]
            self.a_coeffs = [1.0, -alpha]
        elif self.config.order == 2:
            # 二阶低通 (Butterworth)
            w = 2.0 * np.pi * wc
            k = np.tan(w / 2.0)
            norm = 1.0 + np.sqrt(2.0) * k + k * k
            
            self.b_coeffs = [k * k / norm, 2.0 * k * k / norm, k * k / norm]
            self.a_coeffs = [1.0, (2.0 * (k * k - 1.0)) / norm, (1.0 - np.sqrt(2.0) * k + k * k) / norm]
        else:
            # 高阶滤波器 - 简化实现
            self._design_higher_order_lowpass(wc)
    
    def _design_highpass(self, nyquist: float):
        """设计高通滤波器"""
        wc = self.config.cutoff_freq / nyquist
        
        if self.config.order == 1:
            # 一阶高通
            alpha = np.exp(-2.0 * np.pi * wc)
            self.b_coeffs = [alpha, -alpha]
            self.a_coeffs = [1.0, -alpha]
        elif self.config.order == 2:
            # 二阶高通 (Butterworth)
            w = 2.0 * np.pi * wc
            k = np.tan(w / 2.0)
            norm = 1.0 + np.sqrt(2.0) * k + k * k
            
            self.b_coeffs = [1.0 / norm, -2.0 / norm, 1.0 / norm]
            self.a_coeffs = [1.0, (2.0 * (k * k - 1.0)) / norm, (1.0 - np.sqrt(2.0) * k + k * k) / norm]
        else:
            # 高阶滤波器
            self._design_higher_order_highpass(wc)
    
    def _design_bandpass(self, nyquist: float):
        """设计带通滤波器"""
        if isinstance(self.config.cutoff_freq, list) and len(self.config.cutoff_freq) == 2:
            wc1 = self.config.cutoff_freq[0] / nyquist
            wc2 = self.config.cutoff_freq[1] / nyquist
            
            # 简化的带通滤波器设计
            w1 = 2.0 * np.pi * wc1
            w2 = 2.0 * np.pi * wc2
            wc = np.sqrt(w1 * w2)  # 中心频率
            bw = w2 - w1           # 带宽
            
            # 二阶带通滤波器
            r = 1.0 - 3.0 * bw
            k = (1.0 - 2.0 * r * np.cos(wc) + r * r) / (2.0 - 2.0 * np.cos(wc))
            
            self.b_coeffs = [1.0 - k, 2.0 * (k - r) * np.cos(wc), r * r - k]
            self.a_coeffs = [1.0, 2.0 * r * np.cos(wc), -r * r]
        else:
            raise ValueError("带通滤波器需要两个截止频率")
    
    def _design_bandstop(self, nyquist: float):
        """设计带阻滤波器"""
        if isinstance(self.config.cutoff_freq, list) and len(self.config.cutoff_freq) == 2:
            wc1 = self.config.cutoff_freq[0] / nyquist
            wc2 = self.config.cutoff_freq[1] / nyquist
            
            # 简化的带阻滤波器设计
            w1 = 2.0 * np.pi * wc1
            w2 = 2.0 * np.pi * wc2
            wc = np.sqrt(w1 * w2)  # 中心频率
            bw = w2 - w1           # 带宽
            
            # 二阶带阻滤波器
            r = 1.0 - 3.0 * bw
            k = (1.0 - 2.0 * r * np.cos(wc) + r * r) / (2.0 - 2.0 * np.cos(wc))
            
            self.b_coeffs = [k, -2.0 * k * np.cos(wc), k]
            self.a_coeffs = [1.0, 2.0 * r * np.cos(wc), -r * r]
        else:
            raise ValueError("带阻滤波器需要两个截止频率")
    
    def _design_higher_order_lowpass(self, wc: float):
        """设计高阶低通滤波器"""
        # 简化实现：级联二阶段
        sections = self.config.order // 2
        if self.config.order % 2 == 1:
            sections += 1
        
        # 为简化，使用二阶Butterworth段
        w = 2.0 * np.pi * wc
        k = np.tan(w / 2.0)
        norm = 1.0 + np.sqrt(2.0) * k + k * k
        
        self.b_coeffs = [k * k / norm, 2.0 * k * k / norm, k * k / norm]
        self.a_coeffs = [1.0, (2.0 * (k * k - 1.0)) / norm, (1.0 - np.sqrt(2.0) * k + k * k) / norm]
    
    def _design_higher_order_highpass(self, wc: float):
        """设计高阶高通滤波器"""
        # 简化实现：使用二阶Butterworth高通
        w = 2.0 * np.pi * wc
        k = np.tan(w / 2.0)
        norm = 1.0 + np.sqrt(2.0) * k + k * k
        
        self.b_coeffs = [1.0 / norm, -2.0 / norm, 1.0 / norm]
        self.a_coeffs = [1.0, (2.0 * (k * k - 1.0)) / norm, (1.0 - np.sqrt(2.0) * k + k * k) / norm]
    
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        # 更新输入历史
        self.x_history.insert(0, sample.value)
        if len(self.x_history) > len(self.b_coeffs):
            self.x_history.pop()
        
        # 计算输出
        y = 0.0
        
        # 前向部分 (FIR)
        for i, b in enumerate(self.b_coeffs):
            if i < len(self.x_history):
                y += b * self.x_history[i]
        
        # 反馈部分 (IIR)
        for i, a in enumerate(self.a_coeffs[1:], 1):
            if i - 1 < len(self.y_history):
                y -= a * self.y_history[i - 1]
        
        # 更新输出历史
        self.y_history.insert(0, y)
        if len(self.y_history) > len(self.a_coeffs) - 1:
            self.y_history.pop()
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        return FilteredData(
            original_sample=sample,
            filtered_value=y,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        if self.b_coeffs:
            self.x_history = [0.0] * len(self.b_coeffs)
        if self.a_coeffs:
            self.y_history = [0.0] * (len(self.a_coeffs) - 1)
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time()
        }

## FIR FILTER IMPLEMENTATION ###################################################
class FIRFilter(DigitalFilter):
    """FIR滤波器实现"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        self.coefficients = None
        self.delay_line = []
    
    def initialize(self) -> bool:
        """初始化FIR滤波器"""
        try:
            self._design_fir_filter()
            self.delay_line = [0.0] * len(self.coefficients)
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"FIR滤波器初始化失败: {e}")
            return False
    
    def _design_fir_filter(self):
        """设计FIR滤波器"""
        nyquist = self.config.sampling_rate / 2.0
        
        if self.config.filter_type == FilterType.LOWPASS:
            self._design_fir_lowpass(nyquist)
        elif self.config.filter_type == FilterType.HIGHPASS:
            self._design_fir_highpass(nyquist)
        elif self.config.filter_type == FilterType.BANDPASS:
            self._design_fir_bandpass(nyquist)
        elif self.config.filter_type == FilterType.MOVING_AVERAGE:
            self._design_moving_average()
        else:
            self._design_fir_lowpass(nyquist)
    
    def _design_fir_lowpass(self, nyquist: float):
        """设计FIR低通滤波器"""
        wc = self.config.cutoff_freq / nyquist
        N = self.config.order + 1
        
        # 理想低通滤波器的冲激响应
        n = np.arange(N)
        h = np.sinc(2 * wc * (n - (N - 1) / 2))
        
        # 应用窗函数
        window = self._get_window(N)
        self.coefficients = h * window
        
        # 归一化
        self.coefficients = self.coefficients / np.sum(self.coefficients)
    
    def _design_fir_highpass(self, nyquist: float):
        """设计FIR高通滤波器"""
        wc = self.config.cutoff_freq / nyquist
        N = self.config.order + 1
        
        # 先设计低通，然后转换为高通
        n = np.arange(N)
        h_lp = np.sinc(2 * wc * (n - (N - 1) / 2))
        
        # 高通 = 全通 - 低通
        h_hp = np.zeros(N)
        h_hp[(N - 1) // 2] = 1.0
        h_hp = h_hp - h_lp
        
        # 应用窗函数
        window = self._get_window(N)
        self.coefficients = h_hp * window
    
    def _design_fir_bandpass(self, nyquist: float):
        """设计FIR带通滤波器"""
        if isinstance(self.config.cutoff_freq, list) and len(self.config.cutoff_freq) == 2:
            wc1 = self.config.cutoff_freq[0] / nyquist
            wc2 = self.config.cutoff_freq[1] / nyquist
            N = self.config.order + 1
            
            # 带通 = 高频低通 - 低频低通
            n = np.arange(N)
            h_lp1 = np.sinc(2 * wc1 * (n - (N - 1) / 2))
            h_lp2 = np.sinc(2 * wc2 * (n - (N - 1) / 2))
            h_bp = h_lp2 - h_lp1
            
            # 应用窗函数
            window = self._get_window(N)
            self.coefficients = h_bp * window
        else:
            raise ValueError("带通滤波器需要两个截止频率")
    
    def _design_moving_average(self):
        """设计移动平均滤波器"""
        N = self.config.order + 1
        self.coefficients = np.ones(N) / N
    
    def _get_window(self, N: int) -> np.ndarray:
        """获取窗函数"""
        if self.config.window == 'hamming':
            return np.hamming(N)
        elif self.config.window == 'hanning':
            return np.hanning(N)
        elif self.config.window == 'blackman':
            return np.blackman(N)
        elif self.config.window == 'kaiser':
            return np.kaiser(N, beta=8.6)
        else:
            return np.ones(N)  # 矩形窗
    
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        # 更新延迟线
        self.delay_line.insert(0, sample.value)
        if len(self.delay_line) > len(self.coefficients):
            self.delay_line.pop()
        
        # 计算卷积
        y = 0.0
        for i, coeff in enumerate(self.coefficients):
            if i < len(self.delay_line):
                y += coeff * self.delay_line[i]
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        return FilteredData(
            original_sample=sample,
            filtered_value=y,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        if self.coefficients:
            self.delay_line = [0.0] * len(self.coefficients)
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time()
        }

## ADAPTIVE FILTER IMPLEMENTATION ##############################################
class AdaptiveFilter(DigitalFilter):
    """自适应滤波器实现"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        self.weights = None
        self.input_buffer = []
        self.reference_buffer = []
        self.error_history = []
    
    def initialize(self) -> bool:
        """初始化自适应滤波器"""
        try:
            # 初始化权重
            self.weights = np.zeros(self.config.filter_length)
            self.input_buffer = [0.0] * self.config.filter_length
            self.reference_buffer = []
            self.error_history = []
            
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"自适应滤波器初始化失败: {e}")
            return False
    
    def process_sample(self, sample: SampleData, reference: float = None) -> FilteredData:
        """处理单个样本（需要参考信号）"""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        # 更新输入缓冲区
        self.input_buffer.insert(0, sample.value)
        if len(self.input_buffer) > self.config.filter_length:
            self.input_buffer.pop()
        
        # 计算滤波器输出
        x = np.array(self.input_buffer[:len(self.weights)])
        y = np.dot(self.weights, x)
        
        # 如果有参考信号，更新权重
        if reference is not None:
            error = reference - y
            self.error_history.append(error)
            
            # LMS算法更新权重
            self.weights += self.config.adaptation_rate * error * x
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        return FilteredData(
            original_sample=sample,
            filtered_value=y,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        if self.weights is not None:
            self.weights.fill(0.0)
        self.input_buffer = [0.0] * self.config.filter_length
        self.reference_buffer = []
        self.error_history = []
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time()
        }

class KalmanFilter(DigitalFilter):
    """卡尔曼滤波器实现"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        # 状态变量
        self.x = config.initial_estimate  # 状态估计
        self.P = config.initial_error     # 估计误差协方差
        self.Q = config.process_noise     # 过程噪声协方差
        self.R = config.measurement_noise # 测量噪声协方差
        self.K = 0.0                      # 卡尔曼增益
        
        # 状态转移和观测模型（简单的一维情况）
        self.F = 1.0  # 状态转移矩阵
        self.H = 1.0  # 观测矩阵
        
    def initialize(self) -> bool:
        """初始化滤波器"""
        try:
            # 重置状态
            self.x = self.config.initial_estimate
            self.P = self.config.initial_error
            self.K = 0.0
            
            self.statistics = {
                'samples_processed': 0,
                'processing_time_total': 0.0,
                'last_update': time.time(),
                'kalman_gain_avg': 0.0,
                'estimation_error_avg': 0.0
            }
            return True
        except Exception as e:
            print(f"卡尔曼滤波器初始化失败: {e}")
            return False
    
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        start_time = time.time()
        
        # 预测步骤
        x_pred = self.F * self.x  # 状态预测
        P_pred = self.F * self.P * self.F + self.Q  # 协方差预测
        
        # 更新步骤
        z = sample.value  # 观测值
        y = z - self.H * x_pred  # 创新（残差）
        S = self.H * P_pred * self.H + self.R  # 创新协方差
        self.K = P_pred * self.H / S  # 卡尔曼增益
        
        # 状态更新
        self.x = x_pred + self.K * y
        self.P = (1 - self.K * self.H) * P_pred
        
        processing_time = time.time() - start_time
        
        # 更新统计信息
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        # 计算平均值
        n = self.statistics['samples_processed']
        self.statistics['kalman_gain_avg'] = (self.statistics['kalman_gain_avg'] * (n-1) + self.K) / n
        self.statistics['estimation_error_avg'] = (self.statistics['estimation_error_avg'] * (n-1) + abs(y)) / n
        
        return FilteredData(
            original_sample=sample,
            filtered_value=self.x,
            filter_delay=0.0,  # 卡尔曼滤波器没有固定延迟
            filter_gain=self.K,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        self.x = self.config.initial_estimate
        self.P = self.config.initial_error
        self.K = 0.0
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time(),
            'kalman_gain_avg': 0.0,
            'estimation_error_avg': 0.0
        }

class HuberRobustFilter(DigitalFilter):
    """Huber鲁棒滤波器实现"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        self.threshold = config.huber_threshold
        self.window_size = config.robust_window_size
        self.data_buffer = []
        self.filtered_value = 0.0
        
    def initialize(self) -> bool:
        """初始化滤波器"""
        try:
            self.data_buffer = []
            self.filtered_value = 0.0
            
            self.statistics = {
                'samples_processed': 0,
                'processing_time_total': 0.0,
                'last_update': time.time(),
                'outliers_detected': 0
            }
            return True
        except Exception as e:
            print(f"Huber鲁棒滤波器初始化失败: {e}")
            return False
    
    def _huber_weight(self, residual: float) -> float:
        """计算Huber权重"""
        abs_residual = abs(residual)
        if abs_residual <= self.threshold:
            return 1.0
        else:
            return self.threshold / abs_residual
    
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        start_time = time.time()
        
        # 添加新样本到缓冲区
        self.data_buffer.append(sample.value)
        if len(self.data_buffer) > self.window_size:
            self.data_buffer.pop(0)
        
        if len(self.data_buffer) == 1:
            self.filtered_value = sample.value
        else:
            # 计算加权平均值
            median_val = np.median(self.data_buffer)
            weighted_sum = 0.0
            weight_sum = 0.0
            
            outliers = 0
            for val in self.data_buffer:
                residual = val - median_val
                weight = self._huber_weight(residual)
                if weight < 1.0:
                    outliers += 1
                weighted_sum += weight * val
                weight_sum += weight
            
            if weight_sum > 0:
                self.filtered_value = weighted_sum / weight_sum
            else:
                self.filtered_value = median_val
            
            self.statistics['outliers_detected'] += outliers
        
        processing_time = time.time() - start_time
        
        # 更新统计信息
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        return FilteredData(
            original_sample=sample,
            filtered_value=self.filtered_value,
            filter_delay=len(self.data_buffer) / 2.0,  # 估计延迟
            filter_gain=1.0,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        self.data_buffer = []
        self.filtered_value = 0.0
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time(),
            'outliers_detected': 0
        }

class AlphaBetaFilter(DigitalFilter):
    """α-β滤波器实现（简化的卡尔曼滤波）"""
    
    def __init__(self, config: FilterConfig):
        super().__init__(config)
        self.alpha = config.alpha  # 位置平滑因子
        self.beta = config.beta    # 速度平滑因子
        self.dt = 1.0 / config.sampling_rate  # 采样间隔
        
        # 状态变量
        self.position = 0.0  # 位置估计
        self.velocity = 0.0  # 速度估计
        self.initialized = False
        
    def initialize(self) -> bool:
        """初始化滤波器"""
        try:
            self.position = 0.0
            self.velocity = 0.0
            self.initialized = False
            
            self.statistics = {
                'samples_processed': 0,
                'processing_time_total': 0.0,
                'last_update': time.time(),
                'velocity_avg': 0.0
            }
            return True
        except Exception as e:
            print(f"α-β滤波器初始化失败: {e}")
            return False
    
    def process_sample(self, sample: SampleData) -> FilteredData:
        """处理单个样本"""
        start_time = time.time()
        
        if not self.initialized:
            # 第一个样本，直接初始化
            self.position = sample.value
            self.velocity = 0.0
            self.initialized = True
        else:
            # 预测步骤
            predicted_position = self.position + self.velocity * self.dt
            
            # 更新步骤
            residual = sample.value - predicted_position
            self.position = predicted_position + self.alpha * residual
            self.velocity = self.velocity + (self.beta * residual) / self.dt
        
        processing_time = time.time() - start_time
        
        # 更新统计信息
        self.statistics['samples_processed'] += 1
        self.statistics['processing_time_total'] += processing_time
        self.statistics['last_update'] = time.time()
        
        # 计算平均速度
        n = self.statistics['samples_processed']
        if n > 1:
            self.statistics['velocity_avg'] = (self.statistics['velocity_avg'] * (n-1) + abs(self.velocity)) / n
        
        return FilteredData(
            original_sample=sample,
            filtered_value=self.position,
            filter_delay=0.0,  # α-β滤波器延迟很小
            filter_gain=self.alpha,
            processing_time=processing_time
        )
    
    def process_batch(self, samples: List[SampleData]) -> List[FilteredData]:
        """批量处理样本"""
        return [self.process_sample(sample) for sample in samples]
    
    def reset(self):
        """重置滤波器状态"""
        self.position = 0.0
        self.velocity = 0.0
        self.initialized = False
        
        self.statistics = {
            'samples_processed': 0,
            'processing_time_total': 0.0,
            'last_update': time.time(),
            'velocity_avg': 0.0
        }

## FILTER FACTORY ##############################################################
class FilterFactory:
    """滤波器工厂类"""
    
    @staticmethod
    def create_filter(config: FilterConfig) -> DigitalFilter:
        """创建滤波器实例"""
        if config.filter_method == FilterMethod.IIR:
            return IIRFilter(config)
        elif config.filter_method == FilterMethod.FIR:
            return FIRFilter(config)
        elif config.filter_method == FilterMethod.ADAPTIVE:
            return AdaptiveFilter(config)
        elif config.filter_method == FilterMethod.KALMAN:
            return KalmanFilter(config)
        elif config.filter_method == FilterMethod.ROBUST:
            return HuberRobustFilter(config)
        elif config.filter_method == FilterMethod.STATE_SPACE:
            # 根据滤波器类型选择具体实现
            if config.filter_type == FilterType.KALMAN:
                return KalmanFilter(config)
            elif config.filter_type == FilterType.ALPHA_BETA:
                return AlphaBetaFilter(config)
            elif config.filter_type == FilterType.HUBER_ROBUST:
                return HuberRobustFilter(config)
            else:
                raise ValueError(f"不支持的状态空间滤波器类型: {config.filter_type}")
        else:
            raise ValueError(f"不支持的滤波方法: {config.filter_method}")

## REAL-TIME FILTER PROCESSOR ##################################################
class RealTimeFilterProcessor(pt.PrintClient):
    """实时滤波处理器"""
    
    SYMBOL = "[RF]"
    
    def __init__(self, pqueue):
        """初始化实时滤波处理器"""
        pt.PrintClient.__init__(self, pqueue)
        
        self.filters = {}  # 滤波器字典 {channel_id: [filters]}
        self.input_queue = queue.Queue(maxsize=10000)
        self.output_queue = queue.Queue(maxsize=10000)
        self.processing_thread = None
        self.is_running = False
        self.callbacks = []  # 输出回调函数
        
        self.statistics = {
            'samples_processed': 0,
            'samples_dropped': 0,
            'processing_errors': 0,
            'start_time': None
        }
    
    def add_filter(self, channel_id: int, filter_config: FilterConfig):
        """为指定通道添加滤波器"""
        try:
            filter_instance = FilterFactory.create_filter(filter_config)
            
            if channel_id not in self.filters:
                self.filters[channel_id] = []
            
            self.filters[channel_id].append(filter_instance)
            self.printr(f"为通道{channel_id}添加{filter_config.filter_type.value}滤波器")
            return True
            
        except Exception as e:
            self.printe(f"添加滤波器失败: {e}")
            return False
    
    def remove_filter(self, channel_id: int, filter_index: int = -1):
        """移除指定通道的滤波器"""
        if channel_id in self.filters:
            if filter_index == -1:
                # 移除所有滤波器
                del self.filters[channel_id]
                self.print(f"移除通道{channel_id}的所有滤波器")
            else:
                # 移除指定滤波器
                if 0 <= filter_index < len(self.filters[channel_id]):
                    self.filters[channel_id].pop(filter_index)
                    self.print(f"移除通道{channel_id}的滤波器{filter_index}")
    
    def start_processing(self) -> bool:
        """开始实时滤波处理"""
        if self.is_running:
            self.print("滤波处理已在运行中", level=pt.WARNING)
            return True
        
        try:
            self.is_running = True
            self.statistics['start_time'] = time.time()
            
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.print("实时滤波处理已启动")
            return True
            
        except Exception as e:
            self.print(f"启动滤波处理失败: {e}", level=pt.ERROR)
            self.is_running = False
            return False
    
    def stop_processing(self) -> bool:
        """停止实时滤波处理"""
        if not self.is_running:
            return True
        
        try:
            self.is_running = False
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
            
            self.print("实时滤波处理已停止")
            return True
            
        except Exception as e:
            self.print(f"停止滤波处理失败: {e}", level=pt.ERROR)
            return False
    
    def process_samples(self, samples: List[SampleData]):
        """处理输入样本"""
        try:
            self.input_queue.put(samples, timeout=0.001)
        except queue.Full:
            self.statistics['samples_dropped'] += len(samples)
            self.print("输入队列已满，丢弃样本", level=pt.WARNING)
    
    def get_filtered_samples(self, timeout: float = 0.1) -> List[FilteredData]:
        """获取滤波后的样本"""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return []
    
    def add_output_callback(self, callback):
        """添加输出回调函数"""
        self.callbacks.append(callback)
    
    def remove_output_callback(self, callback):
        """移除输出回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.statistics.copy()
        
        # 添加滤波器统计信息
        filter_stats = {}
        for channel_id, filters in self.filters.items():
            filter_stats[channel_id] = [f.get_statistics() for f in filters]
        stats['filter_statistics'] = filter_stats
        
        if stats['start_time']:
            stats['runtime'] = time.time() - stats['start_time']
        
        return stats
    
    def _processing_loop(self):
        """滤波处理循环"""
        self.print("滤波处理线程启动")
        
        while self.is_running:
            try:
                # 获取输入样本
                samples = self.input_queue.get(timeout=0.1)
                
                if samples:
                    filtered_samples = []
                    
                    for sample in samples:
                        channel_id = sample.channel_id
                        
                        if channel_id in self.filters:
                            # 依次通过该通道的所有滤波器
                            current_sample = sample
                            
                            for filter_instance in self.filters[channel_id]:
                                if filter_instance.config.enabled:
                                    filtered_data = filter_instance.process_sample(current_sample)
                                    # 为下一个滤波器创建新的样本
                                    current_sample = SampleData(
                                        timestamp=current_sample.timestamp,
                                        channel_id=current_sample.channel_id,
                                        value=filtered_data.filtered_value,
                                        raw_value=current_sample.raw_value,
                                        quality=current_sample.quality
                                    )
                                    filtered_samples.append(filtered_data)
                        else:
                            # 没有滤波器，直接输出原始数据
                            filtered_samples.append(FilteredData(
                                original_sample=sample,
                                filtered_value=sample.value
                            ))
                    
                    # 更新统计信息
                    self.statistics['samples_processed'] += len(samples)
                    
                    # 输出滤波后的数据
                    if filtered_samples:
                        try:
                            self.output_queue.put(filtered_samples, timeout=0.001)
                        except queue.Full:
                            self.print("输出队列已满", level=pt.WARNING)
                        
                        # 调用回调函数
                        for callback in self.callbacks:
                            try:
                                callback(filtered_samples)
                            except Exception as e:
                                self.print(f"回调函数错误: {e}", level=pt.ERROR)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.statistics['processing_errors'] += 1
                self.print(f"滤波处理错误: {e}", level=pt.ERROR)
                time.sleep(0.01)
        
        self.print("滤波处理线程结束")

## FILTER BANK #################################################################
class FilterBank(pt.PrintClient):
    """滤波器组 - 管理多个并行滤波器"""
    
    SYMBOL = "[FB]"
    
    def __init__(self, pqueue):
        """初始化滤波器组"""
        pt.PrintClient.__init__(self, pqueue)
        
        self.processors = {}  # 处理器字典
        self.global_config = None
        
    def add_processor(self, name: str, processor: RealTimeFilterProcessor):
        """添加滤波处理器"""
        self.processors[name] = processor
        self.print(f"添加滤波处理器: {name}")
    
    def remove_processor(self, name: str):
        """移除滤波处理器"""
        if name in self.processors:
            self.processors[name].stop_processing()
            del self.processors[name]
            self.print(f"移除滤波处理器: {name}")
    
    def start_all(self) -> bool:
        """启动所有处理器"""
        success = True
        for name, processor in self.processors.items():
            if not processor.start_processing():
                self.print(f"处理器{name}启动失败", level=pt.ERROR)
                success = False
        
        if success:
            self.print("所有滤波处理器已启动")
        return success
    
    def stop_all(self) -> bool:
        """停止所有处理器"""
        success = True
        for name, processor in self.processors.items():
            if not processor.stop_processing():
                self.print(f"处理器{name}停止失败", level=pt.ERROR)
                success = False
        
        if success:
            self.print("所有滤波处理器已停止")
        return success
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        stats = {
            'processors': {},
            'total_samples_processed': 0,
            'total_errors': 0,
            'active_processors': 0
        }
        
        for name, processor in self.processors.items():
            proc_stats = processor.get_statistics()
            stats['processors'][name] = proc_stats
            stats['total_samples_processed'] += proc_stats.get('samples_processed', 0)
            stats['total_errors'] += proc_stats.get('processing_errors', 0)
            if processor.is_running:
                stats['active_processors'] += 1
        
        return stats
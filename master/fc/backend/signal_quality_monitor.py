################################################################################
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY                                                        ##
## ADVANCED SYSTEMS LABORATORY                                                ##
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
## AUTHORS: zhaoyang (mzymuzhaoyang@gmail.com)                               ##
##          dashuai (dschen2018@gmail.com)                                   ##
##----------------------------------------------------------------------------##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + 信号质量监测机制
 + 提供实时信号质量分析、异常检测和质量评估功能
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import numpy as np
import scipy.signal as signal
import scipy.stats as stats
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import time
from collections import deque
import warnings

class QualityLevel(Enum):
    """信号质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class AnomalyType(Enum):
    """异常类型"""
    SATURATION = "saturation"          # 饱和
    DROPOUT = "dropout"                # 信号丢失
    NOISE_SPIKE = "noise_spike"        # 噪声尖峰
    DC_DRIFT = "dc_drift"              # 直流漂移
    FREQUENCY_ANOMALY = "freq_anomaly" # 频率异常
    AMPLITUDE_ANOMALY = "amp_anomaly"  # 幅度异常
    CLIPPING = "clipping"              # 削波
    INTERFERENCE = "interference"       # 干扰

@dataclass
class QualityMetrics:
    """质量指标"""
    snr_db: float                    # 信噪比 (dB)
    thd_percent: float               # 总谐波失真 (%)
    rms_value: float                 # 有效值
    peak_value: float                # 峰值
    crest_factor: float              # 峰值因子
    dynamic_range_db: float          # 动态范围 (dB)
    frequency_stability: float       # 频率稳定性
    amplitude_stability: float       # 幅度稳定性
    noise_floor_db: float            # 噪声底
    quality_score: float             # 综合质量分数 (0-100)
    quality_level: QualityLevel      # 质量等级
    timestamp: datetime              # 时间戳

@dataclass
class AnomalyEvent:
    """异常事件"""
    anomaly_type: AnomalyType
    severity: float                  # 严重程度 (0-1)
    start_time: datetime
    end_time: Optional[datetime]
    channel: str
    description: str
    affected_samples: Tuple[int, int]  # 受影响的样本范围
    confidence: float                # 检测置信度 (0-1)

class SignalAnalyzer:
    """信号分析器"""
    
    def __init__(self, sample_rate: float):
        self.sample_rate = sample_rate
        self.nyquist_freq = sample_rate / 2
    
    def calculate_snr(self, signal_data: np.ndarray, 
                     noise_band: Tuple[float, float] = None) -> float:
        """计算信噪比"""
        try:
            # 计算信号功率
            signal_power = np.mean(signal_data ** 2)
            
            if noise_band:
                # 在指定频带内估计噪声
                f, psd = signal.welch(signal_data, self.sample_rate, nperseg=1024)
                noise_mask = (f >= noise_band[0]) & (f <= noise_band[1])
                noise_power = np.mean(psd[noise_mask])
            else:
                # 使用高频部分估计噪声
                high_freq_cutoff = self.nyquist_freq * 0.8
                sos = signal.butter(4, high_freq_cutoff, 'highpass', 
                                  fs=self.sample_rate, output='sos')
                noise_signal = signal.sosfilt(sos, signal_data)
                noise_power = np.mean(noise_signal ** 2)
            
            if noise_power > 0:
                snr_linear = signal_power / noise_power
                snr_db = 10 * np.log10(snr_linear)
            else:
                snr_db = float('inf')
            
            return max(snr_db, 0)  # 确保非负
        except Exception as e:
            print(f"SNR计算失败: {e}")
            return 0.0
    
    def calculate_thd(self, signal_data: np.ndarray, 
                     fundamental_freq: float = None) -> float:
        """计算总谐波失真"""
        try:
            # 计算功率谱
            f, psd = signal.welch(signal_data, self.sample_rate, nperseg=2048)
            
            if fundamental_freq is None:
                # 自动检测基频
                fundamental_idx = np.argmax(psd[1:]) + 1  # 排除直流分量
                fundamental_freq = f[fundamental_idx]
            
            # 找到基频和谐波的功率
            fundamental_power = 0
            harmonic_power = 0
            
            for harmonic in range(1, 6):  # 考虑前5次谐波
                target_freq = fundamental_freq * harmonic
                if target_freq > self.nyquist_freq:
                    break
                
                # 找到最接近的频率索引
                freq_idx = np.argmin(np.abs(f - target_freq))
                power = psd[freq_idx]
                
                if harmonic == 1:
                    fundamental_power = power
                else:
                    harmonic_power += power
            
            if fundamental_power > 0:
                thd = np.sqrt(harmonic_power / fundamental_power) * 100
            else:
                thd = 0.0
            
            return min(thd, 100)  # 限制在100%以内
        except Exception as e:
            print(f"THD计算失败: {e}")
            return 0.0
    
    def calculate_dynamic_range(self, signal_data: np.ndarray) -> float:
        """计算动态范围"""
        try:
            # 计算信号的最大值和噪声底
            max_amplitude = np.max(np.abs(signal_data))
            
            # 估计噪声底（使用最小值的统计方法）
            abs_signal = np.abs(signal_data)
            noise_floor = np.percentile(abs_signal, 5)  # 5%分位数作为噪声底
            
            if noise_floor > 0:
                dynamic_range = 20 * np.log10(max_amplitude / noise_floor)
            else:
                dynamic_range = 120  # 默认值
            
            return max(dynamic_range, 0)
        except Exception as e:
            print(f"动态范围计算失败: {e}")
            return 0.0
    
    def calculate_stability(self, signal_data: np.ndarray, 
                          window_size: int = 1024) -> Tuple[float, float]:
        """计算频率和幅度稳定性"""
        try:
            # 分段分析
            num_windows = len(signal_data) // window_size
            if num_windows < 2:
                return 1.0, 1.0
            
            frequencies = []
            amplitudes = []
            
            for i in range(num_windows):
                start_idx = i * window_size
                end_idx = start_idx + window_size
                segment = signal_data[start_idx:end_idx]
                
                # 计算主频率
                f, psd = signal.welch(segment, self.sample_rate, nperseg=window_size//4)
                main_freq_idx = np.argmax(psd[1:]) + 1
                main_freq = f[main_freq_idx]
                frequencies.append(main_freq)
                
                # 计算RMS幅度
                rms_amp = np.sqrt(np.mean(segment ** 2))
                amplitudes.append(rms_amp)
            
            # 计算稳定性（变异系数的倒数）
            freq_stability = 1.0 / (1.0 + np.std(frequencies) / np.mean(frequencies))
            amp_stability = 1.0 / (1.0 + np.std(amplitudes) / np.mean(amplitudes))
            
            return freq_stability, amp_stability
        except Exception as e:
            print(f"稳定性计算失败: {e}")
            return 0.5, 0.5

class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, sample_rate: float):
        self.sample_rate = sample_rate
        self.detection_thresholds = {
            'saturation_threshold': 0.95,      # 饱和阈值
            'dropout_threshold': 0.01,         # 信号丢失阈值
            'spike_threshold': 5.0,            # 尖峰检测阈值（标准差倍数）
            'drift_threshold': 0.1,            # 漂移检测阈值
            'clipping_threshold': 0.98         # 削波检测阈值
        }
    
    def detect_saturation(self, signal_data: np.ndarray, 
                         channel: str) -> List[AnomalyEvent]:
        """检测信号饱和"""
        anomalies = []
        try:
            # 归一化信号到[-1, 1]
            max_val = np.max(np.abs(signal_data))
            if max_val > 0:
                normalized = signal_data / max_val
            else:
                return anomalies
            
            # 检测饱和点
            saturation_mask = np.abs(normalized) > self.detection_thresholds['saturation_threshold']
            
            if np.any(saturation_mask):
                # 找到连续的饱和区域
                saturation_regions = self._find_continuous_regions(saturation_mask)
                
                for start_idx, end_idx in saturation_regions:
                    severity = np.mean(np.abs(normalized[start_idx:end_idx]))
                    
                    anomaly = AnomalyEvent(
                        anomaly_type=AnomalyType.SATURATION,
                        severity=severity,
                        start_time=datetime.now(),
                        end_time=None,
                        channel=channel,
                        description=f"信号饱和检测到 {end_idx - start_idx} 个样本",
                        affected_samples=(start_idx, end_idx),
                        confidence=0.9
                    )
                    anomalies.append(anomaly)
        
        except Exception as e:
            print(f"饱和检测失败: {e}")
        
        return anomalies
    
    def detect_dropout(self, signal_data: np.ndarray, 
                      channel: str) -> List[AnomalyEvent]:
        """检测信号丢失"""
        anomalies = []
        try:
            # 计算滑动RMS
            window_size = int(self.sample_rate * 0.01)  # 10ms窗口
            rms_values = self._sliding_rms(signal_data, window_size)
            
            # 检测低于阈值的区域
            dropout_mask = rms_values < self.detection_thresholds['dropout_threshold']
            
            if np.any(dropout_mask):
                dropout_regions = self._find_continuous_regions(dropout_mask)
                
                for start_idx, end_idx in dropout_regions:
                    duration_ms = (end_idx - start_idx) / self.sample_rate * 1000
                    
                    # 只报告持续时间超过1ms的丢失
                    if duration_ms > 1.0:
                        severity = 1.0 - np.mean(rms_values[start_idx:end_idx])
                        
                        anomaly = AnomalyEvent(
                            anomaly_type=AnomalyType.DROPOUT,
                            severity=severity,
                            start_time=datetime.now(),
                            end_time=None,
                            channel=channel,
                            description=f"信号丢失 {duration_ms:.1f}ms",
                            affected_samples=(start_idx, end_idx),
                            confidence=0.8
                        )
                        anomalies.append(anomaly)
        
        except Exception as e:
            print(f"信号丢失检测失败: {e}")
        
        return anomalies
    
    def detect_noise_spikes(self, signal_data: np.ndarray, 
                           channel: str) -> List[AnomalyEvent]:
        """检测噪声尖峰"""
        anomalies = []
        try:
            # 计算信号的统计特性
            mean_val = np.mean(signal_data)
            std_val = np.std(signal_data)
            
            # 检测超过阈值的尖峰
            threshold = self.detection_thresholds['spike_threshold'] * std_val
            spike_mask = np.abs(signal_data - mean_val) > threshold
            
            if np.any(spike_mask):
                spike_indices = np.where(spike_mask)[0]
                
                # 合并相邻的尖峰
                spike_groups = self._group_adjacent_indices(spike_indices)
                
                for group in spike_groups:
                    start_idx, end_idx = group[0], group[-1] + 1
                    max_deviation = np.max(np.abs(signal_data[group] - mean_val))
                    severity = min(max_deviation / (threshold * 2), 1.0)
                    
                    anomaly = AnomalyEvent(
                        anomaly_type=AnomalyType.NOISE_SPIKE,
                        severity=severity,
                        start_time=datetime.now(),
                        end_time=None,
                        channel=channel,
                        description=f"噪声尖峰，偏差 {max_deviation:.3f}",
                        affected_samples=(start_idx, end_idx),
                        confidence=0.7
                    )
                    anomalies.append(anomaly)
        
        except Exception as e:
            print(f"尖峰检测失败: {e}")
        
        return anomalies
    
    def detect_dc_drift(self, signal_data: np.ndarray, 
                       channel: str) -> List[AnomalyEvent]:
        """检测直流漂移"""
        anomalies = []
        try:
            # 分段计算均值
            segment_size = int(self.sample_rate)  # 1秒段
            num_segments = len(signal_data) // segment_size
            
            if num_segments < 3:
                return anomalies
            
            segment_means = []
            for i in range(num_segments):
                start_idx = i * segment_size
                end_idx = start_idx + segment_size
                segment_mean = np.mean(signal_data[start_idx:end_idx])
                segment_means.append(segment_mean)
            
            # 检测趋势
            x = np.arange(len(segment_means))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, segment_means)
            
            # 判断是否存在显著漂移
            drift_rate = abs(slope) * self.sample_rate  # 每秒漂移量
            signal_range = np.ptp(signal_data)
            
            if drift_rate > self.detection_thresholds['drift_threshold'] * signal_range:
                severity = min(drift_rate / signal_range, 1.0)
                
                anomaly = AnomalyEvent(
                    anomaly_type=AnomalyType.DC_DRIFT,
                    severity=severity,
                    start_time=datetime.now(),
                    end_time=None,
                    channel=channel,
                    description=f"直流漂移，速率 {drift_rate:.6f}/s",
                    affected_samples=(0, len(signal_data)),
                    confidence=abs(r_value)
                )
                anomalies.append(anomaly)
        
        except Exception as e:
            print(f"直流漂移检测失败: {e}")
        
        return anomalies
    
    def _find_continuous_regions(self, mask: np.ndarray) -> List[Tuple[int, int]]:
        """找到连续的True区域"""
        regions = []
        in_region = False
        start_idx = 0
        
        for i, value in enumerate(mask):
            if value and not in_region:
                start_idx = i
                in_region = True
            elif not value and in_region:
                regions.append((start_idx, i))
                in_region = False
        
        # 处理末尾的区域
        if in_region:
            regions.append((start_idx, len(mask)))
        
        return regions
    
    def _sliding_rms(self, signal_data: np.ndarray, window_size: int) -> np.ndarray:
        """计算滑动RMS"""
        rms_values = np.zeros(len(signal_data))
        
        for i in range(len(signal_data)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(signal_data), i + window_size // 2)
            window_data = signal_data[start_idx:end_idx]
            rms_values[i] = np.sqrt(np.mean(window_data ** 2))
        
        return rms_values
    
    def _group_adjacent_indices(self, indices: np.ndarray) -> List[List[int]]:
        """将相邻的索引分组"""
        if len(indices) == 0:
            return []
        
        groups = []
        current_group = [indices[0]]
        
        for i in range(1, len(indices)):
            if indices[i] - indices[i-1] <= 2:  # 允许1个样本的间隔
                current_group.append(indices[i])
            else:
                groups.append(current_group)
                current_group = [indices[i]]
        
        groups.append(current_group)
        return groups

class QualityMonitor:
    """信号质量监测器"""
    
    def __init__(self, sample_rate: float, buffer_size: int = 10000):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        self.analyzer = SignalAnalyzer(sample_rate)
        self.detector = AnomalyDetector(sample_rate)
        
        # 历史数据缓冲区
        self.quality_history = deque(maxlen=1000)
        self.anomaly_history = deque(maxlen=1000)
        
        # 监测状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 质量评估权重
        self.quality_weights = {
            'snr': 0.25,
            'thd': 0.15,
            'dynamic_range': 0.15,
            'stability': 0.20,
            'anomaly_penalty': 0.25
        }
    
    def analyze_quality(self, signal_data: np.ndarray, 
                       channel: str = "default") -> QualityMetrics:
        """分析信号质量"""
        try:
            # 基本统计量
            rms_value = np.sqrt(np.mean(signal_data ** 2))
            peak_value = np.max(np.abs(signal_data))
            crest_factor = peak_value / rms_value if rms_value > 0 else 0
            
            # 质量指标计算
            snr_db = self.analyzer.calculate_snr(signal_data)
            thd_percent = self.analyzer.calculate_thd(signal_data)
            dynamic_range_db = self.analyzer.calculate_dynamic_range(signal_data)
            freq_stability, amp_stability = self.analyzer.calculate_stability(signal_data)
            
            # 噪声底估计
            f, psd = signal.welch(signal_data, self.sample_rate, nperseg=1024)
            noise_floor_db = 10 * np.log10(np.percentile(psd, 10))
            
            # 异常检测
            anomalies = self.detect_anomalies(signal_data, channel)
            
            # 综合质量评分
            quality_score = self._calculate_quality_score(
                snr_db, thd_percent, dynamic_range_db, 
                freq_stability, amp_stability, len(anomalies)
            )
            
            # 质量等级
            quality_level = self._determine_quality_level(quality_score)
            
            metrics = QualityMetrics(
                snr_db=snr_db,
                thd_percent=thd_percent,
                rms_value=rms_value,
                peak_value=peak_value,
                crest_factor=crest_factor,
                dynamic_range_db=dynamic_range_db,
                frequency_stability=freq_stability,
                amplitude_stability=amp_stability,
                noise_floor_db=noise_floor_db,
                quality_score=quality_score,
                quality_level=quality_level,
                timestamp=datetime.now()
            )
            
            # 保存到历史记录
            self.quality_history.append(metrics)
            
            return metrics
        
        except Exception as e:
            print(f"质量分析失败: {e}")
            return None
    
    def detect_anomalies(self, signal_data: np.ndarray, 
                        channel: str = "default") -> List[AnomalyEvent]:
        """检测信号异常"""
        all_anomalies = []
        
        try:
            # 各种异常检测
            anomalies = []
            anomalies.extend(self.detector.detect_saturation(signal_data, channel))
            anomalies.extend(self.detector.detect_dropout(signal_data, channel))
            anomalies.extend(self.detector.detect_noise_spikes(signal_data, channel))
            anomalies.extend(self.detector.detect_dc_drift(signal_data, channel))
            
            # 保存到历史记录
            for anomaly in anomalies:
                self.anomaly_history.append(anomaly)
            
            all_anomalies.extend(anomalies)
        
        except Exception as e:
            print(f"异常检测失败: {e}")
        
        return all_anomalies
    
    def _calculate_quality_score(self, snr_db: float, thd_percent: float,
                               dynamic_range_db: float, freq_stability: float,
                               amp_stability: float, anomaly_count: int) -> float:
        """计算综合质量分数"""
        try:
            # SNR评分 (0-100)
            snr_score = min(snr_db / 60 * 100, 100)  # 60dB为满分
            
            # THD评分 (0-100)
            thd_score = max(100 - thd_percent * 10, 0)  # THD越低越好
            
            # 动态范围评分 (0-100)
            dr_score = min(dynamic_range_db / 96 * 100, 100)  # 96dB为满分
            
            # 稳定性评分 (0-100)
            stability_score = (freq_stability + amp_stability) / 2 * 100
            
            # 异常惩罚
            anomaly_penalty = min(anomaly_count * 10, 50)  # 每个异常扣10分，最多扣50分
            
            # 加权计算
            weighted_score = (
                snr_score * self.quality_weights['snr'] +
                thd_score * self.quality_weights['thd'] +
                dr_score * self.quality_weights['dynamic_range'] +
                stability_score * self.quality_weights['stability']
            ) - anomaly_penalty * self.quality_weights['anomaly_penalty']
            
            return max(min(weighted_score, 100), 0)
        
        except Exception as e:
            print(f"质量评分计算失败: {e}")
            return 50.0
    
    def _determine_quality_level(self, quality_score: float) -> QualityLevel:
        """确定质量等级"""
        if quality_score >= 90:
            return QualityLevel.EXCELLENT
        elif quality_score >= 75:
            return QualityLevel.GOOD
        elif quality_score >= 60:
            return QualityLevel.FAIR
        elif quality_score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def get_quality_summary(self, time_window: timedelta = None) -> Dict[str, Any]:
        """获取质量摘要"""
        if not self.quality_history:
            return {}
        
        # 时间过滤
        if time_window:
            cutoff_time = datetime.now() - time_window
            filtered_metrics = [m for m in self.quality_history 
                              if m.timestamp >= cutoff_time]
        else:
            filtered_metrics = list(self.quality_history)
        
        if not filtered_metrics:
            return {}
        
        # 统计计算
        scores = [m.quality_score for m in filtered_metrics]
        snr_values = [m.snr_db for m in filtered_metrics]
        
        summary = {
            'average_quality_score': np.mean(scores),
            'min_quality_score': np.min(scores),
            'max_quality_score': np.max(scores),
            'quality_std': np.std(scores),
            'average_snr_db': np.mean(snr_values),
            'total_samples': len(filtered_metrics),
            'quality_distribution': {
                level.value: sum(1 for m in filtered_metrics 
                               if m.quality_level == level)
                for level in QualityLevel
            },
            'recent_anomalies': len([a for a in self.anomaly_history 
                                   if time_window is None or 
                                   a.start_time >= datetime.now() - time_window])
        }
        
        return summary

# 使用示例
if __name__ == "__main__":
    # 创建质量监测器
    sample_rate = 1000.0
    monitor = QualityMonitor(sample_rate)
    
    # 生成测试信号
    t = np.linspace(0, 10, int(sample_rate * 10))
    clean_signal = np.sin(2 * np.pi * 10 * t)
    
    # 添加噪声和异常
    noisy_signal = clean_signal + 0.1 * np.random.randn(len(t))
    
    # 添加一些异常
    noisy_signal[1000:1010] = 2.0  # 饱和
    noisy_signal[2000:2050] = 0.0  # 信号丢失
    noisy_signal[3000] = 5.0       # 尖峰
    
    # 分析质量
    metrics = monitor.analyze_quality(noisy_signal, "test_channel")
    
    if metrics:
        print(f"质量分数: {metrics.quality_score:.1f}")
        print(f"质量等级: {metrics.quality_level.value}")
        print(f"信噪比: {metrics.snr_db:.1f} dB")
        print(f"总谐波失真: {metrics.thd_percent:.2f}%")
        print(f"动态范围: {metrics.dynamic_range_db:.1f} dB")
    
    # 获取质量摘要
    summary = monitor.get_quality_summary()
    print(f"\n质量摘要: {summary}")
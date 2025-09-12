#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
滤波参数可视化配置界面
提供直观的滤波器参数配置和实时预览功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import scipy.signal as signal
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import threading
import sys
import os

# 添加backend模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from digital_filtering import FilterType, FilterMethod, FilterConfig, FilterFactory
except ImportError:
    print("警告: 无法导入数字滤波模块，使用模拟实现")
    
    class FilterType:
        LOWPASS = "lowpass"
        HIGHPASS = "highpass"
        BANDPASS = "bandpass"
        BANDSTOP = "bandstop"
        BUTTERWORTH = "butterworth"
        CHEBYSHEV1 = "chebyshev1"
        KALMAN = "kalman"
        HUBER_ROBUST = "huber_robust"
        ALPHA_BETA = "alpha_beta"
    
    class FilterMethod:
        IIR = "iir"
        FIR = "fir"
        ADAPTIVE = "adaptive"
        KALMAN = "kalman"
        ROBUST = "robust"
        STATE_SPACE = "state_space"
    
    class FilterConfig:
        def __init__(self):
            self.filter_type = FilterType.LOWPASS
            self.filter_method = FilterMethod.IIR
            self.cutoff_freq = 100.0
            self.sampling_rate = 1000.0
            self.order = 4
            self.ripple = 1.0
            self.attenuation = 40.0
            # 新滤波器参数
            self.process_noise = 0.01
            self.measurement_noise = 0.1
            self.initial_estimate = 0.0
            self.initial_error = 1.0
            self.huber_threshold = 1.345
            self.robust_window_size = 10
            self.alpha = 0.85
            self.beta = 0.005

class FilterConfigGUI:
    """滤波器配置GUI主类"""
    
    def __init__(self, root=None):
        if root is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = root
            self.standalone = False
        
        self.root.title("滤波器参数配置")
        self.root.geometry("1200x800")
        
        # 配置参数
        self.config = FilterConfig()
        self.sample_rate = 1000.0
        self.preview_signal = None
        self.filtered_signal = None
        
        # 创建界面
        self.create_widgets()
        self.setup_layout()
        self.bind_events()
        
        # 初始化显示
        self.update_filter_response()
        self.generate_preview_signal()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.root)
        
        # 左侧控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="滤波器配置", padding=10)
        
        # 滤波器类型选择
        self.create_filter_type_widgets()
        
        # 基本参数配置
        self.create_basic_params_widgets()
        
        # 高级参数配置
        self.create_advanced_params_widgets()
        
        # 控制按钮
        self.create_control_buttons()
        
        # 右侧显示面板
        self.display_frame = ttk.Frame(self.main_frame)
        
        # 频率响应图
        self.create_frequency_response_plot()
        
        # 时域预览图
        self.create_time_domain_plot()
        
        # 状态栏
        self.create_status_bar()
    
    def create_filter_type_widgets(self):
        """创建滤波器类型选择组件"""
        type_frame = ttk.LabelFrame(self.control_frame, text="滤波器类型", padding=5)
        
        # 滤波方法
        ttk.Label(type_frame, text="方法:").grid(row=0, column=0, sticky="w", padx=5)
        self.filter_method_var = tk.StringVar(value=FilterMethod.IIR)
        self.filter_method_combo = ttk.Combobox(type_frame, textvariable=self.filter_method_var,
                                              values=[
                                                  FilterMethod.IIR,
                                                  FilterMethod.FIR,
                                                  FilterMethod.ADAPTIVE,
                                                  FilterMethod.KALMAN,
                                                  FilterMethod.ROBUST,
                                                  FilterMethod.STATE_SPACE
                                              ], state="readonly")
        self.filter_method_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)
        
        # 滤波器类型
        ttk.Label(type_frame, text="类型:").grid(row=1, column=0, sticky="w", padx=5)
        self.filter_type_var = tk.StringVar(value=FilterType.LOWPASS)
        self.filter_type_combo = ttk.Combobox(type_frame, textvariable=self.filter_type_var,
                                            values=[
                                                FilterType.LOWPASS,
                                                FilterType.HIGHPASS,
                                                FilterType.BANDPASS,
                                                FilterType.BANDSTOP,
                                                FilterType.BUTTERWORTH,
                                                FilterType.CHEBYSHEV1,
                                                FilterType.KALMAN,
                                                FilterType.HUBER_ROBUST,
                                                FilterType.ALPHA_BETA
                                            ], state="readonly")
        self.filter_type_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        
        type_frame.columnconfigure(1, weight=1)
        self.type_frame = type_frame
        
        # 绑定事件以动态更新可用选项
        self.filter_method_combo.bind('<<ComboboxSelected>>', self.on_filter_method_change)
    
    def create_basic_params_widgets(self):
        """创建基本参数配置组件"""
        basic_frame = ttk.LabelFrame(self.control_frame, text="基本参数", padding=5)
        
        # 采样率
        ttk.Label(basic_frame, text="采样率 (Hz):").grid(row=0, column=0, sticky="w", padx=5)
        self.sample_rate_var = tk.DoubleVar(value=1000.0)
        self.sample_rate_entry = ttk.Entry(basic_frame, textvariable=self.sample_rate_var, width=10)
        self.sample_rate_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        # 截止频率
        ttk.Label(basic_frame, text="截止频率 (Hz):").grid(row=1, column=0, sticky="w", padx=5)
        self.cutoff_freq_var = tk.DoubleVar(value=100.0)
        self.cutoff_freq_entry = ttk.Entry(basic_frame, textvariable=self.cutoff_freq_var, width=10)
        self.cutoff_freq_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        # 滤波器阶数
        ttk.Label(basic_frame, text="阶数:").grid(row=2, column=0, sticky="w", padx=5)
        self.order_var = tk.IntVar(value=4)
        self.order_scale = ttk.Scale(basic_frame, from_=1, to=20, orient="horizontal",
                                   variable=self.order_var, command=self.on_order_change)
        self.order_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.order_label = ttk.Label(basic_frame, text="4")
        self.order_label.grid(row=2, column=2, padx=5)
        
        basic_frame.columnconfigure(1, weight=1)
        self.basic_frame = basic_frame
    
    def create_advanced_params_widgets(self):
        """创建高级参数配置组件"""
        advanced_frame = ttk.LabelFrame(self.control_frame, text="高级参数", padding=5)
        
        # 通带纹波 (Chebyshev I)
        ttk.Label(advanced_frame, text="通带纹波 (dB):").grid(row=0, column=0, sticky="w", padx=5)
        self.ripple_var = tk.DoubleVar(value=1.0)
        self.ripple_entry = ttk.Entry(advanced_frame, textvariable=self.ripple_var, width=10)
        self.ripple_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        # 阻带衰减 (Chebyshev II, Elliptic)
        ttk.Label(advanced_frame, text="阻带衰减 (dB):").grid(row=1, column=0, sticky="w", padx=5)
        self.attenuation_var = tk.DoubleVar(value=40.0)
        self.attenuation_entry = ttk.Entry(advanced_frame, textvariable=self.attenuation_var, width=10)
        self.attenuation_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        # 窗函数类型 (FIR)
        ttk.Label(advanced_frame, text="窗函数:").grid(row=2, column=0, sticky="w", padx=5)
        self.window_var = tk.StringVar(value="hamming")
        self.window_combo = ttk.Combobox(advanced_frame, textvariable=self.window_var,
                                       values=["hamming", "hann", "blackman", "kaiser", "rectangular"],
                                       state="readonly")
        self.window_combo.grid(row=2, column=1, sticky="ew", padx=5)
        
        # 卡尔曼滤波参数
        self.kalman_frame = ttk.LabelFrame(advanced_frame, text="卡尔曼滤波参数", padding=5)
        
        ttk.Label(self.kalman_frame, text="过程噪声:").grid(row=0, column=0, sticky="w", padx=5)
        self.process_noise_var = tk.DoubleVar(value=0.01)
        self.process_noise_entry = ttk.Entry(self.kalman_frame, textvariable=self.process_noise_var, width=10)
        self.process_noise_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.kalman_frame, text="观测噪声:").grid(row=1, column=0, sticky="w", padx=5)
        self.measurement_noise_var = tk.DoubleVar(value=0.1)
        self.measurement_noise_entry = ttk.Entry(self.kalman_frame, textvariable=self.measurement_noise_var, width=10)
        self.measurement_noise_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.kalman_frame, text="初始估计:").grid(row=2, column=0, sticky="w", padx=5)
        self.initial_estimate_var = tk.DoubleVar(value=0.0)
        self.initial_estimate_entry = ttk.Entry(self.kalman_frame, textvariable=self.initial_estimate_var, width=10)
        self.initial_estimate_entry.grid(row=2, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.kalman_frame, text="初始误差:").grid(row=3, column=0, sticky="w", padx=5)
        self.initial_error_var = tk.DoubleVar(value=1.0)
        self.initial_error_entry = ttk.Entry(self.kalman_frame, textvariable=self.initial_error_var, width=10)
        self.initial_error_entry.grid(row=3, column=1, sticky="ew", padx=5)
        
        self.kalman_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.kalman_frame.columnconfigure(1, weight=1)
        
        # Huber鲁棒滤波参数
        self.robust_frame = ttk.LabelFrame(advanced_frame, text="Huber鲁棒滤波参数", padding=5)
        
        ttk.Label(self.robust_frame, text="阈值:").grid(row=0, column=0, sticky="w", padx=5)
        self.huber_threshold_var = tk.DoubleVar(value=1.345)
        self.huber_threshold_entry = ttk.Entry(self.robust_frame, textvariable=self.huber_threshold_var, width=10)
        self.huber_threshold_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.robust_frame, text="窗口大小:").grid(row=1, column=0, sticky="w", padx=5)
        self.robust_window_size_var = tk.IntVar(value=10)
        self.robust_window_size_entry = ttk.Entry(self.robust_frame, textvariable=self.robust_window_size_var, width=10)
        self.robust_window_size_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        self.robust_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.robust_frame.columnconfigure(1, weight=1)
        
        # α-β滤波参数
        self.alpha_beta_frame = ttk.LabelFrame(advanced_frame, text="α-β滤波参数", padding=5)
        
        ttk.Label(self.alpha_beta_frame, text="α因子:").grid(row=0, column=0, sticky="w", padx=5)
        self.alpha_var = tk.DoubleVar(value=0.85)
        self.alpha_entry = ttk.Entry(self.alpha_beta_frame, textvariable=self.alpha_var, width=10)
        self.alpha_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.alpha_beta_frame, text="β因子:").grid(row=1, column=0, sticky="w", padx=5)
        self.beta_var = tk.DoubleVar(value=0.005)
        self.beta_entry = ttk.Entry(self.alpha_beta_frame, textvariable=self.beta_var, width=10)
        self.beta_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        self.alpha_beta_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.alpha_beta_frame.columnconfigure(1, weight=1)
        
        advanced_frame.columnconfigure(1, weight=1)
        self.advanced_frame = advanced_frame
    
    def create_control_buttons(self):
        """创建控制按钮"""
        button_frame = ttk.Frame(self.control_frame)
        
        # 应用按钮
        self.apply_btn = ttk.Button(button_frame, text="应用滤波器", command=self.apply_filter)
        self.apply_btn.pack(side="left", padx=5)
        
        # 重置按钮
        self.reset_btn = ttk.Button(button_frame, text="重置参数", command=self.reset_parameters)
        self.reset_btn.pack(side="left", padx=5)
        
        # 保存配置
        self.save_btn = ttk.Button(button_frame, text="保存配置", command=self.save_config)
        self.save_btn.pack(side="left", padx=5)
        
        # 加载配置
        self.load_btn = ttk.Button(button_frame, text="加载配置", command=self.load_config)
        self.load_btn.pack(side="left", padx=5)
        
        self.button_frame = button_frame
    
    def create_frequency_response_plot(self):
        """创建频率响应图"""
        plot_frame = ttk.LabelFrame(self.display_frame, text="频率响应", padding=5)
        
        # 创建matplotlib图形
        self.freq_fig = Figure(figsize=(8, 4), dpi=100)
        self.freq_ax1 = self.freq_fig.add_subplot(211)
        self.freq_ax2 = self.freq_fig.add_subplot(212)
        
        self.freq_ax1.set_title("幅度响应")
        self.freq_ax1.set_ylabel("幅度 (dB)")
        self.freq_ax1.grid(True, alpha=0.3)
        
        self.freq_ax2.set_title("相位响应")
        self.freq_ax2.set_xlabel("频率 (Hz)")
        self.freq_ax2.set_ylabel("相位 (度)")
        self.freq_ax2.grid(True, alpha=0.3)
        
        self.freq_fig.tight_layout()
        
        # 嵌入到tkinter
        self.freq_canvas = FigureCanvasTkAgg(self.freq_fig, plot_frame)
        self.freq_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.freq_plot_frame = plot_frame
    
    def create_time_domain_plot(self):
        """创建时域预览图"""
        plot_frame = ttk.LabelFrame(self.display_frame, text="时域预览", padding=5)
        
        # 创建matplotlib图形
        self.time_fig = Figure(figsize=(8, 4), dpi=100)
        self.time_ax = self.time_fig.add_subplot(111)
        
        self.time_ax.set_title("滤波前后对比")
        self.time_ax.set_xlabel("时间 (s)")
        self.time_ax.set_ylabel("幅度")
        self.time_ax.grid(True, alpha=0.3)
        
        self.time_fig.tight_layout()
        
        # 嵌入到tkinter
        self.time_canvas = FigureCanvasTkAgg(self.time_fig, plot_frame)
        self.time_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 信号生成控制
        control_frame = ttk.Frame(plot_frame)
        control_frame.pack(fill="x", pady=5)
        
        ttk.Label(control_frame, text="测试信号:").pack(side="left", padx=5)
        
        self.signal_type_var = tk.StringVar(value="mixed")
        signal_combo = ttk.Combobox(control_frame, textvariable=self.signal_type_var,
                                  values=["sine", "square", "sawtooth", "noise", "mixed"],
                                  state="readonly", width=10)
        signal_combo.pack(side="left", padx=5)
        signal_combo.bind("<<ComboboxSelected>>", lambda e: self.generate_preview_signal())
        
        ttk.Button(control_frame, text="生成新信号", 
                  command=self.generate_preview_signal).pack(side="left", padx=5)
        
        self.time_plot_frame = plot_frame
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, 
                                   relief="sunken", anchor="w")
    
    def setup_layout(self):
        """设置布局"""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        self.control_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # 滤波器类型
        self.type_frame.pack(fill="x", pady=5)
        
        # 基本参数
        self.basic_frame.pack(fill="x", pady=5)
        
        # 高级参数
        self.advanced_frame.pack(fill="x", pady=5)
        
        # 控制按钮
        self.button_frame.pack(fill="x", pady=10)
        
        # 右侧显示面板
        self.display_frame.pack(side="right", fill="both", expand=True)
        
        # 频率响应图
        self.freq_plot_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # 时域预览图
        self.time_plot_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # 状态栏
        self.status_bar.pack(side="bottom", fill="x", pady=(5, 0))
    
    def bind_events(self):
        """绑定事件"""
        # 参数变化时自动更新
        self.filter_type_var.trace("w", lambda *args: self.on_parameter_change())
        self.filter_method_var.trace("w", lambda *args: self.on_filter_method_change())
        self.sample_rate_var.trace("w", lambda *args: self.on_parameter_change())
        self.cutoff_freq_var.trace("w", lambda *args: self.on_parameter_change())
        self.ripple_var.trace("w", lambda *args: self.on_parameter_change())
        self.attenuation_var.trace("w", lambda *args: self.on_parameter_change())
        self.window_var.trace("w", lambda *args: self.on_parameter_change())
        self.process_noise_var.trace("w", lambda *args: self.on_parameter_change())
        self.measurement_noise_var.trace("w", lambda *args: self.on_parameter_change())
        self.initial_estimate_var.trace("w", lambda *args: self.on_parameter_change())
        self.initial_error_var.trace("w", lambda *args: self.on_parameter_change())
        self.huber_threshold_var.trace("w", lambda *args: self.on_parameter_change())
        self.robust_window_size_var.trace("w", lambda *args: self.on_parameter_change())
        self.alpha_var.trace("w", lambda *args: self.on_parameter_change())
        self.beta_var.trace("w", lambda *args: self.on_parameter_change())
    
    def on_filter_method_change(self, event=None):
        """滤波方法变化时的处理"""
        method = self.filter_method_var.get()
        
        # 隐藏所有专用参数框架
        self.kalman_frame.grid_remove()
        self.robust_frame.grid_remove()
        self.alpha_beta_frame.grid_remove()
        
        # 根据选择的方法显示相应的参数
        if method == FilterMethod.KALMAN:
            self.kalman_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        elif method == FilterMethod.ROBUST:
            self.robust_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        elif method == FilterMethod.STATE_SPACE:
            self.alpha_beta_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 更新滤波器响应
        self.on_parameter_change()
    
    def on_order_change(self, value):
        """阶数变化回调"""
        order = int(float(value))
        self.order_label.config(text=str(order))
        self.on_parameter_change()
    
    def on_parameter_change(self):
        """参数变化回调"""
        try:
            self.update_config_from_gui()
            self.update_filter_response()
            self.status_var.set("参数已更新")
        except Exception as e:
            self.status_var.set(f"参数错误: {str(e)}")
    
    def update_config_from_gui(self):
        """从GUI更新配置"""
        self.config.filter_type = self.filter_type_var.get()
        self.config.filter_method = self.filter_method_var.get()
        self.config.sampling_rate = self.sample_rate_var.get()
        self.config.cutoff_freq = self.cutoff_freq_var.get()
        self.config.order = self.order_var.get()
        self.config.ripple = self.ripple_var.get()
        self.config.attenuation = self.attenuation_var.get()
        
        # 新滤波器参数
        self.config.process_noise = self.process_noise_var.get()
        self.config.measurement_noise = self.measurement_noise_var.get()
        self.config.initial_estimate = self.initial_estimate_var.get()
        self.config.initial_error = self.initial_error_var.get()
        self.config.huber_threshold = self.huber_threshold_var.get()
        self.config.robust_window_size = self.robust_window_size_var.get()
        self.config.alpha = self.alpha_var.get()
        self.config.beta = self.beta_var.get()
        
        # 验证参数
        if self.config.cutoff_freq >= self.config.sampling_rate / 2:
            raise ValueError("截止频率必须小于奈奎斯特频率")
        
        if self.config.order < 1 or self.config.order > 20:
            raise ValueError("滤波器阶数必须在1-20之间")
    
    def update_filter_response(self):
        """更新频率响应图"""
        try:
            # 设计滤波器
            if self.config.filter_type.startswith("iir"):
                filter_design = self.design_iir_filter()
            else:
                filter_design = self.design_fir_filter()
            
            if filter_design is None:
                return
            
            b, a = filter_design
            
            # 计算频率响应
            w, h = signal.freqz(b, a, worN=2048, fs=self.config.sample_rate)
            
            # 更新幅度响应图
            self.freq_ax1.clear()
            self.freq_ax1.plot(w, 20 * np.log10(np.abs(h) + 1e-10))
            self.freq_ax1.set_title("幅度响应")
            self.freq_ax1.set_ylabel("幅度 (dB)")
            self.freq_ax1.grid(True, alpha=0.3)
            self.freq_ax1.axvline(self.config.cutoff_freq, color='r', linestyle='--', alpha=0.7)
            
            # 更新相位响应图
            self.freq_ax2.clear()
            angles = np.unwrap(np.angle(h)) * 180 / np.pi
            self.freq_ax2.plot(w, angles)
            self.freq_ax2.set_title("相位响应")
            self.freq_ax2.set_xlabel("频率 (Hz)")
            self.freq_ax2.set_ylabel("相位 (度)")
            self.freq_ax2.grid(True, alpha=0.3)
            self.freq_ax2.axvline(self.config.cutoff_freq, color='r', linestyle='--', alpha=0.7)
            
            self.freq_fig.tight_layout()
            self.freq_canvas.draw()
            
        except Exception as e:
            print(f"频率响应更新失败: {e}")
    
    def design_iir_filter(self):
        """设计IIR滤波器"""
        try:
            filter_type = self.config.filter_type.split('_')[1]  # 获取butterworth, chebyshev1等
            
            if filter_type == "butterworth":
                return signal.butter(self.config.order, self.config.cutoff_freq,
                                   btype=self.config.filter_mode, fs=self.config.sample_rate)
            elif filter_type == "chebyshev1":
                return signal.cheby1(self.config.order, self.config.ripple, 
                                    self.config.cutoff_freq, btype=self.config.filter_mode,
                                    fs=self.config.sample_rate)
            elif filter_type == "chebyshev2":
                return signal.cheby2(self.config.order, self.config.attenuation,
                                    self.config.cutoff_freq, btype=self.config.filter_mode,
                                    fs=self.config.sample_rate)
            elif filter_type == "elliptic":
                return signal.ellip(self.config.order, self.config.ripple,
                                  self.config.attenuation, self.config.cutoff_freq,
                                  btype=self.config.filter_mode, fs=self.config.sample_rate)
        except Exception as e:
            print(f"IIR滤波器设计失败: {e}")
            return None
    
    def design_fir_filter(self):
        """设计FIR滤波器"""
        try:
            nyquist = self.config.sample_rate / 2
            normalized_cutoff = self.config.cutoff_freq / nyquist
            
            # 计算滤波器长度
            numtaps = self.config.order * 2 + 1
            
            if self.config.filter_type == FilterType.FIR_WINDOW:
                window = self.window_var.get()
                b = signal.firwin(numtaps, normalized_cutoff, 
                                window=window, pass_zero=self.config.filter_mode)
                return b, [1.0]
            elif self.config.filter_type == FilterType.FIR_REMEZ:
                # Remez算法设计
                if self.config.filter_mode == "lowpass":
                    bands = [0, normalized_cutoff, normalized_cutoff + 0.1, 1]
                    desired = [1, 0]
                elif self.config.filter_mode == "highpass":
                    bands = [0, normalized_cutoff - 0.1, normalized_cutoff, 1]
                    desired = [0, 1]
                else:
                    # 带通和带阻需要更复杂的设计
                    return self.design_iir_filter()
                
                b = signal.remez(numtaps, bands, desired, fs=2)
                return b, [1.0]
        except Exception as e:
            print(f"FIR滤波器设计失败: {e}")
            return None
    
    def generate_preview_signal(self):
        """生成预览信号"""
        try:
            duration = 2.0  # 2秒
            t = np.linspace(0, duration, int(self.config.sample_rate * duration))
            
            signal_type = self.signal_type_var.get()
            
            if signal_type == "sine":
                self.preview_signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 150 * t)
            elif signal_type == "square":
                self.preview_signal = signal.square(2 * np.pi * 25 * t)
            elif signal_type == "sawtooth":
                self.preview_signal = signal.sawtooth(2 * np.pi * 25 * t)
            elif signal_type == "noise":
                self.preview_signal = np.random.randn(len(t))
            else:  # mixed
                self.preview_signal = (np.sin(2 * np.pi * 10 * t) + 
                                     0.5 * np.sin(2 * np.pi * 50 * t) +
                                     0.3 * np.sin(2 * np.pi * 200 * t) +
                                     0.1 * np.random.randn(len(t)))
            
            self.apply_filter()
            
        except Exception as e:
            print(f"信号生成失败: {e}")
    
    def apply_filter(self):
        """应用滤波器"""
        if self.preview_signal is None:
            self.generate_preview_signal()
            return
        
        try:
            # 设计滤波器
            if self.config.filter_type.startswith("iir"):
                filter_design = self.design_iir_filter()
            else:
                filter_design = self.design_fir_filter()
            
            if filter_design is None:
                return
            
            b, a = filter_design
            
            # 应用滤波器
            self.filtered_signal = signal.filtfilt(b, a, self.preview_signal)
            
            # 更新时域图
            self.update_time_domain_plot()
            
            self.status_var.set("滤波器已应用")
            
        except Exception as e:
            self.status_var.set(f"滤波失败: {str(e)}")
            print(f"滤波失败: {e}")
    
    def update_time_domain_plot(self):
        """更新时域图"""
        if self.preview_signal is None:
            return
        
        try:
            duration = len(self.preview_signal) / self.config.sample_rate
            t = np.linspace(0, duration, len(self.preview_signal))
            
            self.time_ax.clear()
            
            # 显示前0.5秒的数据
            display_samples = int(0.5 * self.config.sample_rate)
            t_display = t[:display_samples]
            
            self.time_ax.plot(t_display, self.preview_signal[:display_samples], 
                            label="原始信号", alpha=0.7)
            
            if self.filtered_signal is not None:
                self.time_ax.plot(t_display, self.filtered_signal[:display_samples],
                                label="滤波后信号", linewidth=2)
            
            self.time_ax.set_title("滤波前后对比")
            self.time_ax.set_xlabel("时间 (s)")
            self.time_ax.set_ylabel("幅度")
            self.time_ax.legend()
            self.time_ax.grid(True, alpha=0.3)
            
            self.time_fig.tight_layout()
            self.time_canvas.draw()
            
        except Exception as e:
            print(f"时域图更新失败: {e}")
    
    def reset_parameters(self):
        """重置参数"""
        self.filter_type_var.set(FilterType.IIR_BUTTERWORTH)
        self.filter_mode_var.set("lowpass")
        self.sample_rate_var.set(1000.0)
        self.cutoff_freq_var.set(100.0)
        self.order_var.set(4)
        self.ripple_var.set(1.0)
        self.attenuation_var.set(40.0)
        self.window_var.set("hamming")
        
        self.status_var.set("参数已重置")
    
    def save_config(self):
        """保存配置"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="保存滤波器配置"
            )
            
            if filename:
                config_dict = {
                    "filter_type": self.filter_type_var.get(),
                    "filter_mode": self.filter_mode_var.get(),
                    "sample_rate": self.sample_rate_var.get(),
                    "cutoff_freq": self.cutoff_freq_var.get(),
                    "order": self.order_var.get(),
                    "ripple": self.ripple_var.get(),
                    "attenuation": self.attenuation_var.get(),
                    "window": self.window_var.get(),
                    "saved_at": datetime.now().isoformat()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                self.status_var.set(f"配置已保存到 {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="加载滤波器配置"
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                # 更新GUI
                self.filter_type_var.set(config_dict.get("filter_type", FilterType.LOWPASS))
                self.filter_method_var.set(config_dict.get("filter_method", FilterMethod.IIR))
                self.sample_rate_var.set(config_dict.get("sampling_rate", 1000.0))
                self.cutoff_freq_var.set(config_dict.get("cutoff_freq", 100.0))
                self.order_var.set(config_dict.get("order", 4))
                self.ripple_var.set(config_dict.get("ripple", 1.0))
                self.attenuation_var.set(config_dict.get("attenuation", 40.0))
                self.window_var.set(config_dict.get("window", "hamming"))
                
                # 新滤波器参数
                self.process_noise_var.set(config_dict.get("process_noise", 0.01))
                self.measurement_noise_var.set(config_dict.get("measurement_noise", 0.1))
                self.initial_estimate_var.set(config_dict.get("initial_estimate", 0.0))
                self.initial_error_var.set(config_dict.get("initial_error", 1.0))
                self.huber_threshold_var.set(config_dict.get("huber_threshold", 1.345))
                self.robust_window_size_var.set(config_dict.get("robust_window_size", 10))
                self.alpha_var.set(config_dict.get("alpha", 0.85))
                self.beta_var.set(config_dict.get("beta", 0.005))
                
                # 更新参数显示
                self.on_filter_method_change()
                
                self.status_var.set(f"配置已从 {filename} 加载")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        self.update_config_from_gui()
        return {
            "filter_type": self.config.filter_type,
            "filter_method": self.config.filter_method,
            "sampling_rate": self.config.sampling_rate,
            "cutoff_freq": self.config.cutoff_freq,
            "order": self.config.order,
            "ripple": self.config.ripple,
            "attenuation": self.config.attenuation,
            "window": self.window_var.get(),
            "process_noise": self.config.process_noise,
            "measurement_noise": self.config.measurement_noise,
            "initial_estimate": self.config.initial_estimate,
            "initial_error": self.config.initial_error,
            "huber_threshold": self.config.huber_threshold,
            "robust_window_size": self.config.robust_window_size,
            "alpha": self.config.alpha,
            "beta": self.config.beta
        }
    
    def run(self):
        """运行GUI"""
        if self.standalone:
            self.root.mainloop()

def main():
    """主函数"""
    try:
        # 设置matplotlib后端
        plt.switch_backend('TkAgg')
        
        # 创建并运行GUI
        app = FilterConfigGUI()
        app.run()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")

if __name__ == "__main__":
    main()
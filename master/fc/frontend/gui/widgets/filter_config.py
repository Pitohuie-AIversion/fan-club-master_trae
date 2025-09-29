################################################################################
## Project: Fanclub Mark IV "Master" Filter Configuration Widget            ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
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
## zhaoyang                   ## <mzymuzhaoyang@gmail.com> ##                 ##
## dashuai                    ## <dschen2018@gmail.com>    ##                 ##
##                            ##                           ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Filter configuration widget for integration into main GUI.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib

# 配置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import numpy as np
import json
import os
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import math

# 尝试导入scipy，如果失败则设置为None
try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    signal = None
    SCIPY_AVAILABLE = False

# Import the filter configuration GUI components
from fc.frontend.filter_config_gui import FilterConfigGUI
from fc.backend.digital_filtering import FilterType, FilterMethod
from fc import printer as pt

# Import tach monitoring components
try:
    from fc.backend.mkiii import FCCommunicator as fcc
    FC_COMM_AVAILABLE = True
except ImportError:
    FC_COMM_AVAILABLE = False
    fcc = None

@dataclass
class TachReading:
    """Tach信号读数数据结构"""
    fan_id: int
    rpm: float
    timestamp: float
    duty_cycle: float = 0.0
    timeout: bool = False
    raw_signal: float = 0.0

## MAIN WIDGET #################################################################
class FilterConfigWidget(ttk.Frame, pt.PrintClient):
    """滤波器配置组件，集成到主GUI中"""
    
    SYMBOL = "[FC]"
    
    def __init__(self, master, archive=None, pqueue=None, monitoring_widget=None):
        """
        创建滤波器配置组件
        
        参数:
        - master: 父容器
        - archive: 配置存档（可选）
        - pqueue: 打印队列（可选）
        - monitoring_widget: 监控组件引用，用于获取tach数据
        """
        ttk.Frame.__init__(self, master=master)
        if pqueue:
            pt.PrintClient.__init__(self, pqueue, self.SYMBOL)
        
        self.archive = archive
        self.pqueue = pqueue
        self.monitoring_widget = monitoring_widget
        
        # 滤波器配置相关
        self.filtered_data = {}  # 存储滤波后的数据
        self.update_rate = 10.0  # 10Hz更新率
        
        # 从monitoring组件获取enabled_fans配置，如果不可用则使用默认值
        if self.monitoring_widget and hasattr(self.monitoring_widget, 'tach_config'):
            self.enabled_fans = self.monitoring_widget.tach_config.enabled_fans[:8]  # 最多8个风机
        else:
            self.enabled_fans = list(range(8))  # 默认监控前8个风机
        
        # 创建内嵌的滤波器配置GUI
        self.create_embedded_filter_gui()
        
    def create_embedded_filter_gui(self):
        """创建内嵌的滤波器配置界面"""
        try:
            # 创建一个容器框架
            self.container_frame = ttk.Frame(self)
            self.container_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # 创建滤波器配置GUI的主要组件
            self.create_filter_widgets()
            
            # 设置布局
            self.setup_layout()
            
            # 绑定事件
            self.bind_events()
            
            # 初始化默认值
            self.initialize_defaults()
            
        except Exception as e:
            if hasattr(self, 'printd'):
                self.printd(f"创建滤波器配置界面失败: {e}")
            else:
                print(f"创建滤波器配置界面失败: {e}")
    
    def create_filter_widgets(self):
        """创建滤波器配置组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.container_frame)
        
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
        self.type_frame = ttk.LabelFrame(self.control_frame, text="滤波器类型", padding=5)
        
        # 滤波器类型选择
        ttk.Label(self.type_frame, text="类型:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.filter_type_var = tk.StringVar(value="LOWPASS")
        self.filter_type_combo = ttk.Combobox(self.type_frame, textvariable=self.filter_type_var,
                                            values=["LOWPASS", "HIGHPASS", "BANDPASS", "BANDSTOP"],
                                            state="readonly", width=15)
        self.filter_type_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # 滤波方法选择
        ttk.Label(self.type_frame, text="方法:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.filter_method_var = tk.StringVar(value="BUTTERWORTH")
        self.filter_method_combo = ttk.Combobox(self.type_frame, textvariable=self.filter_method_var,
                                              values=["BUTTERWORTH", "CHEBYSHEV1", "CHEBYSHEV2", "ELLIPTIC", "BESSEL", "KALMAN", "HUBER_ROBUST", "ALPHA_BETA"],
                                              state="readonly", width=15)
        self.filter_method_combo.grid(row=1, column=1, padx=5, pady=2)
    
    def create_basic_params_widgets(self):
        """创建基本参数配置组件"""
        self.basic_frame = ttk.LabelFrame(self.control_frame, text="基本参数", padding=5)
        
        # 采样率
        ttk.Label(self.basic_frame, text="采样率 (Hz):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.sampling_rate_var = tk.StringVar(value="1000")
        self.sampling_rate_entry = ttk.Entry(self.basic_frame, textvariable=self.sampling_rate_var, width=15)
        self.sampling_rate_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 截止频率
        ttk.Label(self.basic_frame, text="截止频率 (Hz):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.cutoff_freq_var = tk.StringVar(value="100")
        self.cutoff_freq_entry = ttk.Entry(self.basic_frame, textvariable=self.cutoff_freq_var, width=15)
        self.cutoff_freq_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 滤波器阶数
        ttk.Label(self.basic_frame, text="阶数:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.order_var = tk.StringVar(value="4")
        self.order_entry = ttk.Entry(self.basic_frame, textvariable=self.order_var, width=15)
        self.order_entry.grid(row=2, column=1, padx=5, pady=2)
    
    def create_advanced_params_widgets(self):
        """创建高级参数配置组件"""
        self.advanced_frame = ttk.LabelFrame(self.control_frame, text="高级参数", padding=5)
        
        # 创建不同滤波方法的参数框架
        self.kalman_frame = ttk.Frame(self.advanced_frame)
        self.huber_frame = ttk.Frame(self.advanced_frame)
        self.alpha_beta_frame = ttk.Frame(self.advanced_frame)
        
        # 卡尔曼滤波参数
        ttk.Label(self.kalman_frame, text="过程噪声:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.process_noise_var = tk.StringVar(value="0.01")
        self.process_noise_entry = ttk.Entry(self.kalman_frame, textvariable=self.process_noise_var, width=15)
        self.process_noise_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.kalman_frame, text="观测噪声:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.observation_noise_var = tk.StringVar(value="0.1")
        self.observation_noise_entry = ttk.Entry(self.kalman_frame, textvariable=self.observation_noise_var, width=15)
        self.observation_noise_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Huber鲁棒滤波参数
        ttk.Label(self.huber_frame, text="阈值:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.huber_threshold_var = tk.StringVar(value="1.345")
        self.huber_threshold_entry = ttk.Entry(self.huber_frame, textvariable=self.huber_threshold_var, width=15)
        self.huber_threshold_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.huber_frame, text="窗口大小:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.huber_window_var = tk.StringVar(value="10")
        self.huber_window_entry = ttk.Entry(self.huber_frame, textvariable=self.huber_window_var, width=15)
        self.huber_window_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # α-β滤波参数
        ttk.Label(self.alpha_beta_frame, text="α因子:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.alpha_var = tk.StringVar(value="0.8")
        self.alpha_entry = ttk.Entry(self.alpha_beta_frame, textvariable=self.alpha_var, width=15)
        self.alpha_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.alpha_beta_frame, text="β因子:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.beta_var = tk.StringVar(value="0.2")
        self.beta_entry = ttk.Entry(self.alpha_beta_frame, textvariable=self.beta_var, width=15)
        self.beta_entry.grid(row=1, column=1, padx=5, pady=2)
    
    def create_control_buttons(self):
        """创建控制按钮"""
        self.button_frame = ttk.Frame(self.control_frame)
        
        # 应用滤波器按钮
        self.apply_button = ttk.Button(self.button_frame, text="应用滤波器", command=self.apply_filter)
        self.apply_button.pack(side="left", padx=5, pady=5)
        
        # 重置按钮
        self.reset_button = ttk.Button(self.button_frame, text="重置", command=self.reset_config)
        self.reset_button.pack(side="left", padx=5, pady=5)
        
        # 保存配置按钮
        self.save_button = ttk.Button(self.button_frame, text="保存配置", command=self.save_config)
        self.save_button.pack(side="left", padx=5, pady=5)
        
        # 加载配置按钮
        self.load_button = ttk.Button(self.button_frame, text="加载配置", command=self.load_config)
        self.load_button.pack(side="left", padx=5, pady=5)
    
    def create_frequency_response_plot(self):
        """创建频率响应图"""
        self.freq_plot_frame = ttk.LabelFrame(self.display_frame, text="频率响应", padding=5)
        
        # 创建matplotlib图形
        self.freq_fig = Figure(figsize=(6, 4), dpi=100)
        self.freq_ax = self.freq_fig.add_subplot(111)
        self.freq_canvas = FigureCanvasTkAgg(self.freq_fig, self.freq_plot_frame)
        self.freq_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 初始化空图
        self.freq_ax.set_xlabel("频率 (Hz)")
        self.freq_ax.set_ylabel("幅度 (dB)")
        self.freq_ax.set_title("频率响应")
        self.freq_ax.grid(True)
    
    def create_time_domain_plot(self):
        """创建时域预览图（显示实时tach数据）"""
        self.time_plot_frame = ttk.LabelFrame(self.display_frame, text="实时Tach信号监控", padding=5)
        
        # 创建matplotlib图形
        self.time_fig = Figure(figsize=(8, 5), dpi=100)
        self.time_ax = self.time_fig.add_subplot(111)
        self.time_canvas = FigureCanvasTkAgg(self.time_fig, self.time_plot_frame)
        self.time_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 设置图表样式
        self.time_fig.patch.set_facecolor('white')
        self.time_ax.set_facecolor('#f8f9fa')
        self.time_ax.set_xlabel("时间 (s)")
        self.time_ax.set_ylabel("RPM")
        self.time_ax.set_title("实时Tach信号监控")
        self.time_ax.grid(True, alpha=0.3)
        
        # 添加tach数据控制面板
        self.create_tach_control_panel()
        
    def create_tach_control_panel(self):
        """创建tach数据控制面板"""
        self.tach_control_frame = ttk.LabelFrame(self.control_frame, text="Tach数据控制", padding=5)
        
        # 风机选择
        fan_frame = ttk.Frame(self.tach_control_frame)
        fan_frame.pack(fill="x", pady=2)
        
        ttk.Label(fan_frame, text="监控风机:").pack(side="left")
        self.fan_selection_var = tk.StringVar(value="0,1,2,3")
        self.fan_entry = ttk.Entry(fan_frame, textvariable=self.fan_selection_var, width=15)
        self.fan_entry.pack(side="left", padx=5)
        ttk.Label(fan_frame, text="(逗号分隔)").pack(side="left")
        
        # 更新率控制
        rate_frame = ttk.Frame(self.tach_control_frame)
        rate_frame.pack(fill="x", pady=2)
        
        ttk.Label(rate_frame, text="更新率(Hz):").pack(side="left")
        self.update_rate_var = tk.DoubleVar(value=10.0)
        self.rate_scale = ttk.Scale(rate_frame, from_=1.0, to=50.0, 
                                   variable=self.update_rate_var, orient="horizontal")
        self.rate_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.rate_label = ttk.Label(rate_frame, text="10.0")
        self.rate_label.pack(side="left")
        
        # 控制按钮
        button_frame = ttk.Frame(self.tach_control_frame)
        button_frame.pack(fill="x", pady=5)
        
        self.start_button = ttk.Button(button_frame, text="开始监控", 
                                      command=self.toggle_monitoring)
        self.start_button.pack(side="left", padx=2)
        
        self.clear_button = ttk.Button(button_frame, text="清除数据", 
                                      command=self.clear_tach_data)
        self.clear_button.pack(side="left", padx=2)
        
        # 状态显示
        self.status_label = ttk.Label(self.tach_control_frame, text="状态: 等待监控")
        self.status_label.pack(pady=2)
        
        # 更新初始状态
        self.update_monitoring_status()
        
        # 绑定事件
        self.rate_scale.configure(command=self.on_rate_change)
        self.fan_entry.bind('<Return>', self.on_fan_selection_change)
     
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, 
                                   relief="sunken", anchor="w")
    
    def setup_layout(self):
        """设置布局"""
        self.main_frame.pack(fill="both", expand=True)
        
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
        
        # Tach控制面板
        self.tach_control_frame.pack(fill="x", pady=5)
        
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
        # 滤波方法变化时更新参数显示
        self.filter_method_var.trace('w', self.on_filter_method_change)
        
        # 绑定参数变化事件
        for var in [self.filter_type_var, self.filter_method_var, self.sampling_rate_var, 
                   self.cutoff_freq_var, self.order_var]:
            var.trace('w', self.update_plots)
             
        # 延迟初始化频率响应图，避免启动时卡顿
        self.after(1000, self.safe_update_plots)
    
    def on_filter_method_change(self, *args):
        """滤波方法变化时的回调"""
        method = self.filter_method_var.get()
        
        # 隐藏所有高级参数框架
        for frame in [self.kalman_frame, self.huber_frame, self.alpha_beta_frame]:
            frame.pack_forget()
        
        # 根据选择的方法显示相应的参数框架
        if method == "KALMAN":
            self.kalman_frame.pack(fill="x", pady=2)
        elif method == "HUBER_ROBUST":
            self.huber_frame.pack(fill="x", pady=2)
        elif method == "ALPHA_BETA":
            self.alpha_beta_frame.pack(fill="x", pady=2)
    
    def initialize_defaults(self):
        """初始化默认值"""
        self.on_filter_method_change()
        # 初始化滤波数据存储
        for fan_id in self.enabled_fans:
            if fan_id not in self.filtered_data:
                self.filtered_data[fan_id] = {
                    'timestamps': deque(maxlen=1000),
                    'filtered_rpm': deque(maxlen=1000)
                }
        
        # 如果monitoring组件已经在运行tach监控，启动滤波器更新
        if self.is_tach_monitoring_active():
            self.schedule_filter_update()
        
    def get_tach_data(self):
        """从monitoring组件获取tach数据"""
        if self.monitoring_widget and hasattr(self.monitoring_widget, 'tach_data'):
            return self.monitoring_widget.tach_data
        return {}
        
    def is_tach_monitoring_active(self):
        """检查tach监控是否激活"""
        if self.monitoring_widget and hasattr(self.monitoring_widget, 'tach_monitoring_active'):
            return self.monitoring_widget.tach_monitoring_active
        return False
        
    def start_tach_monitoring(self):
        """启动tach数据监控（通过monitoring组件）"""
        if self.monitoring_widget and hasattr(self.monitoring_widget, '_start_tach_monitoring'):
            if not self.is_tach_monitoring_active():
                self.monitoring_widget._start_tach_monitoring()
                self.printd("通过monitoring组件启动tach数据监控")
            # 启动滤波器数据更新循环
            self.schedule_filter_update()
        else:
            self.printw("无法启动tach监控：monitoring组件不可用")
            
    def stop_tach_monitoring(self):
        """停止tach数据监控（通过monitoring组件）"""
        if self.monitoring_widget and hasattr(self.monitoring_widget, '_stop_tach_monitoring'):
            self.monitoring_widget._stop_tach_monitoring()
            self.printd("通过monitoring组件停止tach数据监控")
        
    def schedule_filter_update(self):
        """调度滤波器数据更新"""
        if self.is_tach_monitoring_active():
            self.update_filtered_data()
            # 使用tkinter的after方法调度下次更新
            update_interval = int(1000 / self.update_rate)  # 转换为毫秒
            self.after(update_interval, self.schedule_filter_update)
            
    def update_filtered_data(self):
        """更新滤波后的数据"""
        try:
            # 获取monitoring组件的tach数据
            tach_data = self.get_tach_data()
            
            if tach_data:
                # 应用滤波器到tach数据
                self._apply_current_filter(tach_data)
                
                # 更新显示
                self._update_tach_plots()
            
        except Exception as e:
            self.printd(f"滤波数据更新错误: {e}")
            
    def _apply_current_filter(self, tach_data=None):
        """应用当前滤波器设置"""
        try:
            # 获取当前滤波器配置
            config = self.get_current_config()
            filter_type = config['filter_type']
            
            # 如果没有传入tach_data，从monitoring组件获取
            if tach_data is None:
                tach_data = self.get_tach_data()
            
            if not tach_data:
                self.printd("无可用的tach数据进行滤波")
                return
            
            for fan_id in self.enabled_fans:
                if fan_id in tach_data and tach_data[fan_id].get('raw_signals'):
                    raw_signals = tach_data[fan_id]['raw_signals']
                    timestamps = tach_data[fan_id]['timestamps']
                    
                    # 验证数据有效性
                    if not raw_signals or not timestamps or len(raw_signals) != len(timestamps):
                        self.printd(f"Fan {fan_id}: 数据无效或长度不匹配")
                        continue
                    
                    # 转换为列表并验证数据类型
                    try:
                        raw_signals = [float(x) for x in raw_signals if x is not None]
                        timestamps = [float(t) for t in timestamps if t is not None]
                        
                        if len(raw_signals) < 2:
                            self.printd(f"Fan {fan_id}: 数据点不足，跳过滤波")
                            continue
                            
                    except (ValueError, TypeError) as e:
                        self.printd(f"Fan {fan_id}: 数据类型转换错误: {e}")
                        continue
                    
                    # 应用滤波器到原始信号
                    filtered_rpm = self._apply_filter_to_signal(raw_signals, filter_type, config)
                    
                    if filtered_rpm:
                        # 存储滤波后的数据
                        if fan_id not in self.filtered_data:
                            self.filtered_data[fan_id] = {
                                'timestamps': deque(maxlen=1000),
                                'filtered_rpm': deque(maxlen=1000)
                            }
                        
                        self.filtered_data[fan_id]['timestamps'] = deque(timestamps, maxlen=1000)
                        self.filtered_data[fan_id]['filtered_rpm'] = deque(filtered_rpm, maxlen=1000)
                        
        except Exception as e:
            self.printd(f"滤波器应用错误: {e}")
            import traceback
            self.printd(f"详细错误信息: {traceback.format_exc()}")
            
    def _apply_filter_to_signal(self, signal, filter_type, config):
        """对信号应用滤波器"""
        if not signal or len(signal) < 2:
            self.printd("信号数据不足，无法进行滤波")
            return signal
            
        try:
            # 验证信号数据
            if not all(isinstance(x, (int, float)) and not (isinstance(x, float) and (x != x or abs(x) == float('inf'))) for x in signal):
                self.printd("信号包含无效数值（NaN或Inf），跳过滤波")
                return signal
            
            signal_data = np.array(signal)
            
            if filter_type == "moving_average":
                window_size = max(1, min(config.get('window_size', 5), len(signal)))
                filtered = []
                for i in range(len(signal)):
                    start_idx = max(0, i - window_size + 1)
                    window = signal[start_idx:i+1]
                    if window:  # 确保窗口不为空
                        filtered.append(sum(window) / len(window))
                    else:
                        filtered.append(signal[i])
                return filtered
            else:
                # 使用设计的滤波器进行滤波
                b, a = self.design_filter(config)
                
                if b is not None and a is not None:
                    try:
                        # 使用filtfilt进行零相位滤波
                        filtered_signal = signal.filtfilt(b, a, signal_data)
                        return filtered_signal.tolist()
                    except Exception as filter_error:
                        self.printd(f"filtfilt失败，使用lfilter: {filter_error}")
                        try:
                            # 如果filtfilt失败，使用普通滤波
                            filtered_signal = signal.lfilter(b, a, signal_data)
                            return filtered_signal.tolist()
                        except Exception as lfilter_error:
                            self.printd(f"lfilter也失败: {lfilter_error}")
                            return signal
                else:
                    self.printd("滤波器设计失败，使用原始信号")
                    return signal
                
        except Exception as e:
            self.printd(f"滤波器计算错误: {e}")
            import traceback
            self.printd(f"详细错误: {traceback.format_exc()}")
            return signal
            
    def _update_tach_plots(self):
        """更新tach数据图表"""
        try:
            if hasattr(self, 'time_canvas') and self.time_canvas:
                # 清除当前图表
                self.time_ax.clear()
                self.time_ax.set_title('实时Tach信号监控', fontsize=12)
                self.time_ax.set_xlabel('时间 (s)')
                self.time_ax.set_ylabel('RPM')
                self.time_ax.grid(True, alpha=0.3)
                
                # 获取monitoring组件的tach数据
                tach_data = self.get_tach_data()
                
                # 绘制原始和滤波后的数据
                colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
                
                for i, fan_id in enumerate(self.enabled_fans[:4]):  # 最多显示4个风机
                    if fan_id in tach_data and tach_data[fan_id]['timestamps']:
                        timestamps = list(tach_data[fan_id]['timestamps'])
                        raw_signals = list(tach_data[fan_id]['raw_signals'])  # 使用原始信号
                        
                        # 转换为相对时间
                        if timestamps:
                            base_time = timestamps[0]
                            rel_times = [(t - base_time) for t in timestamps]
                            
                            color = colors[i % len(colors)]
                            
                            # 绘制原始raw signal数据
                            self.time_ax.plot(rel_times, raw_signals, 
                                            color=color, alpha=0.5, linewidth=1,
                                            label=f'Fan {fan_id} 原始')
                            
                            # 绘制滤波后的数据
                            if fan_id in self.filtered_data and self.filtered_data[fan_id]['filtered_rpm']:
                                filtered_rpm = list(self.filtered_data[fan_id]['filtered_rpm'])
                                self.time_ax.plot(rel_times, filtered_rpm,
                                                color=color, linewidth=2,
                                                label=f'Fan {fan_id} 滤波')
                
                # 只有当有数据绘制时才显示图例
                handles, labels = self.time_ax.get_legend_handles_labels()
                if handles:
                    self.time_ax.legend()
                self.time_canvas.draw()
                
        except Exception as e:
            self.printd(f"图表更新错误: {e}")
            
    def on_rate_change(self, value):
        """更新率变化事件"""
        rate = float(value)
        self.rate_label.config(text=f"{rate:.1f}")
        self.update_rate = rate
        
    def on_fan_selection_change(self, event=None):
        """风机选择变化事件"""
        try:
            fan_str = self.fan_selection_var.get()
            fan_ids = [int(x.strip()) for x in fan_str.split(',') if x.strip().isdigit()]
            
            # 验证风机ID范围
            valid_fans = [fid for fid in fan_ids if 0 <= fid < 32]
            if valid_fans != fan_ids:
                self.printw(f"无效的风机ID已被过滤，有效范围: 0-31")
            
            self.enabled_fans = valid_fans
            
            # 同步更新monitoring组件的enabled_fans配置
            if self.monitoring_widget and hasattr(self.monitoring_widget, 'tach_config'):
                # 保持monitoring组件的完整配置，只更新filter_config关心的风机
                # 这样不会影响monitoring组件的其他风机监控
                pass
            
            # 重新初始化滤波数据存储
            for fan_id in self.enabled_fans:
                if fan_id not in self.filtered_data:
                    self.filtered_data[fan_id] = {
                        'timestamps': deque(maxlen=1000),
                        'filtered_rpm': deque(maxlen=1000)
                    }
            
            self.printd(f"滤波器监控风机已更新: {self.enabled_fans}")
            
        except Exception as e:
            self.printw(f"风机选择格式错误: {e}")
            self.enabled_fans = [0, 1, 2, 3]  # 默认值
            
    def update_monitoring_status(self):
        """更新监控状态显示"""
        if self.is_tach_monitoring_active():
            self.start_button.config(text="停止监控")
            self.status_label.config(text="状态: 监控中")
        else:
            self.start_button.config(text="开始监控")
            self.status_label.config(text="状态: 已停止")
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_tach_monitoring_active():
            self.stop_tach_monitoring()
        else:
            self.start_tach_monitoring()
        
        # 更新状态显示
        self.update_monitoring_status()
            
    def clear_tach_data(self):
        """清除tach数据"""
        # 清除滤波数据
        for fan_id in self.enabled_fans:
            if fan_id in self.filtered_data:
                self.filtered_data[fan_id]['timestamps'].clear()
                self.filtered_data[fan_id]['filtered_rpm'].clear()
        
        # 清除monitoring组件的tach数据
        if self.monitoring_widget and hasattr(self.monitoring_widget, 'tach_data'):
            for fan_id in self.monitoring_widget.tach_data:
                self.monitoring_widget.tach_data[fan_id]['timestamps'].clear()
                self.monitoring_widget.tach_data[fan_id]['rpm_values'].clear()
                self.monitoring_widget.tach_data[fan_id]['filtered_rpm'].clear()
                self.monitoring_widget.tach_data[fan_id]['duty_cycles'].clear()
                self.monitoring_widget.tach_data[fan_id]['timeouts'].clear()
                self.monitoring_widget.tach_data[fan_id]['raw_signals'].clear()
        
        # 清除图表
        self.time_ax.clear()
        self.time_ax.set_xlabel("时间 (s)")
        self.time_ax.set_ylabel("RPM")
        self.time_ax.set_title("实时Tach信号监控")
        self.time_ax.grid(True, alpha=0.3)
        self.time_canvas.draw()
        
        self.printd("已清除tach数据")
        
        self.update_plots()
    
    def design_filter(self, config):
        """设计滤波器"""
        try:
            # 检查scipy是否可用
            if not SCIPY_AVAILABLE or signal is None:
                return None, None
                
            filter_type = config['filter_type']
            filter_method = config['filter_method']
            fs = float(config['sampling_rate'])
            fc = float(config['cutoff_frequency'])
            order = int(config['order'])
            
            # 参数验证
            if fs <= 0 or fc <= 0 or order <= 0:
                return None, None
                
            # 归一化截止频率
            nyquist = fs / 2
            normalized_fc = fc / nyquist
            
            if normalized_fc >= 1.0:
                normalized_fc = 0.99
                if hasattr(self, 'printw'):
                    self.printw(f"截止频率已调整为 {normalized_fc * nyquist:.1f} Hz")
            
            if normalized_fc <= 0:
                normalized_fc = 0.01
                
            # 限制阶数以避免数值问题
            order = min(order, 10)
            
            # 根据滤波器类型和方法设计滤波器
            if filter_method in ['BUTTERWORTH', 'IIR']:
                if filter_type == 'LOWPASS':
                    b, a = signal.butter(order, normalized_fc, btype='low')
                elif filter_type == 'HIGHPASS':
                    b, a = signal.butter(order, normalized_fc, btype='high')
                elif filter_type == 'BANDPASS':
                    # 对于带通滤波器，需要两个截止频率
                    fc_low = max(0.01, normalized_fc - 0.1)
                    fc_high = min(0.99, normalized_fc + 0.1)
                    if fc_low >= fc_high:
                        fc_low = normalized_fc * 0.8
                        fc_high = normalized_fc * 1.2
                    b, a = signal.butter(order, [fc_low, fc_high], btype='band')
                elif filter_type == 'BANDSTOP':
                    fc_low = max(0.01, normalized_fc - 0.1)
                    fc_high = min(0.99, normalized_fc + 0.1)
                    if fc_low >= fc_high:
                        fc_low = normalized_fc * 0.8
                        fc_high = normalized_fc * 1.2
                    b, a = signal.butter(order, [fc_low, fc_high], btype='bandstop')
                else:
                    # 默认低通
                    b, a = signal.butter(order, normalized_fc, btype='low')
                    
            elif filter_method == 'CHEBYSHEV1':
                ripple = 1.0  # 1dB ripple
                if filter_type == 'LOWPASS':
                    b, a = signal.cheby1(order, ripple, normalized_fc, btype='low')
                elif filter_type == 'HIGHPASS':
                    b, a = signal.cheby1(order, ripple, normalized_fc, btype='high')
                else:
                    b, a = signal.cheby1(order, ripple, normalized_fc, btype='low')
                    
            elif filter_method == 'FIR':
                # FIR滤波器设计，限制长度以提高性能
                fir_length = min(order + 1, 101)  # 限制FIR长度
                if filter_type == 'LOWPASS':
                    b = signal.firwin(fir_length, normalized_fc, window='hamming')
                elif filter_type == 'HIGHPASS':
                    b = signal.firwin(fir_length, normalized_fc, window='hamming', pass_zero=False)
                else:
                    b = signal.firwin(fir_length, normalized_fc, window='hamming')
                a = [1.0]  # FIR滤波器的分母系数
                
            else:
                # 默认Butterworth低通滤波器
                b, a = signal.butter(order, normalized_fc, btype='low')
                
            return b, a
            
        except ImportError:
            # scipy不可用
            return None, None
        except Exception as e:
            if hasattr(self, 'printd'):
                self.printd(f"滤波器设计错误: {e}")
            return None, None
    
    def safe_update_plots(self):
        """安全的图形更新，用于延迟初始化"""
        try:
            self.update_plots()
        except Exception as e:
            if hasattr(self, 'printd'):
                self.printd(f"延迟初始化频率响应失败: {e}")
            # 静默失败，不影响程序启动
            pass
    
    def update_plots(self, *args):
        """更新图形显示"""
        try:
            # 检查必要的组件是否存在
            if not hasattr(self, 'freq_ax') or not hasattr(self, 'freq_canvas'):
                return
                
            config = self.get_current_config()
            
            # 设计滤波器
            b, a = self.design_filter(config)
            
            if b is not None and a is not None:
                # 计算频率响应
                w, h = signal.freqz(b, a, worN=1024, fs=config['sampling_rate'])  # 减少计算量
                
                # 更新频率响应图
                self.freq_ax.clear()
                
                # 幅度响应（dB）
                magnitude_db = 20 * np.log10(np.abs(h) + 1e-10)
                self.freq_ax.plot(w, magnitude_db, 'b-', linewidth=2)
                
                # 添加截止频率线
                self.freq_ax.axvline(config['cutoff_frequency'], color='r', 
                                   linestyle='--', alpha=0.7, label=f"fc = {config['cutoff_frequency']:.1f} Hz")
                
                # 添加-3dB线
                self.freq_ax.axhline(-3, color='g', linestyle=':', alpha=0.7, label='-3dB')
                
                self.freq_ax.set_xlabel('频率 (Hz)')
                self.freq_ax.set_ylabel('幅度 (dB)')
                self.freq_ax.set_title(f'{config["filter_type"]} {config["filter_method"]} 滤波器频率响应')
                self.freq_ax.grid(True, alpha=0.3)
                self.freq_ax.legend()
                
                # 设置合理的y轴范围
                self.freq_ax.set_ylim([-60, 5])
                
                # 设置x轴范围
                self.freq_ax.set_xlim([0, config['sampling_rate'] / 2])
                
                self.freq_canvas.draw()
                
                self.status_var.set(f"频率响应已更新 - {config['filter_type']} {config['filter_method']}")
            else:
                # 如果滤波器设计失败，显示空图表
                self.freq_ax.clear()
                self.freq_ax.set_xlabel('频率 (Hz)')
                self.freq_ax.set_ylabel('幅度 (dB)')
                self.freq_ax.set_title('频率响应 - 等待配置')
                self.freq_ax.grid(True, alpha=0.3)
                self.freq_canvas.draw()
                self.status_var.set("等待滤波器配置")
                
        except ImportError as e:
            # scipy导入失败的情况
            if hasattr(self, 'printd'):
                self.printd(f"scipy导入失败: {e}")
            self.status_var.set("频率响应功能不可用 - 缺少scipy")
        except Exception as e:
            if hasattr(self, 'printd'):
                self.printd(f"图形更新错误: {e}")
            self.status_var.set(f"更新失败: {e}")
    
    def apply_filter(self):
        """应用滤波器"""
        try:
            config = self.get_current_config()
            
            # 更新频率响应图
            self.update_plots()
            
            # 应用滤波器到当前数据
            self._apply_current_filter()
            
            self.status_var.set(f"滤波器已应用 - {config['filter_type']} {config['filter_method']}")
            
            if hasattr(self, 'printd'):
                self.printd(f"应用滤波器配置: {config}")
                
        except Exception as e:
            if hasattr(self, 'printd'):
                self.printd(f"滤波器应用错误: {e}")
            self.status_var.set(f"应用失败: {e}")
            messagebox.showerror("错误", f"应用滤波器失败: {e}")
    
    def reset_config(self):
        """重置配置"""
        self.filter_type_var.set("LOWPASS")
        self.filter_method_var.set("BUTTERWORTH")
        self.sampling_rate_var.set("1000")
        self.cutoff_freq_var.set("100")
        self.order_var.set("4")
        self.process_noise_var.set("0.01")
        self.observation_noise_var.set("0.1")
        self.huber_threshold_var.set("1.345")
        self.huber_window_var.set("10")
        self.alpha_var.set("0.8")
        self.beta_var.set("0.2")
        self.status_var.set("配置已重置")
    
    def save_config(self):
        """保存配置"""
        try:
            config = self.get_current_config()
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self.status_var.set(f"配置已保存到 {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_config(self):
        """加载配置"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.set_config(config)
                self.status_var.set(f"配置已从 {filename} 加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
    
    def get_current_config(self):
        """获取当前配置"""
        try:
            config = {
                'filter_type': self.filter_type_var.get(),
                'filter_method': self.filter_method_var.get(),
                'sampling_rate': max(1.0, float(self.sampling_rate_var.get())),
                'cutoff_frequency': max(0.1, float(self.cutoff_freq_var.get())),
                'order': max(1, min(20, int(self.order_var.get()))),
                'process_noise': max(0.001, float(self.process_noise_var.get())),
                'observation_noise': max(0.001, float(self.observation_noise_var.get())),
                'huber_threshold': max(0.1, float(self.huber_threshold_var.get())),
                'huber_window_size': max(1, min(100, int(self.huber_window_var.get()))),
                'alpha_factor': max(0.0, min(1.0, float(self.alpha_var.get()))),
                'beta_factor': max(0.0, min(1.0, float(self.beta_var.get())))
            }
            
            # 验证奈奎斯特频率
            if config['cutoff_frequency'] >= config['sampling_rate'] / 2:
                config['cutoff_frequency'] = config['sampling_rate'] / 2 - 1
                self.printw(f"截止频率已调整为 {config['cutoff_frequency']:.1f} Hz (奈奎斯特频率限制)")
            
            return config
        except ValueError as e:
            self.printw(f"配置参数错误: {e}，使用默认值")
            return {
                'filter_type': 'LOWPASS',
                'filter_method': 'BUTTERWORTH',
                'sampling_rate': 1000.0,
                'cutoff_frequency': 100.0,
                'order': 4,
                'process_noise': 0.01,
                'observation_noise': 0.1,
                'huber_threshold': 1.345,
                'huber_window_size': 10,
                'alpha_factor': 0.8,
                'beta_factor': 0.2
            }
    
    def set_config(self, config):
        """设置配置"""
        self.filter_type_var.set(config.get('filter_type', 'LOWPASS'))
        self.filter_method_var.set(config.get('filter_method', 'BUTTERWORTH'))
        self.sampling_rate_var.set(str(config.get('sampling_rate', 1000)))
        self.cutoff_freq_var.set(str(config.get('cutoff_frequency', 100)))
        self.order_var.set(str(config.get('order', 4)))
        self.process_noise_var.set(str(config.get('process_noise', 0.01)))
        self.observation_noise_var.set(str(config.get('observation_noise', 0.1)))
        self.huber_threshold_var.set(str(config.get('huber_threshold', 1.345)))
        self.huber_window_var.set(str(config.get('huber_window_size', 10)))
        self.alpha_var.set(str(config.get('alpha_factor', 0.8)))
        self.beta_var.set(str(config.get('beta_factor', 0.2)))
        
        # 更新参数显示
        self.on_filter_method_change()
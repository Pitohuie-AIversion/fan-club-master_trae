################################################################################
## Project: Fanclub Mark IV "Master"  ## File: monitoring.py                ##
##----------------------------------------------------------------------------##
##                        WESTLAKE UNIVERSITY                                ##
##                   ADVANCED SYSTEMS LABORATORY                            ##
##----------------------------------------------------------------------------##
##                                                                            ##
##                    ██╗    ██╗███████╗███████╗████████╗                   ##
##                    ██║    ██║██╔════╝██╔════╝╚══██╔══╝                   ##
##                    ██║ █╗ ██║█████╗  ███████╗   ██║                      ##
##                    ██║███╗██║██╔══╝  ╚════██║   ██║                      ##
##                    ╚███╔███╔╝███████╗███████║   ██║                      ##
##                     ╚══╝╚══╝ ╚══════╝╚══════╝   ╚═╝                      ##
##                                                                            ##
##                         LAKE SYSTEMS LABORATORY                          ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Authors: zhaoyang, dashuai                                                ##
## Email: mzymuzhaoyang@gmail.com, dschen2018@gmail.com                     ##
## Date: 2024                                                                ##
## Version: 1.0                                                              ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Data monitoring and visualization interface component
 + Provides real-time signal monitoring, data visualization and system status display
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk
import threading
import time
import queue
import math
import numpy as np
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import sys
import os

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from fc import printer as pt
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.theme import SURFACE_1, SURFACE_2, SURFACE_3, TEXT_PRIMARY, TEXT_SECONDARY, PRIMARY_500, SUCCESS_MAIN, WARNING_MAIN, ERROR_MAIN
from fc.backend.signal_acquisition import SignalAcquisitionEngine, AcquisitionConfig, ChannelConfig

# Try to import FCCommunicator for real Tach data
try:
    from fc.backend.mkiii import FCCommunicator as fcc
    FC_COMM_AVAILABLE = True
except ImportError:
    FC_COMM_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

## GLOBALS ### CONSTANTS ####################################################################
MAX_DATA_POINTS = 100  # Maximum data points
UPDATE_INTERVAL = 500  # Update interval (ms) - 优化：从100ms增加到500ms减少CPU占用
CHANNEL_COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4']
TACH_COLORS = ['#E91E63', '#9C27B0', '#673AB7', '#3F51B5', '#2196F3', '#00BCD4']
MAX_TACH_FANS = 29  # Maximum number of fans
TACH_FILTER_WINDOW = 10  # Filter window size

## TACH DATA STRUCTURES ##########################################################
@dataclass
class TachReading:
    """Tach signal reading data structure"""
    fan_id: int
    rpm: float
    timestamp: float
    duty_cycle: float = 0.0
    timeout: bool = False
    raw_signal: float = 0.0  # Raw tach pulse signal value
    
@dataclass
class TachSignalConfig:
    """Tach signal configuration"""
    enabled_fans: List[int]
    filter_enabled: bool = True
    filter_type: str = "moving_average"  # moving_average, low_pass
    filter_window: int = TACH_FILTER_WINDOW
    update_rate: float = 10.0  # Hz
    rpm_threshold: float = 100.0  # Minimum valid RPM
    show_raw_signal: bool = False  # Show raw tach signal data
    enable_simulation: bool = False  # Enable/disable simulated data generation
    simulation_diagnostics: bool = False  # Enable/disable diagnostics for simulated data

################################################################################
class MonitoringWidget(ttk.Frame, pt.PrintClient):
    """Main data monitoring and visualization component"""
    
    SYMBOL = "[MON]"
    
    def __init__(self, master, archive, pqueue):
        """
        Create monitoring interface component
        
        Parameters:
        - master: Parent container
        - archive: Configuration archive manager
        - pqueue: Print queue
        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue, self.SYMBOL)
        
        self.archive = archive
        self.pqueue = pqueue
        
        # Data storage
        self.signal_data = {}
        self.system_stats = {
            'cpu_usage': deque(maxlen=MAX_DATA_POINTS),
            'memory_usage': deque(maxlen=MAX_DATA_POINTS),
            'network_packets': deque(maxlen=MAX_DATA_POINTS),
            'timestamps': deque(maxlen=MAX_DATA_POINTS)
        }
        
        # Tach signal data storage
        self.tach_data = {}
        self.tach_config = TachSignalConfig(
            enabled_fans=list(range(MAX_TACH_FANS)),
            filter_enabled=True,
            filter_type="moving_average",
            filter_window=TACH_FILTER_WINDOW,
            show_raw_signal=True,
            enable_simulation=False,  # Disable simulation by default
            simulation_diagnostics=False  # Disable simulation diagnostics by default
        )
        self.tach_filters = {}  # Filter states
        self.fc_communicator = None
        
        # Monitoring status
        self.monitoring_active = False
        self.signal_system = None
        self.update_thread = None
        self.tach_monitoring_active = False
        
        # Signal acquisition engine
        self.acquisition_engine = SignalAcquisitionEngine(pqueue)
        self.acquisition_config = AcquisitionConfig()
        self.acquisition_config.sampling_rate = 1000.0
        self.acquisition_config.channels = [0, 1, 2]  # 3 channels
        self.acquisition_engine.configure(self.acquisition_config)
        
        # Register data callback
        self.acquisition_engine.add_data_callback(self._on_signal_data_received)
        
        # Build interface
        self._build_interface()
        
        # Start data updates
        self._start_monitoring()
    
    def _build_interface(self):
        """Build monitoring interface"""
        # Main container configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top control bar
        self._build_control_bar()
        
        # Main content area
        self._build_main_content()
        
        # Bottom status bar
        self._build_status_bar()
    
    def _build_control_bar(self):
        """Build control bar"""
        control_frame = ttk.Frame(self, style="Toolbar.TFrame")
        control_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Monitoring control button
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", 
                                     command=self._toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        
        # Status indicator
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=0, column=1, sticky='e', padx=10)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=5)
        self.status_label = ttk.Label(status_frame, text="Stopped", 
                                    foreground=ERROR_MAIN)
        self.status_label.grid(row=0, column=1, padx=5)
        
        # Clear data button
        self.clear_button = ttk.Button(control_frame, text="Clear Data", 
                                     command=self._clear_data)
        self.clear_button.grid(row=0, column=2, padx=5)
    
    def _build_main_content(self):
        """Build main content area"""
        # Create notebook container
        self.content_notebook = ttk.Notebook(self)
        self.content_notebook.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        # Signal monitoring tab
        self._build_signal_tab()
        
        # Tach signal monitoring tab
        self._build_tach_tab()
        
        # System status tab
        self._build_system_tab()
        
        # Data statistics tab
        self._build_statistics_tab()
    
    def _build_signal_tab(self):
        """Build signal monitoring tab"""
        signal_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(signal_frame, text="Signal Monitor")
        
        signal_frame.grid_columnconfigure(0, weight=1)
        signal_frame.grid_rowconfigure(1, weight=1)
        
        # Signal control panel
        signal_control = ttk.LabelFrame(signal_frame, text="Signal Control", padding=10)
        signal_control.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        
        # Channel selection
        ttk.Label(signal_control, text="Monitor Channel:").grid(row=0, column=0, padx=5)
        self.channel_var = tk.StringVar(value="All")
        channel_combo = ttk.Combobox(signal_control, textvariable=self.channel_var,
                                   values=["All", "Channel 1", "Channel 2", "Channel 3"],
                                   state="readonly")
        channel_combo.grid(row=0, column=1, padx=5)
        
        # Sampling rate setting
        ttk.Label(signal_control, text="Sample Rate (Hz):").grid(row=0, column=2, padx=5)
        self.sample_rate_var = tk.StringVar(value="1000")
        sample_rate_entry = ttk.Entry(signal_control, textvariable=self.sample_rate_var, width=10)
        sample_rate_entry.grid(row=0, column=3, padx=5)
        
        # Signal display area
        if MATPLOTLIB_AVAILABLE:
            self._build_signal_plot(signal_frame)
        else:
            self._build_signal_text(signal_frame)
    
    def _build_signal_plot(self, parent):
        """Build signal plot display"""
        plot_frame = ttk.LabelFrame(parent, text="Real-time Signal Waveform", padding=10)
        plot_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)
        
        # Create matplotlib chart
        self.signal_fig = Figure(figsize=(10, 6), dpi=100, facecolor=SURFACE_1)
        self.signal_ax = self.signal_fig.add_subplot(111)
        self.signal_ax.set_facecolor(SURFACE_2)
        self.signal_ax.set_title('Real-time Signal Monitoring', color=TEXT_PRIMARY)
        self.signal_ax.set_xlabel('Time (s)', color=TEXT_PRIMARY)
        self.signal_ax.set_ylabel('Signal Amplitude', color=TEXT_PRIMARY)
        self.signal_ax.tick_params(colors=TEXT_PRIMARY)
        
        # Initialize signal lines
        self.signal_lines = []
        for i in range(3):  # 3 channels
            line, = self.signal_ax.plot([], [], color=CHANNEL_COLORS[i], 
                                      label=f'Channel {i+1}', linewidth=2)
            self.signal_lines.append(line)
        
        self.signal_ax.legend()
        self.signal_ax.grid(True, alpha=0.3)
        
        # Embed into tkinter
        self.signal_canvas = FigureCanvasTkAgg(self.signal_fig, plot_frame)
        self.signal_canvas.draw()
        self.signal_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
    
    def _build_signal_text(self, parent):
        """Build text-based signal display (fallback when matplotlib unavailable)"""
        text_frame = ttk.LabelFrame(parent, text="Signal Data", padding=10)
        text_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        # Create text display area
        self.signal_text = tk.Text(text_frame, height=15, bg=SURFACE_2, fg=TEXT_PRIMARY)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.signal_text.yview)
        self.signal_text.configure(yscrollcommand=scrollbar.set)
        
        self.signal_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
    
    def _build_tach_tab(self):
        """Build Tach signal monitoring tab"""
        tach_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(tach_frame, text="Fan Speed (Tach)")
        
        tach_frame.grid_columnconfigure(0, weight=1)
        tach_frame.grid_rowconfigure(2, weight=1)
        
        # Tach control panel
        self._build_tach_control_panel(tach_frame)
        
        # Tach status display panel
        self._build_tach_status_panel(tach_frame)
        
        # Tach data display area
        if MATPLOTLIB_AVAILABLE:
            self._build_tach_plot(tach_frame)
        else:
            self._build_tach_text(tach_frame)
    
    def _build_tach_control_panel(self, parent):
        """Build Tach control panel"""
        control_frame = ttk.LabelFrame(parent, text="Tach Signal Control", padding=10)
        control_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        control_frame.grid_columnconfigure(3, weight=1)
        
        # Tach monitoring switch
        self.tach_monitor_var = tk.BooleanVar(value=False)
        tach_check = ttk.Checkbutton(control_frame, text="Enable Tach Monitoring", 
                                   variable=self.tach_monitor_var,
                                   command=self._toggle_tach_monitoring)
        tach_check.grid(row=0, column=0, padx=5, sticky='w')
        
        # Filter settings
        ttk.Label(control_frame, text="Filter Type:").grid(row=0, column=1, padx=5)
        self.filter_type_var = tk.StringVar(value="moving_average")
        filter_combo = ttk.Combobox(control_frame, textvariable=self.filter_type_var,
                                  values=["moving_average", "low_pass", "none"],
                                  state="readonly", width=12)
        filter_combo.grid(row=0, column=2, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self._on_filter_type_changed)
        
        # Filter window size
        ttk.Label(control_frame, text="Filter Window:").grid(row=0, column=3, padx=5)
        self.filter_window_var = tk.StringVar(value=str(TACH_FILTER_WINDOW))
        filter_window_entry = ttk.Entry(control_frame, textvariable=self.filter_window_var, width=8)
        filter_window_entry.grid(row=0, column=4, padx=5)
        filter_window_entry.bind('<Return>', self._on_filter_window_changed)
        
        # RPM threshold setting
        ttk.Label(control_frame, text="RPM Threshold:").grid(row=0, column=5, padx=5)
        self.rpm_threshold_var = tk.StringVar(value="100")
        rpm_threshold_entry = ttk.Entry(control_frame, textvariable=self.rpm_threshold_var, width=8)
        rpm_threshold_entry.grid(row=0, column=6, padx=5)
        rpm_threshold_entry.bind('<Return>', self._on_rpm_threshold_changed)
    
    def _build_tach_status_panel(self, parent):
        """Build Tach status display panel"""
        status_frame = ttk.LabelFrame(parent, text="Tach Status Overview", padding=10)
        status_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        
        # Create status display grid
        self.tach_status_labels = {}
        for i in range(6):  # Display status of first 6 fans
            fan_frame = ttk.Frame(status_frame)
            fan_frame.grid(row=0, column=i, padx=10, pady=5)
            
            ttk.Label(fan_frame, text=f"Fan {i+1}", font=('Arial', 8, 'bold')).pack()
            
            rpm_label = ttk.Label(fan_frame, text="0 RPM", foreground=TEXT_SECONDARY)
            rpm_label.pack()
            
            status_label = ttk.Label(fan_frame, text="Offline", foreground=ERROR_MAIN)
            status_label.pack()
            
            self.tach_status_labels[i] = {
                'rpm': rpm_label,
                'status': status_label
            }
    
    def _build_tach_plot(self, parent):
        """Build Tach signal plot display"""
        plot_frame = ttk.LabelFrame(parent, text="Tach Signal Real-time Waveform", padding=10)
        plot_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)
        
        # Create matplotlib chart
        self.tach_fig = Figure(figsize=(12, 14), dpi=100, facecolor=SURFACE_1)
        
        # Create subplots: Raw signal, RPM time series and RPM distribution
        self.tach_ax_raw = self.tach_fig.add_subplot(311)  # Raw signal plot
        self.tach_ax1 = self.tach_fig.add_subplot(312)     # RPM time series
        self.tach_ax2 = self.tach_fig.add_subplot(313)     # RPM distribution
        
        # Adjust subplot spacing
        self.tach_fig.subplots_adjust(hspace=0.4, top=0.95, bottom=0.08)
        
        # Raw signal plot
        self.tach_ax_raw.set_facecolor(SURFACE_2)
        self.tach_ax_raw.set_title('Raw Tach Signal Monitoring', color=TEXT_PRIMARY, fontsize=12)
        self.tach_ax_raw.set_xlabel('Time (s)', color=TEXT_PRIMARY)
        self.tach_ax_raw.set_ylabel('Signal Amplitude', color=TEXT_PRIMARY)
        self.tach_ax_raw.tick_params(colors=TEXT_PRIMARY)
        self.tach_ax_raw.grid(True, alpha=0.3)
        
        # RPM time series plot
        self.tach_ax1.set_facecolor(SURFACE_2)
        self.tach_ax1.set_title('Fan Speed Real-time Monitoring', color=TEXT_PRIMARY, fontsize=12)
        self.tach_ax1.set_xlabel('Time (s)', color=TEXT_PRIMARY)
        self.tach_ax1.set_ylabel('Speed (RPM)', color=TEXT_PRIMARY)
        self.tach_ax1.tick_params(colors=TEXT_PRIMARY)
        self.tach_ax1.grid(True, alpha=0.3)
        
        # RPM distribution bar chart
        self.tach_ax2.set_facecolor(SURFACE_2)
        self.tach_ax2.set_title('Current Speed Distribution', color=TEXT_PRIMARY, fontsize=12)
        self.tach_ax2.set_xlabel('Fan Number', color=TEXT_PRIMARY)
        self.tach_ax2.set_ylabel('Speed (RPM)', color=TEXT_PRIMARY)
        self.tach_ax2.tick_params(colors=TEXT_PRIMARY)
        self.tach_ax2.grid(True, alpha=0.3, axis='y')
        
        # Initialize Tach signal lines
        self.tach_lines = {}
        self.tach_bars = None
        
        # Embed into tkinter
        self.tach_canvas = FigureCanvasTkAgg(self.tach_fig, plot_frame)
        self.tach_canvas.draw()
        self.tach_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
    
    def _build_tach_text(self, parent):
        """Build text-based Tach signal display (fallback when matplotlib is unavailable)"""
        text_frame = ttk.LabelFrame(parent, text="Tach Signal Data", padding=10)
        text_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        # Create text display area
        self.tach_text = tk.Text(text_frame, height=20, bg=SURFACE_2, fg=TEXT_PRIMARY,
                               font=('Consolas', 10))
        tach_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.tach_text.yview)
        self.tach_text.configure(yscrollcommand=tach_scrollbar.set)
        
        self.tach_text.grid(row=0, column=0, sticky='nsew')
        tach_scrollbar.grid(row=0, column=1, sticky='ns')
    
    def _build_system_tab(self):
        """Build system status tab"""
        system_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(system_frame, text="System Status")
        
        system_frame.grid_columnconfigure(0, weight=1)
        system_frame.grid_columnconfigure(1, weight=1)
        system_frame.grid_rowconfigure(1, weight=1)
        
        # System information panel
        info_frame = ttk.LabelFrame(system_frame, text="System Information", padding=10)
        info_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # System information labels
        self.system_info_labels = {}
        info_items = [
            ('Runtime', '00:00:00'),
            ('CPU Usage', '0%'),
            ('Memory Usage', '0 MB'),
            ('Network Packets', '0'),
            ('Connected Devices', '0'),
            ('Packets/sec', '0')
        ]
        
        for i, (label, value) in enumerate(info_items):
            row, col = i // 3, (i % 3) * 2
            ttk.Label(info_frame, text=f"{label}:").grid(row=row, column=col, sticky='w', padx=5, pady=2)
            value_label = ttk.Label(info_frame, text=value, foreground=PRIMARY_500)
            value_label.grid(row=row, column=col+1, sticky='w', padx=5, pady=2)
            self.system_info_labels[label] = value_label
        
        # Performance chart
        if MATPLOTLIB_AVAILABLE:
            self._build_performance_plot(system_frame)
        else:
            self._build_performance_text(system_frame)
    
    def _build_performance_plot(self, parent):
        """Build performance chart"""
        plot_frame = ttk.LabelFrame(parent, text="Performance Monitoring", padding=10)
        plot_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)
        
        # Create performance chart
        self.perf_fig = Figure(figsize=(10, 4), dpi=100, facecolor=SURFACE_1)
        self.perf_ax = self.perf_fig.add_subplot(111)
        self.perf_ax.set_facecolor(SURFACE_2)
        self.perf_ax.set_title('System Performance Monitoring', color=TEXT_PRIMARY)
        self.perf_ax.set_xlabel('Time', color=TEXT_PRIMARY)
        self.perf_ax.set_ylabel('Usage (%)', color=TEXT_PRIMARY)
        self.perf_ax.tick_params(colors=TEXT_PRIMARY)
        
        # Performance metric lines
        self.cpu_line, = self.perf_ax.plot([], [], color=SUCCESS_MAIN, label='CPU', linewidth=2)
        self.mem_line, = self.perf_ax.plot([], [], color=WARNING_MAIN, label='Memory', linewidth=2)
        
        self.perf_ax.legend()
        self.perf_ax.grid(True, alpha=0.3)
        self.perf_ax.set_ylim(0, 100)
        
        # Embed into tkinter
        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, plot_frame)
        self.perf_canvas.draw()
        self.perf_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
    
    def _build_performance_text(self, parent):
        """Build text-based performance display"""
        text_frame = ttk.LabelFrame(parent, text="Performance Data", padding=10)
        text_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        self.perf_text = tk.Text(text_frame, height=10, bg=SURFACE_2, fg=TEXT_PRIMARY)
        perf_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.perf_text.yview)
        self.perf_text.configure(yscrollcommand=perf_scrollbar.set)
        
        self.perf_text.grid(row=0, column=0, sticky='nsew')
        perf_scrollbar.grid(row=0, column=1, sticky='ns')
    
    def _build_statistics_tab(self):
        """Build data statistics tab"""
        stats_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(stats_frame, text="Data Statistics")
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)
        
        # Statistics information display
        stats_text_frame = ttk.LabelFrame(stats_frame, text="Statistics Information", padding=10)
        stats_text_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
        stats_text_frame.grid_columnconfigure(0, weight=1)
        stats_text_frame.grid_rowconfigure(0, weight=1)
        
        self.stats_text = tk.Text(stats_text_frame, bg=SURFACE_2, fg=TEXT_PRIMARY)
        stats_scrollbar = ttk.Scrollbar(stats_text_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.grid(row=0, column=0, sticky='nsew')
        stats_scrollbar.grid(row=0, column=1, sticky='ns')
    
    def _build_status_bar(self):
        """Build status bar"""
        status_frame = ttk.Frame(self, style="Bottombar.TFrame")
        status_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Data point count
        ttk.Label(status_frame, text="Data Points:").grid(row=0, column=0, padx=5)
        self.data_count_label = ttk.Label(status_frame, text="0")
        self.data_count_label.grid(row=0, column=1, sticky='w', padx=5)
        
        # Last update time
        ttk.Label(status_frame, text="Last Update:").grid(row=0, column=2, padx=5)
        self.last_update_label = ttk.Label(status_frame, text="Never")
        self.last_update_label.grid(row=0, column=3, sticky='w', padx=5)
    
    def _toggle_monitoring(self):
        """Toggle monitoring status"""
        if self.monitoring_active:
            self._stop_monitoring()
        else:
            self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.start_button.configure(text="Stop Monitoring")
            self.status_label.configure(text="Running", foreground=SUCCESS_MAIN)
            
            # Start signal acquisition engine
            if self.acquisition_engine.start_acquisition():
                self.printd("Signal acquisition engine started")
            else:
                self.printe("Signal acquisition engine failed to start")
                self.monitoring_active = False
                self.start_button.configure(text="Start Monitoring")
                self.status_label.configure(text="Start Failed", foreground=ERROR_MAIN)
                return
            
            # Start data update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Start GUI update
            self._schedule_gui_update()
            
            # Start Tach monitoring
            self._start_tach_monitoring()
            
            self.printd("Monitoring started")
    
    def _stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.start_button.configure(text="Start Monitoring")
            self.status_label.configure(text="Stopped", foreground=ERROR_MAIN)
            
            # Stop signal acquisition engine
            if self.acquisition_engine.stop_acquisition():
                self.printd("Signal acquisition engine stopped")
            else:
                self.printw("Problem occurred while stopping signal acquisition engine")
            
            # Stop Tach monitoring
            self._stop_tach_monitoring()
            
            self.printd("Monitoring stopped")
    
    def _clear_data(self):
        """Clear all data"""
        self.signal_data.clear()
        for key in self.system_stats:
            self.system_stats[key].clear()
        
        # Clear text display
        if hasattr(self, 'signal_text'):
            self.signal_text.delete(1.0, tk.END)
        if hasattr(self, 'perf_text'):
            self.perf_text.delete(1.0, tk.END)
        if hasattr(self, 'stats_text'):
            self.stats_text.delete(1.0, tk.END)
        
        self.printd("Data cleared")
    
    def _update_loop(self):
        """Data update loop (runs in background thread)"""
        start_time = time.time()
        
        while self.monitoring_active:
            try:
                current_time = time.time() - start_time
                
                # Get data from signal acquisition engine - batch processing
                all_signal_data = []
                # 批量获取数据，最多获取20批次以提高消费效率
                for _ in range(20):
                    signal_data = self.acquisition_engine.get_data(timeout=0.005)
                    if signal_data:
                        all_signal_data.extend(signal_data)
                    else:
                        break
                
                if all_signal_data:
                    self._process_signal_data(all_signal_data, current_time)
                
                # Simulate system performance data (kept for demonstration)
                self._generate_mock_system_data(current_time)
                
                # Generate Tach data (if enabled)
                if self.tach_monitoring_active:
                    self._generate_mock_tach_data(current_time)
                
                time.sleep(0.05)  # 50ms update interval - 更频繁的更新以消费更多数据
                
            except Exception as e:
                self.printd(f"Data update error: {e}")
                break
    
    def _on_signal_data_received(self, samples):
        """Signal data reception callback function"""
        try:
            for sample in samples:
                channel_key = f'channel_{sample.channel_id}'
                
                if channel_key not in self.signal_data:
                    self.signal_data[channel_key] = {
                        'timestamps': deque(maxlen=MAX_DATA_POINTS),
                        'values': deque(maxlen=MAX_DATA_POINTS)
                    }
                
                # Add real signal data
                self.signal_data[channel_key]['timestamps'].append(sample.timestamp)
                self.signal_data[channel_key]['values'].append(sample.value)
                
        except Exception as e:
            self.printd(f"Signal data processing error: {e}")
    
    def _process_signal_data(self, samples, current_time):
        """Process signal data obtained from acquisition engine"""
        try:
            # Update signal statistics
            if samples:
                for sample in samples:
                    channel_key = f'channel_{sample.channel_id}'
                    
                    if channel_key not in self.signal_data:
                        self.signal_data[channel_key] = {
                            'timestamps': deque(maxlen=MAX_DATA_POINTS),
                            'values': deque(maxlen=MAX_DATA_POINTS)
                        }
                    
                    # Use relative timestamp
                    relative_time = current_time
                    self.signal_data[channel_key]['timestamps'].append(relative_time)
                    self.signal_data[channel_key]['values'].append(sample.value)
                    
        except Exception as e:
            self.printd(f"Signal data processing error: {e}")
    
    ## TACH SIGNAL METHODS ########################################################
    
    def _toggle_tach_monitoring(self):
        """Toggle Tach monitoring status"""
        if self.tach_monitor_var.get():
            self._start_tach_monitoring()
        else:
            self._stop_tach_monitoring()
    
    def _start_tach_monitoring(self):
        """Start Tach signal monitoring"""
        if not self.tach_monitoring_active:
            self.tach_monitoring_active = True
            self.printd(f"Starting Tach monitoring for {len(self.tach_config.enabled_fans)} fans: {self.tach_config.enabled_fans[:5]}...")
            
            # Try to initialize FCCommunicator
            if FC_COMM_AVAILABLE and self.fc_communicator is None:
                try:
                    self.fc_communicator = fcc.FCCommunicator()
                    self.printd("FCCommunicator initialized successfully, will get real Tach data")
                except Exception as e:
                    self.printw(f"FCCommunicator initialization failed: {e}, using simulated data")
                    self.fc_communicator = None
            
            # Initialize Tach data storage
            for fan_id in self.tach_config.enabled_fans:
                if fan_id not in self.tach_data:
                    self.tach_data[fan_id] = {
                        'timestamps': deque(maxlen=MAX_DATA_POINTS),
                        'rpm_values': deque(maxlen=MAX_DATA_POINTS),
                        'filtered_rpm': deque(maxlen=MAX_DATA_POINTS),
                        'duty_cycles': deque(maxlen=MAX_DATA_POINTS),
                        'timeouts': deque(maxlen=MAX_DATA_POINTS),
                        'raw_signals': deque(maxlen=MAX_DATA_POINTS)
                    }
                
                # Initialize filter
                if fan_id not in self.tach_filters:
                    self.tach_filters[fan_id] = {
                        'buffer': deque(maxlen=self.tach_config.filter_window),
                        'alpha': 0.1  # Low-pass filter parameter
                    }
            
            self.printd("Tach signal monitoring started")
    
    def _stop_tach_monitoring(self):
        """Stop Tach signal monitoring"""
        if self.tach_monitoring_active:
            self.tach_monitoring_active = False
            
            # Clean up FCCommunicator
            if self.fc_communicator:
                try:
                    # If FCCommunicator has close method, call it
                    if hasattr(self.fc_communicator, 'close'):
                        self.fc_communicator.close()
                except Exception as e:
                    self.printw(f"Error closing FCCommunicator: {e}")
                finally:
                    self.fc_communicator = None
            
            self.printd("Tach signal monitoring stopped")
    
    def _on_filter_type_changed(self, event=None):
        """Filter type change event handler"""
        filter_type = self.filter_type_var.get()
        self.tach_config.filter_type = filter_type
        self.tach_config.filter_enabled = (filter_type != "none")
        self.printd(f"Filter type changed to: {filter_type}")
    
    def _on_filter_window_changed(self, event=None):
        """Filter window size change event handler"""
        try:
            window_size = int(self.filter_window_var.get())
            if 1 <= window_size <= 50:
                self.tach_config.filter_window = window_size
                # Update window size for all filters
                for fan_id in self.tach_filters:
                    self.tach_filters[fan_id]['buffer'] = deque(
                        list(self.tach_filters[fan_id]['buffer'])[-window_size:],
                        maxlen=window_size
                    )
                self.printd(f"Filter window size changed to: {window_size}")
            else:
                self.printw("Filter window size must be between 1-50")
                self.filter_window_var.set(str(self.tach_config.filter_window))
        except ValueError:
            self.printw("Filter window size must be an integer")
            self.filter_window_var.set(str(self.tach_config.filter_window))
    
    def _on_rpm_threshold_changed(self, event=None):
        """RPM threshold change event handler"""
        try:
            threshold = float(self.rpm_threshold_var.get())
            if threshold >= 0:
                self.tach_config.rpm_threshold = threshold
                self.printd(f"RPM threshold changed to: {threshold}")
            else:
                self.printw("RPM threshold must be greater than or equal to 0")
                self.rpm_threshold_var.set(str(self.tach_config.rpm_threshold))
        except ValueError:
            self.printw("RPM threshold must be a number")
            self.rpm_threshold_var.set(str(self.tach_config.rpm_threshold))
    
    def _apply_tach_filter(self, fan_id: int, rpm_value: float) -> float:
        """Apply Tach signal filtering"""
        if not self.tach_config.filter_enabled or self.tach_config.filter_type == "none":
            return rpm_value
        
        if fan_id not in self.tach_filters:
            self.tach_filters[fan_id] = {
                'buffer': deque(maxlen=self.tach_config.filter_window),
                'alpha': 0.1
            }
        
        filter_state = self.tach_filters[fan_id]
        
        if self.tach_config.filter_type == "moving_average":
            # Moving average filter
            filter_state['buffer'].append(rpm_value)
            if len(filter_state['buffer']) > 0:
                return sum(filter_state['buffer']) / len(filter_state['buffer'])
            else:
                return rpm_value
        
        elif self.tach_config.filter_type == "low_pass":
            # Simple low-pass filter
            if 'last_filtered' not in filter_state:
                filter_state['last_filtered'] = rpm_value
            
            alpha = filter_state['alpha']
            filtered_value = alpha * rpm_value + (1 - alpha) * filter_state['last_filtered']
            filter_state['last_filtered'] = filtered_value
            return filtered_value
        
        return rpm_value
    
    def _diagnose_tach_signal(self, fan_id: int, reading: TachReading, filtered_rpm: float):
        """Diagnose Tach signal anomalies"""
        try:
            # Skip diagnostics for simulated data to reduce log spam
            if not hasattr(self, 'fc_communicator') or self.fc_communicator is None:
                # Only log critical issues for simulated data with reduced frequency
                if reading.timeout and self.tach_config.simulation_diagnostics:
                    # Reduce timeout logging frequency
                    if not hasattr(self, '_last_timeout_log'):
                        self._last_timeout_log = {}
                    current_time = time.time()
                    if fan_id not in self._last_timeout_log or current_time - self._last_timeout_log[fan_id] > 30:
                        self.printd(f"Fan {fan_id+1} Tach signal timeout (simulated)")
                        self._last_timeout_log[fan_id] = current_time
                return  # Skip other diagnostics for simulated data
            
            # Real hardware diagnostics (only when fc_communicator is available)
            # Add frequency limiting for real hardware diagnostics too
            if not hasattr(self, '_last_diagnostic_log'):
                self._last_diagnostic_log = {}
            current_time = time.time()
            
            # Timeout detection
            if reading.timeout:
                if fan_id not in self._last_diagnostic_log or current_time - self._last_diagnostic_log[fan_id] > 10:
                    self.printw(f"Fan {fan_id+1} Tach signal timeout")
                    self._last_diagnostic_log[fan_id] = current_time
            
            # RPM anomaly detection
            if not reading.timeout:
                # Check if RPM is too low
                if filtered_rpm < self.tach_config.rpm_threshold:
                    if fan_id not in self._last_diagnostic_log or current_time - self._last_diagnostic_log[fan_id] > 15:
                        self.printw(f"Fan {fan_id+1} RPM too low: {filtered_rpm:.0f} < {self.tach_config.rpm_threshold}")
                        self._last_diagnostic_log[fan_id] = current_time
                
                # Check if RPM is abnormally high
                if filtered_rpm > 5000:  # Assume 5000 RPM as abnormally high value
                    if fan_id not in self._last_diagnostic_log or current_time - self._last_diagnostic_log[fan_id] > 15:
                        self.printw(f"Fan {fan_id+1} RPM abnormally high: {filtered_rpm:.0f}")
                        self._last_diagnostic_log[fan_id] = current_time
                
                # Check if RPM fluctuation is too large
                if fan_id in self.tach_data and len(self.tach_data[fan_id]['filtered_rpm']) > 5:
                    recent_rpms = list(self.tach_data[fan_id]['filtered_rpm'])[-5:]
                    rpm_std = np.std(recent_rpms) if len(recent_rpms) > 1 else 0
                    if rpm_std > 200:  # RPM standard deviation too large
                        if fan_id not in self._last_diagnostic_log or current_time - self._last_diagnostic_log[fan_id] > 20:
                            self.printw(f"Fan {fan_id+1} RPM fluctuation too large: std={rpm_std:.1f}")
                            self._last_diagnostic_log[fan_id] = current_time
            
            # Duty cycle anomaly detection
            if reading.duty_cycle < 0 or reading.duty_cycle > 1:
                if fan_id not in self._last_diagnostic_log or current_time - self._last_diagnostic_log[fan_id] > 10:
                    self.printw(f"Fan {fan_id+1} duty cycle abnormal: {reading.duty_cycle:.2f}")
                    self._last_diagnostic_log[fan_id] = current_time
                
        except Exception as e:
            self.printd(f"Tach signal diagnosis error: {e}")
    
    def _process_tach_reading(self, reading: TachReading):
        """Process single Tach reading"""
        fan_id = reading.fan_id
        
        # Ensure data storage is initialized
        if fan_id not in self.tach_data:
            self.tach_data[fan_id] = {
                'timestamps': deque(maxlen=MAX_DATA_POINTS),
                'rpm_values': deque(maxlen=MAX_DATA_POINTS),
                'filtered_rpm': deque(maxlen=MAX_DATA_POINTS),
                'duty_cycles': deque(maxlen=MAX_DATA_POINTS),
                'timeouts': deque(maxlen=MAX_DATA_POINTS),
                'raw_signals': deque(maxlen=MAX_DATA_POINTS)  # Raw signal data
            }
        
        # Apply filtering
        filtered_rpm = self._apply_tach_filter(fan_id, reading.rpm)
        
        # Perform diagnostic checks
        self._diagnose_tach_signal(fan_id, reading, filtered_rpm)
        
        # Store data
        data = self.tach_data[fan_id]
        data['timestamps'].append(reading.timestamp)
        data['rpm_values'].append(reading.rpm)
        data['filtered_rpm'].append(filtered_rpm)
        data['duty_cycles'].append(reading.duty_cycle)
        data['timeouts'].append(reading.timeout)
        data['raw_signals'].append(reading.raw_signal)  # Store raw signal data
    
    def _generate_mock_tach_data(self, timestamp):
        """Generate simulated Tach data or get real data"""
        try:
            if self.fc_communicator:
                # Try to get real Tach data
                self._get_real_tach_data(timestamp)
            elif self.tach_config.enable_simulation:
                # Generate simulated data only if enabled
                self._generate_simulated_tach_data(timestamp)
            # If simulation is disabled and no real hardware, do nothing
                    
        except Exception as e:
            self.printd(f"Tach data acquisition error: {e}")
    
    def _get_real_tach_data(self, timestamp):
        """Get real Tach data from FCCommunicator"""
        try:
            # Try to get RPM data from FCCommunicator
            if hasattr(self.fc_communicator, 'get_rpm_data'):
                rpm_data = self.fc_communicator.get_rpm_data()
                if rpm_data:
                    for fan_id, rpm_value in enumerate(rpm_data):
                        if fan_id in self.tach_config.enabled_fans and fan_id < len(rpm_data):
                            # Create real Tach reading
                            reading = TachReading(
                                fan_id=fan_id,
                                rpm=float(rpm_value),
                                timestamp=timestamp,
                                duty_cycle=0.0,  # Need to get from FCCommunicator
                                timeout=False
                            )
                            self._process_tach_reading(reading)
            else:
                # If no get_rpm_data method, fallback to simulated data only if enabled
                if self.tach_config.enable_simulation:
                    self._generate_simulated_tach_data(timestamp)
                
        except Exception as e:
            if self.tach_config.enable_simulation:
                self.printw(f"Failed to get real Tach data: {e}, using simulated data")
                self._generate_simulated_tach_data(timestamp)
            else:
                self.printd(f"Failed to get real Tach data: {e}, simulation disabled")
    
    def _generate_simulated_tach_data(self, timestamp):
        """Generate simulated Tach data (for testing)"""
        import random
        
        # self.printd(f"Generating simulated Tach data for {len(self.tach_config.enabled_fans)} enabled fans")
        
        for fan_id in range(21):  # Simulate all 21 fans (maximum supported)
            if fan_id in self.tach_config.enabled_fans:
                # Generate simulated RPM values
                base_rpm = 1000 + fan_id * 200
                noise = random.uniform(-50, 50)
                rpm = max(0, base_rpm + noise)
                
                # Generate simulated raw signal (pulse amplitude)
                import math
                signal_freq = rpm / 60.0 * 2  # Assume 2 pulses per revolution
                raw_signal = 3.3 * (0.5 + 0.5 * math.sin(2 * math.pi * signal_freq * timestamp))
                raw_signal += random.uniform(-0.1, 0.1)  # Add noise
                
                # Simulate timeout
                timeout = random.random() < 0.05  # 5% timeout rate
                if timeout:
                    rpm = 0
                    raw_signal = 0
                
                # Create simulated reading
                reading = TachReading(
                    fan_id=fan_id,
                    rpm=rpm,
                    timestamp=timestamp,
                    duty_cycle=0.5 + fan_id * 0.1,
                    timeout=timeout,
                    raw_signal=raw_signal
                )
                
                self._process_tach_reading(reading)
    
    def _generate_mock_signal_data(self, timestamp):
        """Generate simulated signal data (backup method)"""
        import math
        
        # Generate different frequency sine waves for each channel
        for channel in range(3):
            if f'channel_{channel}' not in self.signal_data:
                self.signal_data[f'channel_{channel}'] = {
                    'timestamps': deque(maxlen=MAX_DATA_POINTS),
                    'values': deque(maxlen=MAX_DATA_POINTS)
                }
            
            # Generate signal values
            freq = 10.0 + channel * 5.0  # Different frequencies
            amplitude = 1.0 + channel * 0.5
            noise = (time.time() % 1 - 0.5) * 0.1  # Add noise
            value = amplitude * math.sin(2 * math.pi * freq * timestamp) + noise
            
            self.signal_data[f'channel_{channel}']['timestamps'].append(timestamp)
            self.signal_data[f'channel_{channel}']['values'].append(value)
    
    def _generate_mock_system_data(self, timestamp):
        """Generate simulated system performance data"""
        import random
        
        # CPU usage (simulate fluctuation)
        cpu_usage = 20 + 30 * abs(math.sin(timestamp * 0.1)) + random.uniform(-5, 5)
        cpu_usage = max(0, min(100, cpu_usage))
        
        # Memory usage
        mem_usage = 40 + 20 * abs(math.cos(timestamp * 0.05)) + random.uniform(-3, 3)
        mem_usage = max(0, min(100, mem_usage))
        
        # Network packet count
        packet_count = len(self.system_stats['timestamps']) * 10 + random.randint(0, 5)
        
        # Update system statistics
        self.system_stats['cpu_usage'].append(cpu_usage)
        self.system_stats['memory_usage'].append(mem_usage)
        self.system_stats['network_packets'].append(packet_count)
        self.system_stats['timestamps'].append(timestamp)
    
    def _schedule_gui_update(self):
        """Schedule GUI update"""
        try:
            # Check if widget still exists before scheduling
            if not hasattr(self, 'winfo_exists') or not self.winfo_exists():
                return
            
            # Additional check for root window
            if not hasattr(self, 'master') or not hasattr(self.master, 'winfo_exists') or not self.master.winfo_exists():
                return
                
            # Check if monitoring is still active and we have necessary methods
            if not hasattr(self, 'monitoring_active') or not self.monitoring_active:
                return
                
            if not hasattr(self, '_update_gui'):
                return
                
            try:
                self._update_gui()
            except (tk.TclError, AttributeError):
                # GUI update failed, stop monitoring
                if hasattr(self, 'monitoring_active'):
                    self.monitoring_active = False
                return
                
            # Schedule next update with additional safety check
            try:
                if (hasattr(self, 'winfo_exists') and self.winfo_exists() and 
                    hasattr(self, 'monitoring_active') and self.monitoring_active and
                    hasattr(self, 'after')):
                    self.after(UPDATE_INTERVAL, self._schedule_gui_update)
            except (tk.TclError, AttributeError, RuntimeError):
                # Failed to schedule, stop monitoring
                if hasattr(self, 'monitoring_active'):
                    self.monitoring_active = False
        except (tk.TclError, AttributeError, RuntimeError):
            # Widget has been destroyed or attribute error, stop scheduling
            if hasattr(self, 'monitoring_active'):
                self.monitoring_active = False
    
    def _update_gui(self):
        """Update GUI display"""
        try:
            # Update signal charts
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'signal_lines'):
                self._update_signal_plot()
            elif hasattr(self, 'signal_text'):
                self._update_signal_text()
            
            # Update Tach charts
            if self.tach_monitoring_active:
                if MATPLOTLIB_AVAILABLE and hasattr(self, 'tach_ax1'):
                    self._update_tach_plot()
                elif hasattr(self, 'tach_text'):
                    self._update_tach_text()
                
                # Update Tach status display
                self._update_tach_status()
            
            # Update performance charts
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'cpu_line'):
                self._update_performance_plot()
            elif hasattr(self, 'perf_text'):
                self._update_performance_text()
            
            # Update system information
            self._update_system_info()
            
            # Update status bar
            self._update_status_bar()
            
            # Update statistics
            self._update_statistics()
            
        except Exception as e:
            self.printd(f"GUI update error: {e}")
    
    def _update_signal_plot(self):
        """Update signal charts"""
        for i, line in enumerate(self.signal_lines):
            channel_key = f'channel_{i}'
            if channel_key in self.signal_data:
                data = self.signal_data[channel_key]
                if data['timestamps'] and data['values']:
                    line.set_data(list(data['timestamps']), list(data['values']))
        
        # Auto-adjust coordinate axes
        if self.signal_data:
            all_timestamps = []
            all_values = []
            for data in self.signal_data.values():
                all_timestamps.extend(data['timestamps'])
                all_values.extend(data['values'])
            
            if all_timestamps and all_values:
                self.signal_ax.set_xlim(min(all_timestamps), max(all_timestamps))
                self.signal_ax.set_ylim(min(all_values) - 0.5, max(all_values) + 0.5)
        
        try:
            if hasattr(self, 'signal_canvas') and self.signal_canvas:
                self.signal_canvas.draw_idle()
        except (tk.TclError, AttributeError, RuntimeError):
            # Canvas destroyed or not available
            pass
    
    def _update_signal_text(self):
        """Update signal text display"""
        self.signal_text.delete(1.0, tk.END)
        
        for channel_key, data in self.signal_data.items():
            if data['timestamps'] and data['values']:
                latest_time = data['timestamps'][-1]
                latest_value = data['values'][-1]
                self.signal_text.insert(tk.END, 
                    f"{channel_key}: Time={latest_time:.2f}s, Value={latest_value:.3f}\n")
    
    def _update_performance_plot(self):
        """Update performance charts"""
        timestamps = list(self.system_stats['timestamps'])
        cpu_data = list(self.system_stats['cpu_usage'])
        mem_data = list(self.system_stats['memory_usage'])
        
        if timestamps:
            self.cpu_line.set_data(timestamps, cpu_data)
            self.mem_line.set_data(timestamps, mem_data)
            
            # Ensure minimum range for xlims to avoid singular transformation
            min_time = min(timestamps)
            max_time = max(timestamps)
            if max_time - min_time < 0.1:  # Minimum 0.1 second range
                center = (min_time + max_time) / 2
                min_time = center - 0.05
                max_time = center + 0.05
            self.perf_ax.set_xlim(min_time, max_time)
            
        try:
            if hasattr(self, 'perf_canvas') and self.perf_canvas:
                self.perf_canvas.draw_idle()
        except (tk.TclError, AttributeError, RuntimeError):
            # Canvas destroyed or not available
            pass
    
    def _update_performance_text(self):
        """Update performance text display"""
        self.perf_text.delete(1.0, tk.END)
        
        if self.system_stats['timestamps']:
            latest_time = self.system_stats['timestamps'][-1]
            latest_cpu = self.system_stats['cpu_usage'][-1]
            latest_mem = self.system_stats['memory_usage'][-1]
            
            self.perf_text.insert(tk.END, 
                f"Time: {latest_time:.1f}s\n"
                f"CPU Usage: {latest_cpu:.1f}%\n"
                f"Memory Usage: {latest_mem:.1f}%\n")
    
    def _update_system_info(self):
        """Update system information display"""
        if self.system_stats['timestamps']:
            runtime = self.system_stats['timestamps'][-1]
            cpu_usage = self.system_stats['cpu_usage'][-1] if self.system_stats['cpu_usage'] else 0
            mem_usage = self.system_stats['memory_usage'][-1] if self.system_stats['memory_usage'] else 0
            packet_count = self.system_stats['network_packets'][-1] if self.system_stats['network_packets'] else 0
            
            # Format runtime
            hours = int(runtime // 3600)
            minutes = int((runtime % 3600) // 60)
            seconds = int(runtime % 60)
            runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Update labels
            self.system_info_labels['Runtime'].configure(text=runtime_str)
            self.system_info_labels['CPU Usage'].configure(text=f"{cpu_usage:.1f}%")
            self.system_info_labels['Memory Usage'].configure(text=f"{mem_usage:.1f}%")
            self.system_info_labels['Network Packets'].configure(text=str(packet_count))
            self.system_info_labels['Connected Devices'].configure(text="3")  # Simulated value
            
            # Calculate packets/second
            if len(self.system_stats['timestamps']) > 1:
                time_diff = self.system_stats['timestamps'][-1] - self.system_stats['timestamps'][-2]
                if time_diff > 0:
                    packets_per_sec = 10 / time_diff  # Simulated value
                    self.system_info_labels['Packets/sec'].configure(text=f"{packets_per_sec:.1f}")
    
    def _update_status_bar(self):
        """Update status bar"""
        # Data point count
        total_points = sum(len(data['timestamps']) for data in self.signal_data.values())
        self.data_count_label.configure(text=str(total_points))
        
        # Last update time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.configure(text=current_time)
    
    def _update_statistics(self):
        """Update statistics information"""
        self.stats_text.delete(1.0, tk.END)
        
        stats_info = "=== Data Monitoring Statistics ===\n\n"
        
        # Signal statistics
        stats_info += "Signal Statistics:\n"
        for channel_key, data in self.signal_data.items():
            if data['values']:
                values = list(data['values'])
                avg_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                stats_info += f"  {channel_key}: Average={avg_val:.3f}, Min={min_val:.3f}, Max={max_val:.3f}\n"
        
        # System statistics
        stats_info += "\nSystem Statistics:\n"
        if self.system_stats['cpu_usage']:
            cpu_values = list(self.system_stats['cpu_usage'])
            avg_cpu = sum(cpu_values) / len(cpu_values)
            stats_info += f"  Average CPU Usage: {avg_cpu:.1f}%\n"
        
        if self.system_stats['memory_usage']:
            mem_values = list(self.system_stats['memory_usage'])
            avg_mem = sum(mem_values) / len(mem_values)
            stats_info += f"  Average Memory Usage: {avg_mem:.1f}%\n"
        
        stats_info += f"\nTotal Data Points: {sum(len(data['timestamps']) for data in self.signal_data.values())}\n"
        stats_info += f"Monitoring Duration: {self.system_stats['timestamps'][-1]:.1f}s\n" if self.system_stats['timestamps'] else "Monitoring Duration: 0s\n"
        
        self.stats_text.insert(tk.END, stats_info)
    
    def _update_tach_plot(self):
        """Update Tach plot display"""
        try:
            # Update raw signal plot (if enabled)
            if self.tach_config.show_raw_signal:
                self.tach_ax_raw.clear()
                self.tach_ax_raw.set_facecolor(SURFACE_2)
                self.tach_ax_raw.set_title('Raw Tach Signal Monitoring', color=TEXT_PRIMARY, fontsize=12)
                self.tach_ax_raw.set_xlabel('Time (s)', color=TEXT_PRIMARY)
                self.tach_ax_raw.set_ylabel('Signal Amplitude (V)', color=TEXT_PRIMARY)
                self.tach_ax_raw.tick_params(colors=TEXT_PRIMARY)
                self.tach_ax_raw.grid(True, alpha=0.3)
                
                # Plot raw signal curves for first 6 fans
                for fan_id in range(min(6, len(self.tach_data))):
                    if fan_id in self.tach_data:
                        data = self.tach_data[fan_id]
                        if data['timestamps'] and data['raw_signals']:
                            timestamps = list(data['timestamps'])
                            raw_signals = list(data['raw_signals'])
                            color = TACH_COLORS[fan_id % len(TACH_COLORS)]
                            self.tach_ax_raw.plot(timestamps, raw_signals, color=color, 
                                               label=f'Fan{fan_id+1}', linewidth=1, alpha=0.7)
                
                # 只有当有数据绘制时才显示图例
                handles, labels = self.tach_ax_raw.get_legend_handles_labels()
                if handles:
                    self.tach_ax_raw.legend()
            
            # Update RPM time series plot
            self.tach_ax1.clear()
            self.tach_ax1.set_facecolor(SURFACE_2)
            self.tach_ax1.set_title('Fan Speed Real-time Monitoring', color=TEXT_PRIMARY, fontsize=12)
            self.tach_ax1.set_xlabel('Time (s)', color=TEXT_PRIMARY)
            self.tach_ax1.set_ylabel('Speed (RPM)', color=TEXT_PRIMARY)
            self.tach_ax1.tick_params(colors=TEXT_PRIMARY)
            self.tach_ax1.grid(True, alpha=0.3)
            
            # Plot RPM curves for first 6 fans
            for fan_id in range(min(6, len(self.tach_data))):
                if fan_id in self.tach_data:
                    data = self.tach_data[fan_id]
                    if data['timestamps'] and data['filtered_rpm']:
                        timestamps = list(data['timestamps'])
                        rpm_values = list(data['filtered_rpm'])
                        color = TACH_COLORS[fan_id % len(TACH_COLORS)]
                        self.tach_ax1.plot(timestamps, rpm_values, color=color, 
                                         label=f'Fan{fan_id+1}', linewidth=2)
            
            # 只有当有数据绘制时才显示图例
            handles, labels = self.tach_ax1.get_legend_handles_labels()
            if handles:
                self.tach_ax1.legend()
            
            # Update RPM distribution bar chart
            self.tach_ax2.clear()
            self.tach_ax2.set_facecolor(SURFACE_2)
            self.tach_ax2.set_title('Current Speed Distribution', color=TEXT_PRIMARY, fontsize=12)
            self.tach_ax2.set_xlabel('Fan Number', color=TEXT_PRIMARY)
            self.tach_ax2.set_ylabel('Speed (RPM)', color=TEXT_PRIMARY)
            self.tach_ax2.tick_params(colors=TEXT_PRIMARY)
            self.tach_ax2.grid(True, alpha=0.3, axis='y')
            
            # Plot current RPM bar chart
            fan_ids = []
            current_rpms = []
            colors = []
            
            for fan_id in range(min(6, len(self.tach_data))):
                if fan_id in self.tach_data:
                    data = self.tach_data[fan_id]
                    if data['filtered_rpm']:
                        fan_ids.append(fan_id + 1)
                        current_rpms.append(data['filtered_rpm'][-1])
                        colors.append(TACH_COLORS[fan_id % len(TACH_COLORS)])
            
            if fan_ids:
                self.tach_ax2.bar(fan_ids, current_rpms, color=colors, alpha=0.7)
            
            # Layout is handled by subplots_adjust in _build_tach_plot
            try:
                if hasattr(self, 'tach_canvas') and self.tach_canvas:
                    self.tach_canvas.draw_idle()
            except (tk.TclError, AttributeError, RuntimeError):
                # Canvas destroyed or not available
                pass
            
        except Exception as e:
            self.printd(f"Tach plot update error: {e}")
    
    def _update_tach_text(self):
        """Update Tach text display"""
        try:
            self.tach_text.delete(1.0, tk.END)
            
            header = f"{'Fan ID':<8} {'RPM':<8} {'Filtered RPM':<10} {'Duty Cycle':<8} {'Status':<8} {'Time':<12}\n"
            header += "-" * 60 + "\n"
            self.tach_text.insert(tk.END, header)
            
            for fan_id in sorted(self.tach_data.keys()):
                data = self.tach_data[fan_id]
                if data['timestamps']:
                    latest_time = data['timestamps'][-1]
                    raw_rpm = data['rpm_values'][-1] if data['rpm_values'] else 0
                    filtered_rpm = data['filtered_rpm'][-1] if data['filtered_rpm'] else 0
                    duty_cycle = data['duty_cycles'][-1] if data['duty_cycles'] else 0
                    timeout = data['timeouts'][-1] if data['timeouts'] else False
                    
                    status = "Timeout" if timeout else "Normal"
                    
                    line = f"{fan_id+1:<8} {raw_rpm:<8.0f} {filtered_rpm:<10.1f} {duty_cycle:<8.2f} {status:<8} {latest_time:<12.2f}\n"
                    self.tach_text.insert(tk.END, line)
            
        except Exception as e:
            self.printd(f"Tach text update error: {e}")
    
    def _update_tach_status(self):
        """Update Tach status display panel"""
        try:
            for fan_id in range(6):  # Update status for first 6 fans
                if fan_id in self.tach_status_labels and fan_id in self.tach_data:
                    data = self.tach_data[fan_id]
                    labels = self.tach_status_labels[fan_id]
                    
                    if data['filtered_rpm'] and data['timeouts']:
                        current_rpm = data['filtered_rpm'][-1]
                        is_timeout = data['timeouts'][-1]
                        
                        # Update RPM display
                        labels['rpm'].configure(text=f"{current_rpm:.0f} RPM")
                        
                        # Update status display
                        if is_timeout:
                            labels['status'].configure(text="Timeout", foreground=ERROR_MAIN)
                        elif current_rpm < self.tach_config.rpm_threshold:
                            labels['status'].configure(text="Low Speed", foreground=WARNING_MAIN)
                        else:
                            labels['status'].configure(text="Normal", foreground=SUCCESS_MAIN)
                    else:
                        labels['rpm'].configure(text="0 RPM")
                        labels['status'].configure(text="Offline", foreground=ERROR_MAIN)
                        
        except Exception as e:
            self.printd(f"Tach status update error: {e}")
    
    def destroy(self):
        """Override destroy method to properly clean up matplotlib canvases"""
        try:
            # Stop monitoring first
            if hasattr(self, 'monitoring_active') and self.monitoring_active:
                self._stop_monitoring()
            
            # Cancel any pending after() calls by clearing the widget's after queue
            try:
                # This will cancel all pending after() calls for this widget
                if hasattr(self, 'tk') and self.tk:
                    self.tk.call('after', 'cancel', 'all')
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Clean up matplotlib canvases
            if hasattr(self, 'signal_canvas') and self.signal_canvas:
                try:
                    self.signal_canvas.get_tk_widget().destroy()
                    self.signal_canvas = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
            if hasattr(self, 'perf_canvas') and self.perf_canvas:
                try:
                    self.perf_canvas.get_tk_widget().destroy()
                    self.perf_canvas = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
            if hasattr(self, 'tach_canvas') and self.tach_canvas:
                try:
                    self.tach_canvas.get_tk_widget().destroy()
                    self.tach_canvas = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
            # Clean up matplotlib figures
            if hasattr(self, 'signal_fig'):
                try:
                    plt.close(self.signal_fig)
                    self.signal_fig = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
            if hasattr(self, 'perf_fig'):
                try:
                    plt.close(self.perf_fig)
                    self.perf_fig = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
            if hasattr(self, 'tach_fig'):
                try:
                    plt.close(self.tach_fig)
                    self.tach_fig = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                    
        except Exception as e:
            # Ignore cleanup errors during shutdown
            pass
            
        # Call parent destroy
        try:
            super().destroy()
        except (tk.TclError, AttributeError, RuntimeError):
            pass

    def get_monitoring_status(self):
        """Get monitoring status"""
        return {
            'active': self.monitoring_active,
            'data_points': sum(len(data['timestamps']) for data in self.signal_data.values()),
            'channels': len(self.signal_data),
            'runtime': self.system_stats['timestamps'][-1] if self.system_stats['timestamps'] else 0,
            'tach_monitoring': self.tach_monitoring_active,
            'tach_fans': len(self.tach_data)
        }
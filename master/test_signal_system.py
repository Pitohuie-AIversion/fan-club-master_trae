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
 + Signal processing system test script.
 + Verifies signal acquisition and filtering integration.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import sys
import os
import time
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 导入信号处理系统模块
from fc.signal_processing_system import SignalProcessingSystem
from fc.backend.signal_acquisition import SimulatedHardware, AcquisitionConfig, ChannelConfig
from fc.backend.digital_filtering import FilterConfig, FilterType
from fc.backend.data_storage import StorageConfig

def create_test_config():
    """创建测试配置"""
    # 信号采集配置
    acquisition_config = AcquisitionConfig()
    acquisition_config.sample_rate = 1000.0  # 1kHz采样率
    acquisition_config.channels = ["Channel_1", "Channel_2", "Channel_3"]  # 3通道
    acquisition_config.buffer_size = 5000
    acquisition_config.resolution = 16
    
    # 滤波器配置
    filter_configs = []
    
    # 低通滤波器
    lowpass_config = FilterConfig()
    lowpass_config.filter_type = FilterType.LOWPASS
    lowpass_config.filter_method = FilterMethod.IIR
    lowpass_config.cutoff_freq = 100.0  # 100Hz截止频率
    lowpass_config.sampling_rate = 1000.0
    lowpass_config.order = 4
    filter_configs.append(lowpass_config)
    
    # 高通滤波器
    highpass_config = FilterConfig()
    highpass_config.filter_type = FilterType.HIGHPASS
    highpass_config.filter_method = FilterMethod.IIR
    highpass_config.cutoff_freq = 10.0  # 10Hz截止频率
    highpass_config.sampling_rate = 1000.0
    highpass_config.order = 2
    filter_configs.append(highpass_config)
    
    # 数据存储配置
    storage_config = StorageConfig()
    storage_config.base_path = "./test_signal_data"
    storage_config.auto_create_dirs = True
    storage_config.compression_enabled = True
    
    # 系统配置
    system_config = SystemConfig(
        acquisition_config=acquisition_config,
        filter_configs=filter_configs,
        storage_config=storage_config,
        quality_monitoring_enabled=True,
        quality_check_interval=2.0,  # 2秒检查一次质量
        buffer_size=8000,
        processing_threads=2,
        auto_save_enabled=True,
        auto_save_interval=15.0,  # 15秒自动保存一次
        real_time_processing=True,
        processing_chunk_size=512
    )
    
    return system_config

def setup_event_handlers(system):
    """设置事件处理器"""
    
    def on_data_acquired(data):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据采集: 形状={data['data_shape']}")
    
    def on_data_filtered(data):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据滤波: 原始={data['original_shape']} -> 滤波后={data['filtered_shape']}")
    
    def on_quality_updated(data):
        metrics = data['metrics']
        channel = data['channel']
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 质量更新 - {channel}: "
              f"分数={metrics.quality_score:.2f}, 等级={metrics.quality_level.value}, "
              f"SNR={metrics.snr:.1f}dB")
    
    def on_anomaly_detected(data):
        anomaly = data['anomaly']
        channel = data['channel']
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  异常检测 - {channel}: "
              f"{anomaly.anomaly_type.value}, 严重程度={anomaly.severity:.2f}, "
              f"位置={anomaly.position}")
    
    def on_data_saved(data):
        filepath = data['filepath']
        shape = data['data_shape']
        manual = data.get('manual', False)
        save_type = "手动" if manual else "自动"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 {save_type}保存: {filepath} (形状={shape})")
    
    def on_error_occurred(data):
        error = data['error']
        component = data['component']
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 错误 - {component}: {error}")
    
    # 注册事件处理器
    system.add_event_callback('data_acquired', on_data_acquired)
    system.add_event_callback('data_filtered', on_data_filtered)
    system.add_event_callback('quality_updated', on_quality_updated)
    system.add_event_callback('anomaly_detected', on_anomaly_detected)
    system.add_event_callback('data_saved', on_data_saved)
    system.add_event_callback('error_occurred', on_error_occurred)

def print_system_status(system):
    """打印系统状态"""
    status = system.get_system_status()
    
    print("\n" + "="*60)
    print("系统状态报告")
    print("="*60)
    print(f"状态: {status['state']}")
    print(f"运行中: {status['running']}")
    print(f"暂停: {status['paused']}")
    
    if 'runtime_seconds' in status:
        runtime_minutes = status['runtime_seconds'] / 60
        print(f"运行时间: {runtime_minutes:.1f} 分钟")
    
    print("\n统计信息:")
    stats = status['statistics']
    print(f"  总采集样本数: {stats['total_samples_acquired']:,}")
    print(f"  总处理样本数: {stats['total_samples_processed']:,}")
    print(f"  保存文件数: {stats['total_files_saved']}")
    print(f"  检测异常数: {stats['total_anomalies_detected']}")
    
    if stats['last_quality_check']:
        print(f"  最后质量检查: {stats['last_quality_check'].strftime('%H:%M:%S')}")
    
    print("\n缓冲区状态:")
    buffer_status = status['buffer_status']
    print(f"  原始数据缓冲区: {buffer_status['raw_data_buffer_size']} (满: {buffer_status['raw_data_buffer_full']})")
    print(f"  滤波数据缓冲区: {buffer_status['filtered_data_buffer_size']} (满: {buffer_status['filtered_data_buffer_full']})")
    
    print("\n线程状态:")
    thread_status = status['thread_status']
    print(f"  处理线程数: {thread_status['processing_threads']}")
    print(f"  监测线程活跃: {thread_status['monitoring_thread_alive']}")
    print(f"  自动保存线程活跃: {thread_status['auto_save_thread_alive']}")
    
    print("="*60)

def print_quality_summary(system):
    """打印质量摘要"""
    quality_summary = system.get_quality_summary()
    
    if quality_summary:
        print("\n" + "-"*40)
        print("信号质量摘要")
        print("-"*40)
        
        for channel, summary in quality_summary.items():
            if isinstance(summary, dict):
                print(f"\n{channel}:")
                print(f"  平均质量分数: {summary.get('average_quality_score', 'N/A')}")
                print(f"  质量等级分布: {summary.get('quality_level_distribution', {})}")
                print(f"  异常事件数: {summary.get('anomaly_count', 0)}")
        
        print("-"*40)

def run_test():
    """运行测试"""
    print("信号处理系统集成测试")
    print("=" * 50)
    
    try:
        # 创建配置
        print("1. 创建系统配置...")
        config = create_test_config()
        print("   ✓ 配置创建完成")
        
        # 创建系统
        print("2. 创建信号处理系统...")
        system = SignalProcessingSystem(config)
        print("   ✓ 系统创建完成")
        
        # 设置事件处理器
        print("3. 设置事件处理器...")
        setup_event_handlers(system)
        print("   ✓ 事件处理器设置完成")
        
        # 初始化组件
        print("4. 初始化系统组件...")
        if not system.initialize_components():
            print("   ❌ 组件初始化失败")
            return False
        print("   ✓ 组件初始化完成")
        
        # 启动系统
        print("5. 启动系统...")
        if not system.start_system():
            print("   ❌ 系统启动失败")
            return False
        print("   ✓ 系统启动成功")
        
        print("\n系统正在运行，监控数据处理...")
        print("(按 Ctrl+C 停止测试)\n")
        
        # 运行测试
        test_duration = 60  # 运行60秒
        start_time = time.time()
        status_interval = 20  # 每20秒打印一次状态
        last_status_time = start_time
        
        try:
            while time.time() - start_time < test_duration:
                current_time = time.time()
                
                # 定期打印状态
                if current_time - last_status_time >= status_interval:
                    print_system_status(system)
                    print_quality_summary(system)
                    last_status_time = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在停止系统...")
        
        # 最终状态报告
        print("\n6. 最终状态报告:")
        print_system_status(system)
        print_quality_summary(system)
        
        # 手动保存测试
        print("\n7. 测试手动保存功能...")
        saved_path = system.manual_save_data("test_manual_save", DataFormat.HDF5)
        if saved_path:
            print(f"   ✓ 手动保存成功: {saved_path}")
        else:
            print("   ⚠️  手动保存失败或无数据")
        
        # 停止系统
        print("\n8. 停止系统...")
        system.stop_system()
        print("   ✓ 系统已停止")
        
        print("\n" + "="*50)
        print("测试完成！")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
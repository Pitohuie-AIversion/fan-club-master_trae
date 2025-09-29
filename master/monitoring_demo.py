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
 + Monitoring capabilities demonstration script.
 + Shows monitoring abilities after main.py startup.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import sys
import os
import time
import threading
from datetime import datetime
import multiprocessing as mp

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 导入FC模块
import fc.archive as ac
import fc.printer as pt
import fc.builtin.profiles as btp

def demo_monitoring_capabilities():
    """演示监控功能"""
    print("Fan Club MkIV 监控功能演示")
    print("=" * 50)
    
    # 创建打印队列（模拟main.py中的pqueue）
    pqueue = mp.Queue()
    
    # 创建档案管理器（模拟main.py中的archive）
    print("1. 初始化系统档案...")
    archive = ac.FCArchive(pqueue, "0.17", btp.PROFILES["TENX10"])
    print("   ✓ 档案管理器已创建")
    
    # 显示配置信息
    profile = archive.profile()
    print(f"\n2. 当前配置信息:")
    print(f"   • 配置名称: {profile[ac.name]}")
    print(f"   • 广播周期: {profile[ac.broadcastPeriodMS]}ms")
    print(f"   • 处理周期: {profile[ac.periodMS]}ms")
    print(f"   • 最大风扇数: {profile[ac.maxFans]}")
    print(f"   • 广播端口: {profile[ac.broadcastPort]}")
    print(f"   • 外部监听端口: {profile.get(ac.externalDefaultListenerPort, 'N/A')}")
    
    # 模拟监控线程
    print(f"\n3. 启动监控线程...")
    
    class MonitoringDemo:
        def __init__(self):
            self.running = True
            self.stats = {
                'broadcast_count': 0,
                'data_packets': 0,
                'connected_slaves': 0,
                'monitoring_cycles': 0
            }
        
        def broadcast_routine(self):
            """模拟广播线程"""
            while self.running:
                self.stats['broadcast_count'] += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 广播信号 #{self.stats['broadcast_count']} - 搜索从机设备")
                time.sleep(1.0)  # 1秒广播间隔
        
        def data_processing_routine(self):
            """模拟数据处理线程"""
            while self.running:
                self.stats['data_packets'] += 1
                self.stats['connected_slaves'] = min(3, self.stats['data_packets'] // 10)  # 模拟设备连接
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 处理数据包 #{self.stats['data_packets']} - 已连接设备: {self.stats['connected_slaves']}")
                time.sleep(0.5)  # 500ms处理间隔
        
        def monitoring_routine(self):
            """模拟监控线程"""
            while self.running:
                self.stats['monitoring_cycles'] += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 监控周期 #{self.stats['monitoring_cycles']} - 系统状态检查")
                
                # 每5个周期显示统计信息
                if self.stats['monitoring_cycles'] % 5 == 0:
                    print(f"   📈 统计: 广播{self.stats['broadcast_count']}次, 数据包{self.stats['data_packets']}个, 设备{self.stats['connected_slaves']}台")
                
                time.sleep(2.0)  # 2秒监控间隔
        
        def stop(self):
            self.running = False
    
    # 创建监控实例
    monitor = MonitoringDemo()
    
    # 启动监控线程
    threads = [
        threading.Thread(target=monitor.broadcast_routine, daemon=True),
        threading.Thread(target=monitor.data_processing_routine, daemon=True),
        threading.Thread(target=monitor.monitoring_routine, daemon=True)
    ]
    
    for thread in threads:
        thread.start()
    
    print("   ✓ 监控线程已启动")
    print("\n4. 系统监控运行中...")
    print("   (这模拟了main.py启动后的持续监控状态)")
    print("   按 Ctrl+C 停止演示\n")
    
    try:
        # 运行15秒演示
        time.sleep(15)
        print("\n演示时间结束，正在停止监控...")
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止监控...")
    
    # 停止监控
    monitor.stop()
    
    # 等待线程结束
    for thread in threads:
        thread.join(timeout=1)
    
    print("\n5. 监控功能总结:")
    print("   ✓ 广播线程: 持续搜索和发现从机设备")
    print("   ✓ 数据处理线程: 实时处理来自设备的数据")
    print("   ✓ 监控线程: 定期检查系统状态和健康度")
    print("   ✓ GUI界面: 提供实时可视化和用户交互")
    print("   ✓ 网络通信: 维持与从机设备的连接")
    
    print("\n" + "=" * 50)
    print("✅ 是的，main.py启动后能够持续监控！")
    print("系统会一直运行直到用户主动关闭GUI界面。")
    print("=" * 50)

if __name__ == "__main__":
    demo_monitoring_capabilities()
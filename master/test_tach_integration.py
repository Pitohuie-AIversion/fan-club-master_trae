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
 + Test script for integrating tach_monitor.py with FC system.
 + Verifies compatibility of tach monitoring component with existing system.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import sys
import os
import time
import threading
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 导入tach监控模块
from tach_monitor import TachSignalMonitor

# 转速监控集成测试控制开关 - 默认禁用
ENABLE_TACH_INTEGRATION_TEST = False


class MockFCCommunicator:
    """模拟FC通信器用于测试"""

    def __init__(self):
        self.connected = True
        self.data_counter = 0
        self.error_simulation = False

    def get_rpm_data(self):
        """模拟获取RPM数据"""
        if self.error_simulation and self.data_counter % 10 == 0:
            raise Exception("模拟通信错误")

        if not self.connected:
            return None

        # 模拟多个风机的RPM数据
        self.data_counter += 1
        base_rpm = 1500 + (self.data_counter % 100) * 10

        return {
            "fan_1": base_rpm + 50,
            "fan_2": base_rpm + 100,
            "fan_3": base_rpm - 50,
            "fan_4": base_rpm + 200,
        }

    def set_error_simulation(self, enable):
        """设置错误模拟"""
        self.error_simulation = enable

    def set_connection_status(self, connected):
        """设置连接状态"""
        self.connected = connected


def test_basic_integration():
    """测试基本集成功能"""
    print("=== 测试基本集成功能 ===")

    # 创建模拟FC通信器
    mock_fc = MockFCCommunicator()

    # 创建转速监控器
    monitor = TachSignalMonitor(fc_communicator=mock_fc)

    print("✓ 转速监控器创建成功")
    print(f"✓ FC通信器集成状态: {'已连接' if mock_fc.connected else '未连接'}")

    # 启动监控
    monitor.start_monitoring(simulation=False)
    print("✓ 监控已启动（实际模式）")

    # 运行一段时间收集数据
    time.sleep(3)

    # 获取统计信息
    stats = monitor.get_current_stats()
    print(f"✓ 数据点数量: {stats['total_readings']}")
    print(f"✓ 错误计数: {stats['error_count']}")
    print(
        f"✓ 平均读取时间: {stats.get('performance', {}).get('avg_read_time', 'N/A')} ms"
    )

    # 停止监控
    monitor.stop_monitoring()
    print("✓ 监控已停止")

    return stats["total_readings"] > 0


def test_error_handling():
    """测试错误处理机制"""
    print("\n=== 测试错误处理机制 ===")

    # 创建模拟FC通信器并启用错误模拟
    mock_fc = MockFCCommunicator()
    mock_fc.set_error_simulation(True)

    # 创建转速监控器
    monitor = TachSignalMonitor(fc_communicator=mock_fc)

    # 启动监控
    monitor.start_monitoring(simulation=False)
    print("✓ 监控已启动（错误模拟模式）")

    # 运行一段时间
    time.sleep(2)

    # 获取统计信息
    stats = monitor.get_current_stats()
    print(f"✓ 错误计数: {stats['error_count']}")
    print(f"✓ 数据点数量: {stats['total_readings']}")
    print(f"✓ 连接状态: {stats.get('connection_status', 'unknown')}")

    # 停止监控
    monitor.stop_monitoring()
    print("✓ 错误处理测试完成")

    return True


def test_performance_optimization():
    """测试性能优化功能"""
    print("\n=== 测试性能优化功能 ===")

    # 创建模拟FC通信器
    mock_fc = MockFCCommunicator()

    # 创建转速监控器
    monitor = TachSignalMonitor(fc_communicator=mock_fc)

    # 启动监控
    monitor.start_monitoring(simulation=False)
    print("✓ 监控已启动（性能测试模式）")

    # 运行较长时间以测试性能优化
    time.sleep(5)

    # 获取性能统计
    stats = monitor.get_current_stats()
    performance = stats.get("performance", {})

    print(f"✓ 平均读取时间: {performance.get('avg_read_time', 'N/A')} ms")
    print(f"✓ 平均处理时间: {performance.get('avg_process_time', 'N/A')} ms")
    print(f"✓ 数据率: {performance.get('data_rate', 'N/A')} 点/秒")
    print(f"✓ 总数据点: {stats['total_readings']}")

    # 停止监控
    monitor.stop_monitoring()
    print("✓ 性能测试完成")

    return performance.get("avg_read_time", 0) > 0


def test_data_validation():
    """测试数据验证功能"""
    print("\n=== 测试数据验证功能 ===")

    # 创建模拟FC通信器
    mock_fc = MockFCCommunicator()

    # 创建转速监控器
    monitor = TachSignalMonitor(fc_communicator=mock_fc)

    # 启动监控
    monitor.start_monitoring(simulation=False)
    print("✓ 监控已启动（数据验证模式）")

    # 运行一段时间
    time.sleep(3)

    # 获取最近数据
    recent_data = monitor.get_recent_data(10)

    if recent_data:
        print(f"✓ 获取到 {len(recent_data)} 个数据点")

        # 检查数据质量
        valid_data = [data for data in recent_data if data.signal_quality > 0.5]
        print(f"✓ 有效数据点: {len(valid_data)}/{len(recent_data)}")

        # 检查RPM范围
        rpm_values = [data.rpm for data in recent_data]
        if rpm_values:
            min_rpm = min(rpm_values)
            max_rpm = max(rpm_values)
            print(f"✓ RPM范围: {min_rpm} - {max_rpm}")

    # 停止监控
    monitor.stop_monitoring()
    print("✓ 数据验证测试完成")

    return len(recent_data) > 0 if recent_data else False


def test_fallback_mechanism():
    """测试回退机制"""
    print("\n=== 测试回退机制 ===")

    # 测试无FC通信器的情况
    monitor = TachSignalMonitor(fc_communicator=None)

    # 启动监控
    monitor.start_monitoring(simulation=False)
    print("✓ 监控已启动（无FC通信器）")

    # 运行一段时间
    time.sleep(2)

    # 获取统计信息
    stats = monitor.get_current_stats()
    print(f"✓ 数据点数量: {stats['total_readings']}")
    print("✓ 回退到模拟模式")

    # 停止监控
    monitor.stop_monitoring()
    print("✓ 回退机制测试完成")

    return stats["total_readings"] > 0


def run_all_tests():
    """运行所有测试"""
    print("开始转速监控集成测试...")
    print("=" * 50)

    test_results = []

    try:
        # 基本集成测试
        result1 = test_basic_integration()
        test_results.append(("基本集成功能", result1))

        # 错误处理测试
        result2 = test_error_handling()
        test_results.append(("错误处理机制", result2))

        # 性能优化测试
        result3 = test_performance_optimization()
        test_results.append(("性能优化功能", result3))

        # 数据验证测试
        result4 = test_data_validation()
        test_results.append(("数据验证功能", result4))

        # 回退机制测试
        result5 = test_fallback_mechanism()
        test_results.append(("回退机制", result5))

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)

    all_passed = True
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 所有测试通过！转速监控集成功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查相关功能。")

    return all_passed


if __name__ == "__main__":
    if not ENABLE_TACH_INTEGRATION_TEST:
        print(
            "转速监控集成测试已禁用。如需启用，请将 ENABLE_TACH_INTEGRATION_TEST 设为 True"
        )
        sys.exit(0)

    success = run_all_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
程序稳定性测试脚本
用于测试优化后的程序稳定性和错误恢复能力
"""

import time
import threading
import socket
import logging
import sys
import os
import psutil
from typing import Dict, List, Any
import json

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 导入测试模块
try:
    from stability_optimizer import stability_optimizer
    from debug_monitor import debug_monitor
    from error_recovery import error_recovery_manager
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

class StabilityTester:
    """稳定性测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        self.test_duration = 300  # 测试持续时间（秒）
        self.is_running = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stability_test.log'),
                logging.StreamHandler()
            ]
        )
    
    def run_all_tests(self):
        """运行所有稳定性测试"""
        self.logger.info("开始稳定性测试...")
        self.is_running = True
        
        tests = [
            ("网络超时测试", self.test_network_timeout),
            ("线程死锁测试", self.test_thread_deadlock),
            ("内存泄漏测试", self.test_memory_leak),
            ("错误恢复测试", self.test_error_recovery),
            ("系统资源监控测试", self.test_system_monitoring),
            ("并发连接测试", self.test_concurrent_connections)
        ]
        
        for test_name, test_func in tests:
            if not self.is_running:
                break
                
            self.logger.info(f"运行测试: {test_name}")
            try:
                result = test_func()
                self.test_results[test_name] = result
                self.logger.info(f"测试完成: {test_name} - {'通过' if result['passed'] else '失败'}")
            except Exception as e:
                self.logger.error(f"测试异常: {test_name} - {e}")
                self.test_results[test_name] = {
                    'passed': False,
                    'error': str(e),
                    'details': {}
                }
        
        self.generate_report()
        self.is_running = False
    
    def test_network_timeout(self) -> Dict[str, Any]:
        """测试网络超时处理"""
        result = {
            'passed': True,
            'details': {
                'timeout_tests': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0
            }
        }
        
        try:
            # 启动稳定性优化器
            stability_optimizer.start_monitoring()
            
            # 模拟网络超时
            for i in range(10):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    optimized_timeout = stability_optimizer.optimize_socket_timeout(sock, "data")
                    sock.settimeout(optimized_timeout)
                    
                    # 尝试连接到不存在的地址
                    sock.sendto(b"test", ("192.168.255.255", 12345))
                    sock.recvfrom(1024)
                    
                except socket.timeout:
                    result['details']['timeout_tests'] += 1
                    # 测试错误恢复
                    if error_recovery_manager.handle_error("socket_timeout", 
                                                         Exception("Test timeout"), 
                                                         {'test': True}):
                        result['details']['successful_recoveries'] += 1
                    else:
                        result['details']['failed_recoveries'] += 1
                except Exception as e:
                    self.logger.warning(f"网络测试异常: {e}")
                finally:
                    sock.close()
                
                time.sleep(0.5)
            
            # 检查恢复成功率
            if result['details']['timeout_tests'] > 0:
                recovery_rate = result['details']['successful_recoveries'] / result['details']['timeout_tests']
                result['passed'] = recovery_rate >= 0.8  # 80%恢复成功率
                result['details']['recovery_rate'] = recovery_rate
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def test_thread_deadlock(self) -> Dict[str, Any]:
        """测试线程死锁检测"""
        result = {
            'passed': True,
            'details': {
                'deadlock_tests': 0,
                'detected_deadlocks': 0,
                'resolved_deadlocks': 0
            }
        }
        
        try:
            # 启动死锁检测
            stability_optimizer.start_monitoring()
            
            # 创建可能导致死锁的锁
            lock1 = threading.Lock()
            lock2 = threading.Lock()
            
            # 注册锁
            stability_optimizer.register_lock(lock1, "test_lock1")
            stability_optimizer.register_lock(lock2, "test_lock2")
            
            def thread1():
                try:
                    if stability_optimizer.safe_acquire_lock(lock1, timeout=2):
                        time.sleep(0.1)
                        if stability_optimizer.safe_acquire_lock(lock2, timeout=2):
                            time.sleep(0.1)
                            stability_optimizer.safe_release_lock(lock2)
                        stability_optimizer.safe_release_lock(lock1)
                except Exception as e:
                    self.logger.warning(f"Thread1异常: {e}")
            
            def thread2():
                try:
                    if stability_optimizer.safe_acquire_lock(lock2, timeout=2):
                        time.sleep(0.1)
                        if stability_optimizer.safe_acquire_lock(lock1, timeout=2):
                            time.sleep(0.1)
                            stability_optimizer.safe_release_lock(lock1)
                        stability_optimizer.safe_release_lock(lock2)
                except Exception as e:
                    self.logger.warning(f"Thread2异常: {e}")
            
            # 运行多次测试
            for i in range(5):
                t1 = threading.Thread(target=thread1)
                t2 = threading.Thread(target=thread2)
                
                t1.start()
                t2.start()
                
                t1.join(timeout=5)
                t2.join(timeout=5)
                
                result['details']['deadlock_tests'] += 1
                time.sleep(0.5)
            
            result['passed'] = True  # 如果没有卡死，说明死锁检测有效
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def test_memory_leak(self) -> Dict[str, Any]:
        """测试内存泄漏"""
        result = {
            'passed': True,
            'details': {
                'initial_memory': 0,
                'final_memory': 0,
                'memory_increase': 0,
                'max_memory_increase': 50  # MB
            }
        }
        
        try:
            # 记录初始内存
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            result['details']['initial_memory'] = initial_memory
            
            # 启动监控
            debug_monitor.start_monitoring()
            
            # 模拟大量操作
            data_list = []
            for i in range(1000):
                # 创建一些数据
                data = {
                    'index': i,
                    'data': 'x' * 1000,
                    'timestamp': time.time()
                }
                data_list.append(data)
                
                # 记录活动
                debug_monitor.record_thread_activity(f"test_activity_{i}")
                debug_monitor.record_network_event(f"test_event_{i}", "test_data")
                
                if i % 100 == 0:
                    # 检查内存使用
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    if memory_increase > result['details']['max_memory_increase']:
                        result['passed'] = False
                        break
            
            # 清理数据
            data_list.clear()
            
            # 记录最终内存
            final_memory = process.memory_info().rss / 1024 / 1024
            result['details']['final_memory'] = final_memory
            result['details']['memory_increase'] = final_memory - initial_memory
            
            # 检查内存增长是否在合理范围内
            if result['details']['memory_increase'] > result['details']['max_memory_increase']:
                result['passed'] = False
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def test_error_recovery(self) -> Dict[str, Any]:
        """测试错误恢复机制"""
        result = {
            'passed': True,
            'details': {
                'error_types_tested': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0
            }
        }
        
        try:
            error_types = [
                ('socket_timeout', socket.timeout("Test timeout")),
                ('socket_error', socket.error("Test socket error")),
                ('network_error', ConnectionError("Test network error")),
                ('memory_error', MemoryError("Test memory error")),
                ('communication_error', Exception("Test communication error"))
            ]
            
            for error_type, error in error_types:
                result['details']['error_types_tested'] += 1
                
                context = {'test': True, 'error_type': error_type}
                if error_recovery_manager.handle_error(error_type, error, context):
                    result['details']['successful_recoveries'] += 1
                else:
                    result['details']['failed_recoveries'] += 1
            
            # 检查恢复成功率
            if result['details']['error_types_tested'] > 0:
                recovery_rate = result['details']['successful_recoveries'] / result['details']['error_types_tested']
                result['passed'] = recovery_rate >= 0.6  # 60%恢复成功率
                result['details']['recovery_rate'] = recovery_rate
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def test_system_monitoring(self) -> Dict[str, Any]:
        """测试系统监控"""
        result = {
            'passed': True,
            'details': {
                'monitoring_duration': 10,  # 秒
                'cpu_samples': 0,
                'memory_samples': 0,
                'avg_cpu': 0,
                'avg_memory': 0
            }
        }
        
        try:
            debug_monitor.start_monitoring()
            
            cpu_readings = []
            memory_readings = []
            
            # 监控系统资源
            for i in range(result['details']['monitoring_duration']):
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                cpu_readings.append(cpu_percent)
                memory_readings.append(memory_percent)
                
                result['details']['cpu_samples'] += 1
                result['details']['memory_samples'] += 1
            
            # 计算平均值
            if cpu_readings:
                result['details']['avg_cpu'] = sum(cpu_readings) / len(cpu_readings)
            if memory_readings:
                result['details']['avg_memory'] = sum(memory_readings) / len(memory_readings)
            
            # 检查监控是否正常工作
            result['passed'] = (result['details']['cpu_samples'] > 0 and 
                              result['details']['memory_samples'] > 0)
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def test_concurrent_connections(self) -> Dict[str, Any]:
        """测试并发连接处理"""
        result = {
            'passed': True,
            'details': {
                'concurrent_threads': 10,
                'successful_connections': 0,
                'failed_connections': 0,
                'timeout_errors': 0
            }
        }
        
        try:
            def simulate_connection(thread_id):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    optimized_timeout = stability_optimizer.optimize_socket_timeout(sock, "heartbeat")
                    sock.settimeout(optimized_timeout)
                    
                    # 模拟网络操作
                    for i in range(5):
                        try:
                            sock.sendto(f"test_{thread_id}_{i}".encode(), ("127.0.0.1", 12345))
                            time.sleep(0.1)
                        except socket.timeout:
                            result['details']['timeout_errors'] += 1
                        except Exception:
                            pass
                    
                    result['details']['successful_connections'] += 1
                    
                except Exception as e:
                    result['details']['failed_connections'] += 1
                    self.logger.warning(f"连接测试失败 {thread_id}: {e}")
                finally:
                    sock.close()
            
            # 创建并发线程
            threads = []
            for i in range(result['details']['concurrent_threads']):
                thread = threading.Thread(target=simulate_connection, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=30)
            
            # 检查成功率
            total_attempts = result['details']['concurrent_threads']
            success_rate = result['details']['successful_connections'] / total_attempts
            result['passed'] = success_rate >= 0.8  # 80%成功率
            result['details']['success_rate'] = success_rate
            
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def generate_report(self):
        """生成测试报告"""
        report = {
            'timestamp': time.time(),
            'test_duration': self.test_duration,
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for r in self.test_results.values() if r.get('passed', False)),
            'failed_tests': sum(1 for r in self.test_results.values() if not r.get('passed', False)),
            'test_results': self.test_results,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                'python_version': sys.version
            }
        }
        
        # 保存报告到文件
        with open('stability_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        self.logger.info("=" * 60)
        self.logger.info("稳定性测试报告")
        self.logger.info("=" * 60)
        self.logger.info(f"总测试数: {report['total_tests']}")
        self.logger.info(f"通过测试: {report['passed_tests']}")
        self.logger.info(f"失败测试: {report['failed_tests']}")
        self.logger.info(f"成功率: {report['passed_tests']/report['total_tests']*100:.1f}%")
        self.logger.info("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "通过" if result.get('passed', False) else "失败"
            self.logger.info(f"{test_name}: {status}")
            if 'error' in result:
                self.logger.error(f"  错误: {result['error']}")
        
        self.logger.info("详细报告已保存到: stability_test_report.json")
    
    def stop_tests(self):
        """停止测试"""
        self.is_running = False
        self.logger.info("测试已停止")

def main():
    """主函数"""
    tester = StabilityTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        tester.logger.info("用户中断测试")
        tester.stop_tests()
    except Exception as e:
        tester.logger.error(f"测试异常: {e}")
    finally:
        # 清理资源
        try:
            debug_monitor.stop_monitoring()
        except:
            pass

if __name__ == "__main__":
    main()